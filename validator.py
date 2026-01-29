#!/usr/bin/env python3
"""
ojs_filesdir_hunter_deterministic.py
Enhanced version with proper exception handling, resource cleanup, and comprehensive logging.
Features:
- Real-time output with fsync
- Thread-safe operations
- Proper error handling and logging
- Resource cleanup
- Deterministic user-agent selection
"""
import os
import requests
import cloudscraper
from concurrent.futures import ThreadPoolExecutor
import random
import threading
import hashlib
import logging
import traceback

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; SM-G996B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/117.0.2045.47"
]

# ROOT PATHS - ISI SENDIRI SESUAI KEBUTUHAN
ROOT_PATHS = [
    # Contoh:
    # "files",
    # "uploads",
    # "ojs/files",
    # dst...
]

# Thread-local storage for sessions and scrapers
thread_local = threading.local()

# Global lock for file writes
file_lock = threading.Lock()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def deterministic_ua(domain: str):
    """Return a deterministic UA string per domain to avoid randomness across runs/threads."""
    if not domain:
        return USER_AGENTS[0]
    try:
        h = int(hashlib.md5(domain.encode('utf-8')).hexdigest(), 16)
        return USER_AGENTS[h % len(USER_AGENTS)]
    except Exception as e:
        logger.warning(f"Error in deterministic_ua for {domain}: {e}")
        return random.choice(USER_AGENTS)

def get_session():
    """Per-thread requests session for connection reuse and consistency."""
    sess = getattr(thread_local, "session", None)
    if sess is None:
        sess = requests.Session()
        thread_local.session = sess
        logger.debug("Created new session for thread")
    return sess

def get_scraper():
    """Per-thread cloudscraper instance."""
    scr = getattr(thread_local, "scraper", None)
    if scr is None:
        scr = cloudscraper.create_scraper()
        thread_local.scraper = scr
        logger.debug("Created new cloudscraper for thread")
    return scr

def cleanup_thread_resources():
    """Cleanup thread-local resources."""
    sess = getattr(thread_local, "session", None)
    if sess:
        try:
            sess.close()
            logger.debug("Closed session for thread")
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
    
    scr = getattr(thread_local, "scraper", None)
    if scr:
        try:
            scr.close()
            logger.debug("Closed scraper for thread")
        except Exception as e:
            logger.warning(f"Error closing scraper: {e}")

def is_cf_jschallenge(body):
    """Check if response is CloudFlare JS challenge."""
    body_lower = (body or "").lower()
    return "cloudflare" in body_lower and (
        "attention required" in body_lower or
        "cf-challenge" in body_lower or
        "just a moment" in body_lower
    )

def is_homepage_ojs(body):
    """Check if response is OJS homepage (to skip)."""
    body_lower = (body or "").lower()
    return (
        "portal jurnal ilmiah" in body_lower or
        "open journal systems" in body_lower or
        "journal help" in body_lower or
        "home >" in body_lower or
        "username" in body_lower or
        "login" in body_lower or
        "register" in body_lower or
        "current issue" in body_lower or
        "universitas tanjungpura" in body_lower or
        "selamat datang" in body_lower or
        "journal content" in body_lower or
        "<title>home" in body_lower or
        "<title>beranda" in body_lower or
        "<title>welcome" in body_lower or
        "ojs" in body_lower or
        "journal" in body_lower or
        "pkp" in body_lower or
        "<meta name=\"generator\" content=\"open journal systems\"" in body_lower or
        "<html" in body_lower or
        "content=\"open journal systems" in body_lower or
        (len(body_lower) > 3000 and "<html" in body_lower)
    )

def extract_scheme_and_domain(raw_domain):
    """Extract scheme and domain from raw input."""
    raw_domain = raw_domain.strip()
    if raw_domain.startswith("https://"):
        return "https", raw_domain[8:].rstrip('/')
    elif raw_domain.startswith("http://"):
        return "http", raw_domain[7:].rstrip('/')
    else:
        return "https", raw_domain.rstrip('/')[cron]       

def is_journals_folder_exists(scheme, domain, root_path):
    """Check if /journals folder exists under root_path."""
    url_noslash = f"{scheme}://{domain}/{root_path}/journals"
    ua = deterministic_ua(domain)
    headers = {
        "User-Agent": ua,
        "Accept": "*/*",
        "Connection": "close"
    }
    
    sess = get_session()
    
    try:
        logger.debug(f"Checking folder existence: {url_noslash}")
        res = sess.get(url_noslash, headers=headers, timeout=15, allow_redirects=False)
        body = res.text if res else ""
        
        if is_cf_jschallenge(body):
            print(f"{YELLOW}[CF JS Challenge] {url_noslash} - using cloudscraper{RESET}", flush=True)
            logger.info(f"CloudFlare challenge detected for {url_noslash}")
            scraper = get_scraper()
            try:
                res = scraper.get(url_noslash, headers=headers, timeout=15, allow_redirects=False)
            except Exception as e:
                print(f"{RED}[ERROR CF] {url_noslash}: {str(e)}{RESET}", flush=True)
                logger.error(f"CloudFlare bypass failed for {url_noslash}: {str(e)}")
                return False
            body = res.text if res else ""
        
        # Check for redirect to /journals/
        if res and res.is_redirect and "Location" in res.headers and res.headers["Location"].endswith("/journals/"):
            print(f"{GREEN}[FOLDER EXISTS] {url_noslash} -> {res.headers['Location']}{RESET}", flush=True)
            logger.info(f"Folder exists (redirect): {url_noslash}")
            return True
        
        if res and res.status_code == 403 and "Location" in res.headers and res.headers["Location"].endswith("/journals/"):
            print(f"{GREEN}[FOLDER EXISTS (403)] {url_noslash} -> {res.headers['Location']}{RESET}", flush=True)
            logger.info(f"Folder exists (403 redirect): {url_noslash}")
            return True
        
        if res and res.status_code == 200 and "Location" in res.headers and res.headers["Location"].endswith("/journals/"):
            print(f"{GREEN}[FOLDER EXISTS (200)] {url_noslash} -> {res.headers['Location']}{RESET}", flush=True)
            logger.info(f"Folder exists (200 redirect): {url_noslash}")
            return True
        
        print(f"{RED}[FOLDER NOT FOUND] {url_noslash}{RESET}", flush=True)
        logger.debug(f"Folder not found: {url_noslash}")
        return False
        
    except requests.exceptions.SSLError as e:
        if scheme == "https":
            print(f"{YELLOW}[SSL ERROR] {url_noslash} - fallback to http{RESET}", flush=True)
            logger.warning(f"SSL error for {url_noslash}, trying HTTP")
            return is_journals_folder_exists("http", domain, root_path)
        else:
            print(f"{RED}[SSL ERROR] {url_noslash}: {str(e)}{RESET}", flush=True)
            logger.error(f"SSL error for {url_noslash}: {str(e)}")
            return False
        
    except requests.exceptions.Timeout as e:
        print(f"{RED}[TIMEOUT] {url_noslash}{RESET}", flush=True)
        logger.error(f"Timeout for {url_noslash}: {str(e)}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"{RED}[ERROR] {url_noslash}: {str(e)}{RESET}", flush=True)
        logger.error(f"Request error for {url_noslash}: {str(e)}")
        return False
        
    except Exception as e:
        print(f"{RED}[UNEXPECTED ERROR] {url_noslash}: {str(e)}{RESET}", flush=True)
        logger.error(f"Unexpected error for {url_noslash}: {str(e)}", exc_info=True)
        return False

def check_journals_dir(scheme, domain, root_path, output_file):
    """Check if journals directory is accessible and valid."""
    url_slash = f"{scheme}://{domain}/{root_path}/journals/"
    ua = deterministic_ua(domain)
    headers = {
        "User-Agent": ua,
        "Accept": "*/*",
        "Connection": "close"
    }
    
    sess = get_session()
    
    try:
        logger.debug(f"Checking directory: {url_slash}")
        res = sess.get(url_slash, headers=headers, timeout=15, allow_redirects=False)
        status = res.status_code
        body = res.text.strip()
        body_lower = body.lower()
        
        if is_cf_jschallenge(body):
            print(f"{YELLOW}[CF JS Challenge] {url_slash} - using cloudscraper{RESET}", flush=True)
            logger.info(f"CloudFlare challenge detected for {url_slash}")
            scraper = get_scraper()
            try:
                res = scraper.get(url_slash, headers=headers, timeout=15, allow_redirects=False)
            except Exception as e:
                print(f"{RED}[ERROR CF] {url_slash}: {str(e)}{RESET}", flush=True)
                logger.error(f"CloudFlare bypass failed for {url_slash}: {str(e)}")
                return None
            status = res.status_code
            body = res.text.strip()
            body_lower = body.lower()
        
        # Check for directory listing
        if "index of" in body_lower or "directory listing" in body_lower:
            print(f"{GREEN}[INDEX OF] {url_slash}{RESET}", flush=True)
            logger.info(f"Directory listing found: {url_slash}")
            with file_lock:
                with open(output_file, "a", encoding="utf-8") as out:
                    out.write(url_slash + "\n")
                    out.flush()
                    os.fsync(out.fileno())
            return url_slash
        
        # Check for 403 Forbidden
        if status == 403:
            print(f"{GREEN}[FORBIDDEN 403] {url_slash}{RESET}", flush=True)
            logger.info(f"Forbidden directory found: {url_slash}")
            with file_lock:
                with open(output_file, "a", encoding="utf-8") as out:
                    out.write(url_slash + "\n")
                    out.flush()
                    os.fsync(out.fileno())
            return url_slash
        
        # Check for blank 200 response
        elif status == 200 and body == "":
            print(f"{GREEN}[BLANK 200] {url_slash}{RESET}", flush=True)
            logger.info(f"Blank 200 response: {url_slash}")
            with file_lock:
                with open(output_file, "a", encoding="utf-8") as out:
                    out.write(url_slash + "\n")
                    out.flush()
                    os.fsync(out.fileno())
            return url_slash
        
        # Check for almost blank response
        elif status == 200 and len(body) < 30 and "<html" not in body_lower and "journal" not in body_lower and "doctype" not in body_lower and "not found" not in body_lower:
            print(f"{GREEN}[ALMOST BLANK 200] {url_slash}{RESET}", flush=True)
            logger.info(f"Almost blank 200 response: {url_slash}")
            with file_lock:
                with open(output_file, "a", encoding="utf-8") as out:
                    out.write(url_slash + "\n")
                    out.flush()
                    os.fsync(out.fileno())
            return url_slash
        
        # Skip OJS homepage
        elif is_homepage_ojs(body):
            print(f"{YELLOW}[SKIP HOMEPAGE OJS] {url_slash} ({status}){RESET}", flush=True)
            logger.debug(f"Skipped OJS homepage: {url_slash}")
            return None
        
        # Skip 404 or HTML pages
        elif status == 404 or "not found" in body_lower or "doctype" in body_lower or "<html" in body_lower:
            print(f"{YELLOW}[SKIP] {url_slash} ({status}){RESET}", flush=True)
            logger.debug(f"Skipped (404 or HTML): {url_slash}")
            return None
        
        else:
            print(f"{YELLOW}[SKIP] {url_slash} ({status}){RESET}", flush=True)
            logger.debug(f"Skipped (other): {url_slash}")
            return None
    
    except requests.exceptions.SSLError as e:
        if scheme == "https":
            print(f"{YELLOW}[SSL ERROR] {url_slash} - fallback to http{RESET}", flush=True)
            logger.warning(f"SSL error for {url_slash}, trying HTTP")
            return check_journals_dir("http", domain, root_path, output_file)
        else:
            print(f"{RED}[SSL ERROR] {url_slash}: {str(e)}{RESET}", flush=True)
            logger.error(f"SSL error for {url_slash}: {str(e)}")
            return None
    
    except requests.exceptions.Timeout as e:
        print(f"{RED}[TIMEOUT] {url_slash}{RESET}", flush=True)
        logger.error(f"Timeout for {url_slash}: {str(e)}")
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"{RED}[ERROR] {url_slash}: {str(e)}{RESET}", flush=True)
        logger.error(f"Request error for {url_slash}: {str(e)}")
        return None
    
    except Exception as e:
        print(f"{RED}[UNEXPECTED ERROR] {url_slash}: {str(e)}{RESET}", flush=True)
        logger.error(f"Unexpected error for {url_slash}: {str(e)}", exc_info=True)
        return None

def brute_force_journals(raw_domain, output_file):
    """Brute force check all root paths for journals directory."""
    if not ROOT_PATHS:
        logger.warning("ROOT_PATHS is empty! Please fill it with paths to check.")
        print(f"{RED}[WARNING] ROOT_PATHS kosong! Isi dulu ROOT_PATHS di script.{RESET}", flush=True)
        return False
    
    scheme, domain = extract_scheme_and_domain(raw_domain)
    logger.info(f"Starting brute force for domain: {domain}")
    
    for root_path in ROOT_PATHS:
        try:
            if not is_journals_folder_exists(scheme, domain, root_path):
                continue
            
            result = check_journals_dir(scheme, domain, root_path, output_file)
            if result:
                print(f"{GREEN}[SUCCESS] {result}{RESET}\n", flush=True)
                logger.info(f"Successfully found: {result}")
                return True
        
        except Exception as e:
            print(f"{RED}[ERROR in root_path {root_path}] {str(e)}{RESET}", flush=True)
            logger.error(f"Error processing root_path {root_path} for {domain}: {str(e)}", exc_info=True)
            continue
    
    return False

def process_domain(domain, output_file, notfound_file):
    """Process a single domain with error handling."""
    try:
        logger.info(f"Processing domain: {domain}")
        found = brute_force_journals(domain, output_file)
        
        if not found:
            print(f"{RED}[NOT FOUND] {domain}{RESET}", flush=True)
            logger.info(f"Not found: {domain}")
            with file_lock:
                with open(notfound_file, "a", encoding="utf-8") as notfound_out:
                    notfound_out.write(f"{domain}\n")
                    notfound_out.flush()
                    os.fsync(notfound_out.fileno())
    
    except KeyboardInterrupt:
        print(f"{YELLOW}[INTERRUPTED] {domain}{RESET}", flush=True)
        logger.warning(f"Interrupted while processing: {domain}")
        raise
    
    except Exception as e:
        print(f"{RED}[FATAL ERROR] {domain}: {type(e).__name__} - {str(e)}{RESET}", flush=True)
        logger.error(f"Fatal error processing {domain}: {type(e).__name__} - {str(e)}", exc_info=True)
        with file_lock:
            with open(notfound_file, "a", encoding="utf-8") as notfound_out:
                notfound_out.write(f"{domain} # ERROR: {type(e).__name__} - {str(e)}\n")
                notfound_out.flush()
                os.fsync(notfound_out.fileno())
    
    finally:
        cleanup_thread_resources()

def process_domain_wrapper(args):
    """Wrapper for process_domain to unpack arguments."""
    domain, output_file, notfound_file = args
    process_domain(domain, output_file, notfound_file)

if __name__ == "__main__":
    try:
        print(f"{GREEN}=== OJS Files Directory Hunter ==={RESET}")
        print(f"{YELLOW}PERHATIAN: Pastikan ROOT_PATHS sudah diisi di script!{RESET}\n")
        
        input_file = input("Masukkan nama file input domain (misal: input.txt): ").strip()
        output_file = input("Masukkan nama file output hasil ditemukan (misal: hasil.txt): ").strip()
        notfound_file = input("Masukkan nama file output TIDAK ditemukan (misal: notfound.txt): ").strip()
        
        try:
            max_threads = int(input("Jumlah thread (misal: 10): ").strip())
        except Exception:
            max_threads = 10
            print(f"{YELLOW}Default: menggunakan {max_threads} thread{RESET}")
        
        # Normalize paths to absolute
        output_file = os.path.abspath(output_file)
        notfound_file = os.path.abspath(notfound_file)
        
        # Read domains from input file
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                domains = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{RED}Error: File {input_file} tidak ditemukan!{RESET}")
            logger.error(f"Input file not found: {input_file}")
            exit(1)
        except Exception as e:
            print(f"{RED}Error membuka file: {e}{RESET}")
            logger.error(f"Error opening input file: {e}", exc_info=True)
            exit(1)
        
        if not domains:
            print(f"{RED}Error: File input kosong atau tidak ada domain yang valid!{RESET}")
            logger.error("No domains found in input file")
            exit(1)
        
        print(f"{GREEN}Total domain: {len(domains)}{RESET}")
        logger.info(f"Loaded {len(domains)} domains from {input_file}")
        
        # Initialize output files
        with file_lock:
            with open(output_file, "w", encoding="utf-8") as out:
                out.write("# Daftar path files_dir/journals yang valid (forbidden/blank/index of)\n")
                out.write(f"# Generated: {os.popen('date').read().strip()}\n\n")
                out.flush()
                os.fsync(out.fileno())
        
        with file_lock:
            with open(notfound_file, "w", encoding="utf-8") as notfound_out:
                notfound_out.write("# Daftar domain yang tidak ditemukan/error\n")
                notfound_out.write(f"# Generated: {os.popen('date').read().strip()}\n\n")
                notfound_out.flush()
                os.fsync(notfound_out.fileno())
        
        print(f"{GREEN}Mulai scanning...{RESET}\n")
        logger.info("Starting domain scanning")
        
        # Process domains with thread pool
        args_list = [(domain, output_file, notfound_file) for domain in domains]
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(process_domain_wrapper, args_list)
        
        print(f"\n{GREEN}========================================{RESET}")
        print(f"{GREEN}Selesai! Hasil scanning:{RESET}")
        print(f"{GREEN}  - Valid paths: {output_file}{RESET}")
        print(f"{GREEN}  - Not found: {notfound_file}{RESET}")
        print(f"{GREEN}  - Debug log: debug.log{RESET}")
        print(f"{GREEN}========================================{RESET}")
        logger.info("Scanning completed successfully")
    
    except KeyboardInterrupt:
        print(f"\n{YELLOW}========================================{RESET}")
        print(f"{YELLOW}[INTERRUPTED] Program dihentikan oleh user{RESET}")
        print(f"{YELLOW}========================================{RESET}")
        logger.warning("Program interrupted by user")
    
    except Exception as e:
        print(f"\n{RED}========================================{RESET}")
        print(f"{RED}[FATAL ERROR] Program crash: {type(e).__name__}{RESET}")
        print(f"{RED}Message: {str(e)}{RESET}")
        print(f"{RED}Cek debug.log untuk detail lengkap{RESET}")
        print(f"{RED}========================================{RESET}")
        logger.critical(f"Program crashed: {type(e).__name__} - {str(e)}", exc_info=True)
        traceback.print_exc()