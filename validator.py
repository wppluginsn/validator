def extract_scheme_and_domain(raw_domain):
    """Extract scheme and domain from raw input."""
    raw_domain = raw_domain.strip()
    if raw_domain.startswith("https://"):
        return "https", raw_domain[8:].rstrip('/')
    elif raw_domain.startswith("http://"):
        return "http", raw_domain[7:].rstrip('/')
    else:
        return "https", raw_domain.rstrip('/')
