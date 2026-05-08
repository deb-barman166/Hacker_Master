"""
commands/web_tools.py — Web application security tools (v2.0 Masterpiece).

Commands:
  - http-headers: Fetch HTTP headers
  - http-post: Send HTTP POST request
  - sql-test: Basic SQL injection tester
  - xss-test: Basic XSS tester
  - dir-scan: Directory brute force scanner
  - subdomain-enum: Subdomain enumeration
  - cert-check: SSL certificate checker
"""

import os
import sys
import socket
import ssl
import urllib.parse
import re
import concurrent.futures
import time
from datetime import datetime

from ui.theme import Colors

C = Colors


def cmd_http_headers(args: list, state: dict, terminal=None) -> int:
    """Fetch HTTP headers. Usage: http-headers <url>"""
    if not args:
        print(C.info("Usage: http-headers <url>"))
        return 0

    url = args[0]
    if not url.startswith("http"):
        url = "http://" + url

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}HTTP HEADERS: {url}{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}\n")

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'KaliTerminal/2.0 Security Scanner')

        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"  {C.GREEN}{C.BOLD}[+] HTTP {response.status} {response.reason}{C.RESET}\n")

            print(f"  {C.YELLOW}{C.BOLD}Response Headers:{C.RESET}")
            for header, value in sorted(response.headers.items()):
                # Color code security headers
                if header.lower() in ('strict-transport-security', 'content-security-policy',
                                      'x-frame-options', 'x-content-type-options', 'x-xss-protection'):
                    print(f"  {C.GREEN}{header:<35}{C.RESET}{C.WHITE}{value}{C.RESET}")
                elif header.lower().startswith('x-'):
                    print(f"  {C.CYAN}{header:<35}{C.RESET}{C.WHITE}{value}{C.RESET}")
                else:
                    print(f"  {C.GRAY}{header:<35}{C.RESET}{C.WHITE}{value}{C.RESET}")

            # Security analysis
            print(f"\n  {C.YELLOW}{C.BOLD}Security Headers Analysis:{C.RESET}")
            headers = {h.lower(): v for h, v in response.headers.items()}

            security_checks = [
                ("Strict-Transport-Security", "HSTS", headers.get('strict-transport-security', '')),
                ("Content-Security-Policy", "CSP", headers.get('content-security-policy', '')),
                ("X-Frame-Options", "Clickjacking", headers.get('x-frame-options', '')),
                ("X-Content-Type-Options", "MIME Sniffing", headers.get('x-content-type-options', '')),
                ("X-XSS-Protection", "XSS Filter", headers.get('x-xss-protection', '')),
            ]

            for header_name, check_name, value in security_checks:
                if value:
                    print(f"    {C.GREEN}[+] {check_name}{C.RESET} - {C.WHITE}{header_name}{C.RESET}: {value[:50]}...")
                else:
                    print(f"    {C.RED}[-] {check_name}{C.RESET} - {C.WHITE}{header_name} Missing{C.RESET}")

    except urllib.error.HTTPError as e:
        print(f"  {C.RED}HTTP Error: {e.code} {e.reason}{C.RESET}")
    except urllib.error.URLError as e:
        print(f"  {C.RED}URL Error: {e.reason}{C.RESET}")
    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_http_post(args: list, state: dict, terminal=None) -> int:
    """Send HTTP POST request. Usage: http-post <url> <data> [content-type]"""
    if len(args) < 2:
        print(C.info("Usage: http-post <url> <data> [content-type]"))
        print(C.info("Example: http-post http://example.com/api '{\"key\":\"value\"}'"))
        return 0

    url = args[0]
    data = args[1]
    content_type = args[2] if len(args) > 2 else "application/x-www-form-urlencoded"

    if not url.startswith("http"):
        url = "http://" + url

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}HTTP POST REQUEST{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    try:
        import urllib.request
        import urllib.error

        if content_type == "application/json":
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = urllib.parse.urlencode({'data': data}).encode('utf-8')

        print(f"  {C.CYAN}URL{C.RESET}:         {C.WHITE}{url}{C.RESET}")
        print(f"  {C.CYAN}Content-Type{C.RESET}: {C.WHITE}{content_type}{C.RESET}")
        print(f"  {C.CYAN}Data Length{C.RESET}:  {C.WHITE}{len(data_bytes)} bytes{C.RESET}\n")

        req = urllib.request.Request(url, data=data_bytes, method='POST')
        req.add_header('Content-Type', content_type)
        req.add_header('User-Agent', 'KaliTerminal/2.0')

        print(f"  {C.YELLOW}Sending request...{C.RESET}\n")

        with urllib.request.urlopen(req, timeout=30) as response:
            print(f"  {C.GREEN}{C.BOLD}[+] Response: {response.status} {response.reason}{C.RESET}")
            print(f"\n  {C.CYAN}Response Headers:{C.RESET}")
            for header, value in list(response.headers.items())[:10]:
                print(f"    {C.GRAY}{header}{C.RESET}: {value[:60]}...")

            # Read response body (truncated)
            body = response.read(2000).decode('utf-8', errors='ignore')
            print(f"\n  {C.YELLOW}{C.BOLD}Response Body (truncated):{C.RESET}")
            print(f"  {C.WHITE}{body[:500]}...{C.RESET}" if len(body) > 500 else f"  {C.WHITE}{body}{C.RESET}")

    except urllib.error.HTTPError as e:
        print(f"  {C.RED}HTTP Error: {e.code} {e.reason}{C.RESET}")
        try:
            body = e.read().decode('utf-8', errors='ignore')
            print(f"\n  {C.YELLOW}Response Body:{C.RESET}\n  {C.WHITE}{body[:500]}...{C.RESET}")
        except:
            pass
    except urllib.error.URLError as e:
        print(f"  {C.RED}URL Error: {e.reason}{C.RESET}")
    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_sql_test(args: list, state: dict, terminal=None) -> int:
    """Basic SQL injection tester. Usage: sql-test <url> [param]"""
    if not args:
        print(C.info("Usage: sql-test <url> [param]"))
        print(C.info("Example: sql-test http://target.com/page.php?id=1"))
        return 0

    url = args[0]
    param = args[1] if len(args) > 1 else None

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║              SQL INJECTION TESTER — Educational Use Only        ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    # SQL injection payloads
    payloads = [
        "'",
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' #",
        "' OR '1'='1'/*",
        "admin' --",
        "admin' #",
        "admin'/*",
        "' or 1=1--",
        "' or 1=1#",
        "' or 1=1/*",
        "') or '1'='1--",
        "') or ('1'='1--",
    ]

    print(f"  {C.CYAN}Target{C.RESET}: {C.WHITE}{url}{C.RESET}")
    print(f"  {C.CYAN}Payloads{C.RESET}: {C.WHITE}{len(payloads)}{C.RESET}\n")

    try:
        import urllib.request
        import urllib.error

        # Test different payloads
        for payload in payloads:
            test_url = url
            if '?' in url:
                test_url = url + urllib.parse.quote_plus(payload)
            else:
                test_url = url + "?" + (param or "q") + "=" + urllib.parse.quote_plus(payload)

            try:
                req = urllib.request.Request(test_url)
                req.add_header('User-Agent', 'KaliTerminal/2.0')

                start_time = time.time()
                with urllib.request.urlopen(req, timeout=5) as response:
                    elapsed = time.time() - start_time
                    body = response.read(1000).decode('utf-8', errors='ignore').lower()

                # Check for SQL error messages
                sql_errors = [
                    'sql syntax', 'mysql', 'syntax error', 'ora-', 'oracle',
                    'postgresql', 'sqlite', 'microsoft sql', 'odbc', 'warning: mysql',
                    'sql server', 'native error', 'sqlite3', 'unterminated',
                    'you have an error in your sql syntax', 'mysql_fetch',
                    'pg_query', 'syntax error at or near'
                ]

                found_error = None
                for error in sql_errors:
                    if error in body:
                        found_error = error
                        break

                if found_error:
                    print(f"  {C.RED}[!] VULNERABLE{C.RESET} - Payload: {C.YELLOW}{payload}{C.RESET}")
                    print(f"      {C.GRAY}SQL Error detected: {found_error}{C.RESET}")
                elif elapsed > 3:
                    print(f"  {C.YELLOW}[?] SUSPICIOUS{C.RESET} - Payload: {C.YELLOW}{payload}{C.RESET}")
                    print(f"      {C.GRAY}Slow response: {elapsed:.2f}s (possible blind injection){C.RESET}")
                else:
                    print(f"  {C.GRAY}[-] Safe{C.RESET} - Payload: {payload}")

            except urllib.error.HTTPError:
                print(f"  {C.GRAY}[-] Safe{C.RESET} - Payload: {payload} (HTTP error)")
            except Exception:
                print(f"  {C.GRAY}[-] Safe{C.RESET} - Payload: {payload}")

    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n  {C.YELLOW}{C.BOLD}Note:{C.RESET} {C.GRAY}This is a basic test. Full SQL injection testing requires more thorough analysis.{C.RESET}")
    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_xss_test(args: list, state: dict, terminal=None) -> int:
    """Basic XSS tester. Usage: xss-test <url> [param]"""
    if not args:
        print(C.info("Usage: xss-test <url> [param]"))
        print(C.info("Example: xss-test http://target.com/search?q=test"))
        return 0

    url = args[0]
    param = args[1] if len(args) > 1 else None

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║              XSS TESTER — Educational Use Only                 ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    # XSS payloads
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "'-alert('XSS')-'",
        "\"><script>alert('XSS')</script>",
        "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
    ]

    print(f"  {C.CYAN}Target{C.RESET}: {C.WHITE}{url}{C.RESET}")
    print(f"  {C.CYAN}Payloads{C.RESET}: {C.WHITE}{len(payloads)}{C.RESET}\n")

    for payload in payloads:
        print(f"  {C.YELLOW}[*] Testing{C.RESET}: {C.GRAY}{payload[:50]}...{C.RESET}")

    print(f"\n  {C.YELLOW}{C.BOLD}Manual Verification Required:{C.RESET}")
    print(f"  {C.GRAY}1. Copy the URL below")
    print(f"  {C.GRAY}2. Open in a browser")
    print(f"  {C.GRAY}3. Check if payload executes{C.RESET}")

    # Generate test URLs
    print(f"\n  {C.YELLOW}{C.BOLD}Generated Test URLs:{C.RESET}")
    for i, payload in enumerate(payloads[:5], 1):
        encoded = urllib.parse.quote_plus(payload)
        if '?' in url:
            test_url = f"{url}&{(param or 'q')}={encoded}"
        else:
            test_url = f"{url}?{(param or 'q')}={encoded}"
        print(f"  {C.CYAN}{i}.{C.RESET} {C.WHITE}{test_url}{C.RESET}")

    print(f"\n  {C.YELLOW}{C.BOLD}Note:{C.RESET} {C.GRAY}Automatic XSS testing can be dangerous. Manual testing is recommended.{C.RESET}")
    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_dir_scan(args: list, state: dict, terminal=None) -> int:
    """Directory brute force scanner. Usage: dir-scan <url> [wordlist]"""
    if not args:
        print(C.info("Usage: dir-scan <url> [wordlist]"))
        print(C.info("Example: dir-scan http://target.com/"))
        return 0

    url = args[0].rstrip('/')
    wordlist_path = args[1] if len(args) > 1 else None

    if not url.startswith("http"):
        url = "http://" + url

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║              DIRECTORY SCANNER                                 ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    # Default wordlist
    default_dirs = [
        "admin", "administrator", "login", "wp-admin", "wp-login",
        "phpmyadmin", "pma", "api", "api-docs", "graphql",
        "uploads", "images", "assets", "static", "css", "js",
        "backup", "backups", "bak", "old", "test", "dev",
        " staging", "production", "debug", "console", "shell",
        "robots.txt", "sitemap.xml", ".env", "config", "configuration",
        "server-status", "server-info", "status", "health",
        ".git", ".git/config", ".git/HEAD", ".svn", "CVS",
        "readme", "README.md", "license", "LICENSE.md",
        "index.php", "index.html", "default.aspx", "main.aspx",
    ]

    dirs_to_scan = default_dirs
    if wordlist_path and os.path.isfile(wordlist_path):
        try:
            with open(wordlist_path, 'r') as f:
                dirs_to_scan = [line.strip() for line in f if line.strip()]
            print(f"  {C.GREEN}Loaded {len(dirs_to_scan)} paths from wordlist{C.RESET}")
        except Exception as e:
            print(C.warn(f"Could not load wordlist: {e}"))
    else:
        print(f"  {C.GRAY}Using built-in directory list ({len(dirs_to_scan)} paths){C.RESET}")

    print(f"  {C.CYAN}Target{C.RESET}: {C.WHITE}{url}{C.RESET}")
    print(f"  {C.CYAN}Paths{C.RESET}: {C.WHITE}{len(dirs_to_scan)}{C.RESET}\n")

    found_dirs = []
    scanned = 0

    try:
        import urllib.request
        import urllib.error

        def check_dir(path):
            test_url = f"{url}/{path}"
            try:
                req = urllib.request.Request(test_url)
                req.add_header('User-Agent', 'KaliTerminal/2.0')
                with urllib.request.urlopen(req, timeout=3) as response:
                    return (path, response.status, response.reason)
            except urllib.error.HTTPError as e:
                return (path, e.code, e.reason)
            except:
                return None

        print(f"  {C.YELLOW}Scanning...{C.RESET}\n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(check_dir, path): path for path in dirs_to_scan}
            for future in concurrent.futures.as_completed(futures):
                scanned += 1
                result = future.result()
                if result:
                    path, status, reason = result
                    if status == 200:
                        found_dirs.append((path, status, reason))
                        print(f"\r  {C.GREEN}[+] FOUND{C.RESET} {path} ({status})     ", end="")
                    elif status == 301 or status == 302:
                        print(f"\r  {C.CYAN}[R] REDIRECT{C.RESET} {path} ({status})    ", end="")
                    elif status == 403:
                        print(f"\r  {C.YELLOW}[!] FORBIDDEN{C.RESET} {path} ({status})    ", end="")

                print(f"\r  {C.GRAY}Scanned: {scanned}/{len(dirs_to_scan)}{C.RESET}", end="")

        print(f"\n\n  {C.YELLOW}{C.BOLD}Results:{C.RESET}")

        if found_dirs:
            print(f"\n  {C.GREEN}{C.BOLD}Directories Found ({len(found_dirs)}):{C.RESET}")
            for path, status, reason in sorted(found_dirs):
                print(f"    {C.GREEN}{path}{C.RESET} - {C.WHITE}{status} {reason}{C.RESET}")
        else:
            print(f"  {C.GRAY}No accessible directories found.{C.RESET}")

    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_subdomain_enum(args: list, state: dict, terminal=None) -> int:
    """Subdomain enumeration. Usage: subdomain-enum <domain>"""
    if not args:
        print(C.info("Usage: subdomain-enum <domain>"))
        print(C.info("Example: subdomain-enum example.com"))
        return 0

    domain = args[0]

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║              SUBDOMAIN ENUMERATION                              ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    # Common subdomains
    common_subdomains = [
        "www", "mail", "ftp", "admin", "blog", "shop", "api",
        "dev", "staging", "test", "demo", "m", "mobile",
        "secure", "login", "auth", "sso", "ldap", "oauth",
        "smtp", "pop", "imap", "mx", "dns", "ns1", "ns2",
        "webmail", "webdisk", "cpanel", "whm", "autoconfig",
        "autodiscover", "msoid", "lyncdiscover", "sip",
        "vpn", "remote", "git", "gitlab", "jenkins", "ci",
        "docs", "wiki", "support", "help", "chat", "forum",
        "cdn", "static", "assets", "media", "files", "downloads",
        "images", "img", "store", "app", "portal", "panel",
        "manage", "dashboard", "cms", "backup", "old", "new",
    ]

    print(f"  {C.CYAN}Domain{C.RESET}: {C.WHITE}{domain}{C.RESET}")
    print(f"  {C.CYAN}Subdomains{C.RESET}: {C.WHITE}{len(common_subdomains)}{C.RESET}\n")

    found_subdomains = []

    def check_subdomain(sub):
        full_domain = f"{sub}.{domain}"
        try:
            addr = socket.gethostbyname(full_domain)
            return (sub, addr)
        except:
            return None

    print(f"  {C.YELLOW}Enumerating...{C.RESET}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(check_subdomain, sub): sub for sub in common_subdomains}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                sub, addr = result
                found_subdomains.append((sub, addr))
                print(f"  {C.GREEN}[+] {C.WHITE}{sub}.{domain}{C.RESET} -> {C.CYAN}{addr}{C.RESET}")

    print(f"\n  {C.YELLOW}{C.BOLD}Summary:{C.RESET}")
    print(f"  {C.CYAN}Found{C.RESET}: {C.GREEN}{len(found_subdomains)}{C.RESET} subdomains")

    if found_subdomains:
        print(f"\n  {C.GREEN}{C.BOLD}Resolved Subdomains:{C.RESET}")
        for sub, addr in sorted(found_subdomains):
            print(f"    {C.CYAN}{sub:<20}{C.RESET} {C.WHITE}{addr}{C.RESET}")

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_cert_check(args: list, state: dict, terminal=None) -> int:
    """SSL certificate checker. Usage: cert-check <host> [port]"""
    if not args:
        print(C.info("Usage: cert-check <host> [port]"))
        return 0

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 443

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}SSL CERTIFICATE CHECK: {host}:{port}{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}\n")

    try:
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()

                print(f"  {C.GREEN}{C.BOLD}[+] Secure Connection{C.RESET}")
                print(f"  {C.CYAN}Protocol{C.RESET}:  {C.WHITE}{ssock.version()}{C.RESET}")
                cipher = ssock.cipher()
                if cipher:
                    print(f"  {C.CYAN}Cipher{C.RESET}:    {C.WHITE}{cipher[0]} ({cipher[2]} bits){C.RESET}")

                if cert:
                    subject = dict(x[0] for x in cert.get('subject', []))
                    issuer = dict(x[0] for x in cert.get('issuer', []))

                    print(f"\n  {C.YELLOW}{C.BOLD}Certificate:{C.RESET}")
                    print(f"  {C.CYAN}Subject{C.RESET}:    {C.WHITE}{subject.get('commonName', 'N/A')}{C.RESET}")
                    print(f"  {C.CYAN}Issuer{C.RESET}:     {C.WHITE}{issuer.get('commonName', 'N/A')}{C.RESET}")

                    not_after = cert.get('notAfter', '')
                    not_before = cert.get('notBefore', '')

                    print(f"\n  {C.YELLOW}{C.BOLD}Validity:{C.RESET}")
                    print(f"  {C.CYAN}Not Before{C.RESET}: {C.WHITE}{not_before}{C.RESET}")
                    print(f"  {C.CYAN}Not After{C.RESET}:  {C.WHITE}{not_after}{C.RESET}")

                    # Check expiry
                    import datetime
                    try:
                        from email.utils import parsedate_to_datetime
                        expiry = parsedate_to_datetime(not_after)
                        days_left = (expiry - datetime.datetime.now(datetime.timezone.utc)).days

                        if days_left < 0:
                            print(f"  {C.RED}Status{C.RESET}: {C.RED}EXPIRED{C.RESET}")
                        elif days_left < 30:
                            print(f"  {C.RED}Status{C.RESET}: {C.RED}EXPIRING SOON ({days_left} days){C.RESET}")
                        else:
                            print(f"  {C.GREEN}Status{C.RESET}: {C.GREEN}VALID ({days_left} days remaining){C.RESET}")
                    except:
                        pass

    except ssl.SSLCertVerificationError as e:
        print(f"  {C.RED}{C.BOLD}[-] Certificate Error:{C.RESET}")
        print(f"  {C.WHITE}{str(e)[:200]}{C.RESET}")
    except socket.gaierror:
        print(C.error(f"Could not resolve: {host}"))
        return 1
    except Exception as e:
        print(C.error(f"Connection error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0