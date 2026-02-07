# Importing necessary libraries
import requests
import random
from urllib.parse import urlparse

# Defining user agents
USER_AGENTS = [
    # (List of user agents)
]

# phpMyAdmin paths constants
PHPMYADMIN_PATHS = [
    '/phpmyadmin/index.php',
    '/phpMyAdmin/index.php',
    '/pma/index.php',
    '/PMA/index.php',
    '/myadmin/index.php',
    '/MyAdmin/index.php',
    '/sql/index.php',
    '/db/index.php',
    '/database/index.php',
    '/mysql/index.php',
    '/admin/phpmyadmin/index.php',
    '/admin/pma/index.php',
    '/admin/db/index.php',
    '/dbadmin/index.php',
    '/websql/index.php',
    '/phpmyadmin4/index.php',
    '/phpmyadmin3/index.php',
    '/php-my-admin/index.php',
    '/sqladmin/index.php',
    '/mysqladmin/index.php',
    '/typo3/phpmyadmin/index.php',
    '/xampp/phpmyadmin/index.php',
    '/tools/phpmyadmin/index.php',
    '/claroline/phpMyAdmin/index.php',
    '/_phpmyadmin/index.php',
    '/db/phpmyadmin/index.php',
    '/admin/phpMyAdmin/index.php',
    '/phpma/index.php',
]

class ZhyperChecker:
    # Existing methods...

    def find_phpmyadmin_path(self, base_url):
        """Find working phpMyAdmin path from 28 alternatives"""
        try:
            if not base_url.startswith('http'):
                base_url = f"https://{base_url}"
            
            parsed = urlparse(base_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            
            if self.debug_mode.get():
                self.log(f"  PHPMYADMIN: Scanning {len(PHPMYADMIN_PATHS)} paths...", "cyan")
            
            s = requests.Session()
            s.verify = False
            s.headers.update({'User-Agent': random.choice(USER_AGENTS)})
            
            for idx, path in enumerate(PHPMYADMIN_PATHS, 1):
                try:
                    test_url = base + path
                    
                    if self.debug_mode.get():
                        self.log(f"  [{idx}/{len(PHPMYADMIN_PATHS)}] Testing: {path}", "gray")
                    
                    resp = s.get(test_url, timeout=5, allow_redirects=True)
                    
                    if resp.status_code == 200:
                        txt_lower = resp.text.lower()
                        
                        pma_indicators = ['phpmyadmin', 'pma_username', 'pma_password', 'server choice']
                        
                        if any(indicator in txt_lower for indicator in pma_indicators):
                            if self.debug_mode.get():
                                self.log(f"  PHPMYADMIN: ✓ FOUND at {path}", "green")
                            return test_url
                    
                except:
                    continue
            
            if self.debug_mode.get():
                self.log(f"  PHPMYADMIN: ✗ Not found in all {len(PHPMYADMIN_PATHS)} paths", "yellow")
            
            return None
        
        except Exception as e:
            if self.debug_mode.get():
                self.log(f"  PHPMYADMIN: Path finder error: {str(e)[:50]}", "red")
            return None

    def check_login(self, url, cms):
        # Existing code...
        if cms == 'phpmyadmin':
            found_path = self.find_phpmyadmin_path(url)
            if found_path:
                login_url = found_path
                if self.debug_mode.get():
                    self.log(f"  PHPMYADMIN: Using found path: {login_url}", "green")
            else:
                if url.rstrip('/').endswith('/phpmyadmin'):
                    login_url = url.rstrip('/') + '/index.php'
                elif '/phpmyadmin/' in url:
                    base = url.split('/phpmyadmin/')[0] + '/phpmyadmin'
                    login_url = base + '/index.php'
                else:
                    login_url = cfg['login_url'].format(url=url.rstrip('/'))

    # All other existing code remains unchanged...