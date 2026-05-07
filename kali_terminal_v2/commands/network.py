"""
commands/network.py — Complete network security toolkit for KaliTerminal v2.

Commands:
  port-scan       TCP/UDP port scanner with service fingerprinting
  dns-lookup      Full DNS record lookup (A/AAAA/MX/NS/TXT/CNAME/SOA)
  whois           WHOIS domain / IP lookup
  ip-info         Network interfaces & routing
  ip-geo          IP geolocation
  ssl-check       SSL/TLS certificate inspector
  http-headers    HTTP response headers analyzer
  netstat-enhanced Enhanced active connection viewer
"""

import os
import sys
import socket
import subprocess
import concurrent.futures
import ssl
import json
import datetime
import urllib.request
import urllib.error
import urllib.parse

from ui.theme import Colors

C = Colors


# ══════════════════════════════════════════════════════════════════════════════
#  PORT SCAN
# ══════════════════════════════════════════════════════════════════════════════

COMMON_SERVICES = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP",
    53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP", 80: "HTTP",
    88: "KERBEROS", 110: "POP3", 111: "RPC", 119: "NNTP", 123: "NTP",
    135: "MSRPC", 137: "NETBIOS-NS", 138: "NETBIOS-DGM", 139: "NETBIOS-SSN",
    143: "IMAP", 161: "SNMP", 162: "SNMP-TRAP", 389: "LDAP",
    443: "HTTPS", 445: "SMB", 465: "SMTPS", 500: "IKE",
    514: "SYSLOG", 587: "SUBMISSION", 631: "IPP", 636: "LDAPS",
    993: "IMAPS", 995: "POP3S", 1080: "SOCKS", 1194: "OPENVPN",
    1433: "MSSQL", 1521: "ORACLE", 1723: "PPTP", 2049: "NFS",
    2181: "ZOOKEEPER", 2375: "DOCKER", 2376: "DOCKER-TLS",
    3000: "DEV-SERVER", 3306: "MYSQL", 3389: "RDP", 4444: "METASPLOIT",
    4789: "VXLAN", 5000: "FLASK", 5432: "POSTGRESQL", 5900: "VNC",
    5985: "WINRM", 6379: "REDIS", 7001: "WEBLOGIC", 8000: "HTTP-ALT",
    8080: "HTTP-PROXY", 8443: "HTTPS-ALT", 8888: "JUPYTER",
    9000: "XDEBUG/PHP", 9200: "ELASTICSEARCH", 9300: "ELASTICSEARCH-CLUSTER",
    10250: "KUBELET", 11211: "MEMCACHED", 27017: "MONGODB",
    27018: "MONGODB-SHARD", 50000: "SAP", 50070: "HADOOP",
}

TOP_PORTS = [21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,
             1723,3306,3389,5900,8080,8443,9200,27017]


def cmd_port_scan(args: list, state: dict) -> int:
    """
    port-scan <host> [port-spec] [options]
    Port specs: 1-1024 | 80,443,8080 | top | all
    Options:    --udp --timeout <s> --threads <n> --banner
    """
    if not args:
        print(C.info("Usage: port-scan <host> [port-spec] [options]"))
        print(C.info("Specs:   1-1024 | 80,443,8080 | top (common) | all (1-65535)"))
        print(C.info("Options: --timeout <s>  --threads <n>  --banner"))
        print(C.info("Example: port-scan 192.168.1.1 1-1024 --banner"))
        return 0

    # Parse arguments
    host     = args[0]
    port_str = "top"
    timeout  = 1.0
    threads  = 150
    banner   = False

    i = 1
    while i < len(args):
        a = args[i]
        if a == "--timeout" and i+1 < len(args):
            timeout = float(args[i+1]); i += 2
        elif a == "--threads" and i+1 < len(args):
            threads = int(args[i+1]); i += 2
        elif a == "--banner":
            banner = True; i += 1
        elif not a.startswith("--"):
            port_str = a; i += 1
        else:
            i += 1

    # Resolve ports
    if port_str == "top":
        ports = TOP_PORTS
        port_desc = f"top {len(TOP_PORTS)} common ports"
    elif port_str == "all":
        ports = range(1, 65536)
        port_desc = "all 65535 ports"
    elif "-" in port_str:
        start, end = port_str.split("-", 1)
        ports = range(int(start), int(end)+1)
        port_desc = f"ports {start}-{end}"
    elif "," in port_str:
        ports = [int(p) for p in port_str.split(",")]
        port_desc = f"{len(ports)} specified ports"
    else:
        try:
            ports = [int(port_str)]
            port_desc = f"port {port_str}"
        except ValueError:
            print(C.error(f"Invalid port spec: {port_str}"))
            return 1

    # Resolve host
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(C.error(f"Cannot resolve host: {host}"))
        return 1

    ports_list = list(ports)
    total      = len(ports_list)

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PORT SCAN{C.RESET}  {C.CYAN}{host}{C.RESET}  {C.GRAY}({ip}){C.RESET}")
    print(f"  {C.GRAY}Scanning {port_desc} | timeout={timeout}s | threads={threads}{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    open_ports  = []
    scanned     = 0
    start_time  = datetime.datetime.now()

    def scan_tcp(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            if result == 0:
                grab = ""
                if banner:
                    try:
                        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                        grab = sock.recv(256).decode(errors="replace").split("\r\n")[0]
                    except Exception:
                        pass
                sock.close()
                return (port, grab)
            sock.close()
        except Exception:
            pass
        return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
            futures = {ex.submit(scan_tcp, p): p for p in ports_list}
            for fut in concurrent.futures.as_completed(futures):
                scanned += 1
                result = fut.result()
                if result:
                    open_ports.append(result)
                # Progress every 500 ports
                if scanned % 500 == 0 or scanned == total:
                    pct = scanned * 100 // total
                    sys.stdout.write(f"\r  {C.GRAY}Progress: {pct}%  ({scanned}/{total}){C.RESET}  ")
                    sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n{C.warn('Scan interrupted.')}")

    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    print(f"\r{' '*60}\r", end="")

    open_ports.sort(key=lambda x: x[0])

    print(f"  {C.GREEN}Scan complete{C.RESET}: {C.BOLD}{len(open_ports)} open{C.RESET} / {scanned} scanned in {elapsed:.2f}s\n")

    if open_ports:
        print(f"  {C.BOLD}{C.GRAY}{'PORT':<8}{'PROTO':<6}{'SERVICE':<18}{'BANNER'}{C.RESET}")
        print(f"  {C.BLUE}{'─'*60}{C.RESET}")
        for port, grab in open_ports:
            svc   = COMMON_SERVICES.get(port, "unknown")
            clr   = C.GREEN
            gbstr = f"  {C.GRAY}{grab[:35]}{C.RESET}" if grab else ""
            print(f"  {clr}{C.BOLD}{port:<8}{C.RESET}{C.CYAN}tcp   {C.RESET}{C.WHITE}{svc:<18}{C.RESET}{C.YELLOW}OPEN{C.RESET}{gbstr}")
    else:
        print(f"  {C.GRAY}No open ports found in scanned range.{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  DNS LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

def cmd_dns_lookup(args: list, state: dict) -> int:
    """dns-lookup <host> [type] — DNS lookup. Types: A AAAA MX NS TXT CNAME SOA all"""
    if not args:
        print(C.info("Usage: dns-lookup <host> [A|AAAA|MX|NS|TXT|CNAME|SOA|all]"))
        return 0

    host     = args[0]
    rec_type = args[1].upper() if len(args) > 1 else "all"

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DNS LOOKUP: {host}{C.RESET}")
    print(f"{C.BLUE}{'═'*60}{C.RESET}\n")

    # Always show A/AAAA
    try:
        addrs = socket.getaddrinfo(host, None)
        seen = {}
        for r in addrs:
            ip   = r[4][0]
            fam  = "A" if r[0] == socket.AF_INET else "AAAA"
            if ip not in seen:
                seen[ip] = fam
                color = C.GREEN if fam == "A" else C.CYAN
                print(f"  {C.YELLOW}{fam:<6}{C.RESET}  {color}{ip}{C.RESET}")
    except socket.gaierror as e:
        print(C.error(f"DNS resolution failed: {e}"))

    # Use `dig` or `host` if available for richer records
    if rec_type in ("all", "MX", "NS", "TXT", "CNAME", "SOA"):
        _dig_lookup(host, rec_type)

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}\n")
    return 0


def _dig_lookup(host: str, rec_type: str):
    types = ["MX", "NS", "TXT", "CNAME", "SOA"] if rec_type == "all" else [rec_type]
    for t in types:
        try:
            res = subprocess.run(
                ["dig", "+short", f"+{t.lower()}", host, t],
                capture_output=True, text=True, timeout=5
            )
            out = res.stdout.strip()
            if not out:
                res = subprocess.run(
                    ["host", "-t", t, host],
                    capture_output=True, text=True, timeout=5
                )
                out = res.stdout.strip()
            if out:
                print(f"\n  {C.YELLOW}{t}{C.RESET}")
                for line in out.splitlines():
                    print(f"    {C.WHITE}{line}{C.RESET}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  WHOIS
# ══════════════════════════════════════════════════════════════════════════════

def cmd_whois(args: list, state: dict) -> int:
    """whois <domain|ip> — WHOIS lookup."""
    if not args:
        print(C.info("Usage: whois <domain|ip>"))
        return 0

    target = args[0]
    print(f"\n{C.BLUE}{'═'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}WHOIS: {target}{C.RESET}")
    print(f"{C.BLUE}{'═'*60}{C.RESET}\n")

    # Try system whois first
    try:
        res = subprocess.run(
            ["whois", target],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode == 0 and res.stdout.strip():
            interesting = [
                "Domain Name", "Registrar", "Creation Date", "Registry Expiry",
                "Updated Date", "Name Server", "DNSSEC", "Registrant",
                "Tech Email", "Admin Email", "Status", "OrgName", "NetRange",
                "CIDR", "Country", "RegDate", "Updated", "NetType",
            ]
            lines = res.stdout.splitlines()
            shown = 0
            for line in lines:
                if any(k.lower() in line.lower() for k in interesting):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        label = parts[0].strip()
                        value = parts[1].strip()
                        if value:
                            print(f"  {C.CYAN}{label:<25}{C.RESET}  {C.WHITE}{value}{C.RESET}")
                            shown += 1
            if shown == 0:
                # Fallback: print first 30 lines
                for line in lines[:30]:
                    if line.strip() and not line.startswith("%"):
                        print(f"  {C.WHITE}{line}{C.RESET}")
            print(f"\n{C.BLUE}{'═'*60}{C.RESET}\n")
            return 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: raw WHOIS socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect(("whois.iana.org", 43))
        s.send(f"{target}\r\n".encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        text = data.decode(errors="replace")
        for line in text.splitlines()[:40]:
            if line.strip():
                print(f"  {C.WHITE}{line}{C.RESET}")
    except Exception as e:
        print(C.error(f"WHOIS failed: {e}"))
        print(C.info("Install 'whois' package for better results."))
        return 1

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  IP-GEO
# ══════════════════════════════════════════════════════════════════════════════

def cmd_ip_geo(args: list, state: dict) -> int:
    """ip-geo <ip> — Geolocate an IP address using ip-api.com."""
    if not args:
        print(C.info("Usage: ip-geo <ip|domain>"))
        print(C.info("Example: ip-geo 8.8.8.8"))
        return 0

    target = args[0]
    # Resolve if domain
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(C.error(f"Cannot resolve: {target}"))
        return 1

    print(f"\n{C.BLUE}{'═'*55}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}IP GEOLOCATION: {ip}{C.RESET}")
    print(f"{C.BLUE}{'═'*55}{C.RESET}\n")

    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        req = urllib.request.Request(url, headers={"User-Agent": "KaliTerminal/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") == "fail":
            print(C.error(f"Lookup failed: {data.get('message', 'Unknown error')}"))
            return 1

        fields = [
            ("IP",        data.get("query", ip),          C.GREEN),
            ("Country",   f"{data.get('country','')} ({data.get('countryCode','')})", C.WHITE),
            ("Region",    f"{data.get('regionName','')} ({data.get('region','')})",    C.WHITE),
            ("City",      data.get("city", ""),            C.WHITE),
            ("ZIP",       data.get("zip", ""),             C.GRAY),
            ("Latitude",  str(data.get("lat", "")),        C.CYAN),
            ("Longitude", str(data.get("lon", "")),        C.CYAN),
            ("Timezone",  data.get("timezone", ""),        C.YELLOW),
            ("ISP",       data.get("isp", ""),             C.WHITE),
            ("Org",       data.get("org", ""),             C.WHITE),
            ("AS",        data.get("as", ""),              C.GRAY),
        ]
        for label, value, color in fields:
            if value:
                print(f"  {C.CYAN}{label:<14}{C.RESET}  {color}{value}{C.RESET}")

        lat  = data.get("lat", "")
        lon  = data.get("lon", "")
        if lat and lon:
            print(f"\n  {C.GRAY}Map: https://maps.google.com/?q={lat},{lon}{C.RESET}")

    except urllib.error.URLError as e:
        print(C.error(f"Network error: {e.reason}"))
        return 1
    except Exception as e:
        print(C.error(f"GeoIP lookup failed: {e}"))
        return 1

    print(f"\n{C.BLUE}{'═'*55}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  SSL CHECK
# ══════════════════════════════════════════════════════════════════════════════

def cmd_ssl_check(args: list, state: dict) -> int:
    """ssl-check <host> [port] — Inspect SSL/TLS certificate."""
    if not args:
        print(C.info("Usage: ssl-check <host> [port]"))
        print(C.info("Example: ssl-check google.com"))
        return 0

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 443

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}SSL/TLS CERTIFICATE: {host}:{port}{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(
            socket.create_connection((host, port), timeout=10),
            server_hostname=host
        ) as ssock:
            cert    = ssock.getpeercert()
            cipher  = ssock.cipher()
            version = ssock.version()

        # Basic info
        subject = dict(x[0] for x in cert.get("subject", []))
        issuer  = dict(x[0] for x in cert.get("issuer", []))
        san     = cert.get("subjectAltName", [])

        def row(label, value, color=None):
            c = color or C.WHITE
            print(f"  {C.CYAN}{label:<24}{C.RESET}  {c}{value}{C.RESET}")

        row("Common Name",    subject.get("commonName", "N/A"),     C.GREEN)
        row("Organization",   subject.get("organizationName", "N/A"))
        row("Issuer CN",      issuer.get("commonName", "N/A"),      C.YELLOW)
        row("Issuer Org",     issuer.get("organizationName", "N/A"))
        row("TLS Version",    version or "N/A",                     C.CYAN)
        row("Cipher Suite",   cipher[0] if cipher else "N/A",       C.CYAN)
        row("Cipher Bits",    str(cipher[2]) if cipher else "N/A",  C.CYAN)

        # Dates
        not_before = cert.get("notBefore", "")
        not_after  = cert.get("notAfter",  "")

        if not_before:
            try:
                nb = datetime.datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z")
                row("Valid From", nb.strftime("%Y-%m-%d %H:%M:%S UTC"), C.GREEN)
            except Exception:
                row("Valid From", not_before)

        if not_after:
            try:
                na   = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                now  = datetime.datetime.utcnow()
                days = (na - now).days
                exp_clr = C.GREEN if days > 30 else C.YELLOW if days > 7 else C.RED
                row("Expires", f"{na.strftime('%Y-%m-%d %H:%M:%S UTC')} ({days}d remaining)", exp_clr)
            except Exception:
                row("Expires", not_after)

        # SANs
        if san:
            print(f"\n  {C.YELLOW}Subject Alternative Names ({len(san)}):{C.RESET}")
            for typ, name in san[:15]:
                print(f"    {C.GRAY}{typ:<5}{C.RESET}  {C.WHITE}{name}{C.RESET}")
            if len(san) > 15:
                print(f"    {C.GRAY}... and {len(san)-15} more{C.RESET}")

    except ssl.SSLCertVerificationError as e:
        print(C.warn(f"Certificate verification FAILED: {e}"))
        print(C.info("The certificate may be self-signed or expired."))
        return 1
    except ssl.SSLError as e:
        print(C.error(f"SSL error: {e}"))
        return 1
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(C.error(f"Connection failed: {e}"))
        return 1

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  HTTP HEADERS
# ══════════════════════════════════════════════════════════════════════════════

def cmd_http_headers(args: list, state: dict) -> int:
    """http-headers <url> [--follow] — Analyze HTTP response headers."""
    if not args:
        print(C.info("Usage: http-headers <url> [--follow]"))
        print(C.info("Example: http-headers https://example.com --follow"))
        return 0

    url    = args[0]
    follow = "--follow" in args or "-L" in args

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}HTTP HEADERS: {url}{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    # Security headers to highlight
    SECURITY_HEADERS = {
        "strict-transport-security": ("HSTS",             "Enforces HTTPS"),
        "content-security-policy":   ("CSP",              "Controls resource loading"),
        "x-content-type-options":    ("XCTO",             "Prevents MIME sniffing"),
        "x-frame-options":           ("XFO",              "Clickjacking protection"),
        "x-xss-protection":          ("XSS-Protection",   "XSS filter (legacy)"),
        "referrer-policy":           ("Referrer-Policy",  "Controls referrer info"),
        "permissions-policy":        ("Permissions-Policy","Feature permissions"),
        "access-control-allow-origin":("CORS",            "Cross-origin policy"),
        "server":                    ("Server",            "⚠ May reveal server info"),
        "x-powered-by":              ("X-Powered-By",     "⚠ Reveals tech stack"),
        "set-cookie":                ("Set-Cookie",       "Check for Secure/HttpOnly"),
    }

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (KaliTerminal/2.0; Security-Scanner)",
                "Accept": "*/*",
            }
        )
        # Don't follow redirects unless asked
        if not follow:
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
            opener.handlers = [h for h in opener.handlers
                                if not isinstance(h, urllib.request.HTTPRedirectHandler)]
        with urllib.request.urlopen(req, timeout=15) as resp:
            headers = dict(resp.headers)
            status  = resp.status

    except urllib.error.HTTPError as e:
        headers = dict(e.headers)
        status  = e.code
    except urllib.error.URLError as e:
        print(C.error(f"Request failed: {e.reason}"))
        return 1
    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    # Status line
    status_color = C.GREEN if 200 <= status < 300 else C.YELLOW if status < 400 else C.RED
    print(f"  {C.BOLD}HTTP Status{C.RESET}  {status_color}{status}{C.RESET}\n")

    # All headers
    print(f"  {C.YELLOW}━━━ All Headers ━━━{C.RESET}")
    for name, value in sorted(headers.items()):
        print(f"  {C.CYAN}{name:<35}{C.RESET}  {C.WHITE}{value[:80]}{C.RESET}")

    # Security analysis
    print(f"\n  {C.YELLOW}━━━ Security Analysis ━━━{C.RESET}")
    found     = set()
    missing   = []
    headers_l = {k.lower(): v for k, v in headers.items()}

    for hdr, (label, note) in SECURITY_HEADERS.items():
        if hdr in headers_l:
            found.add(hdr)
            warn = "⚠" if "⚠" in note else "✔"
            clr  = C.YELLOW if "⚠" in note else C.GREEN
            print(f"  {clr}{warn} {label:<22}{C.RESET}  {C.GRAY}{note}{C.RESET}")
            print(f"    {C.WHITE}{headers_l[hdr][:70]}{C.RESET}")
        else:
            if hdr not in ("server", "x-powered-by", "set-cookie",
                           "access-control-allow-origin", "x-xss-protection"):
                missing.append((label, note))

    if missing:
        print(f"\n  {C.RED}✗ Missing Security Headers:{C.RESET}")
        for label, note in missing:
            print(f"  {C.RED}  ✗ {label:<22}{C.RESET}  {C.GRAY}{note}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  IP INFO
# ══════════════════════════════════════════════════════════════════════════════

def cmd_ip_info(args: list, state: dict) -> int:
    """ip-info [host] — Network interfaces and IP information."""
    try:
        import psutil
    except ImportError:
        print(C.warn("psutil not installed. Run: pip install psutil"))
        _basic_ip_info()
        return 0

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}NETWORK INFORMATION{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    hostname = socket.gethostname()
    print(f"  {C.CYAN}Hostname{C.RESET}  {C.GREEN}{hostname}{C.RESET}")
    try:
        print(f"  {C.CYAN}FQDN    {C.RESET}  {C.WHITE}{socket.getfqdn()}{C.RESET}")
    except Exception:
        pass

    print(f"\n  {C.YELLOW}Network Interfaces:{C.RESET}")
    try:
        net     = psutil.net_if_addrs()
        net_io  = psutil.net_io_counters(pernic=True)
        net_stat= psutil.net_if_stats()

        for iface, addrs in sorted(net.items()):
            stat = net_stat.get(iface)
            is_up= stat.isup if stat else False
            speed= f"{stat.speed} Mbps" if stat and stat.speed else "N/A"
            up_str = f"{C.GREEN}UP{C.RESET}" if is_up else f"{C.RED}DOWN{C.RESET}"
            print(f"\n  {C.RED}{C.BOLD}[{iface}]{C.RESET}  {up_str}  {C.GRAY}{speed}{C.RESET}")
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    print(f"    {C.CYAN}IPv4{C.RESET}  {C.GREEN}{addr.address}{C.RESET}/{C.GRAY}{addr.netmask}{C.RESET}")
                elif addr.family == socket.AF_INET6:
                    print(f"    {C.CYAN}IPv6{C.RESET}  {C.GREEN}{addr.address}{C.RESET}")
                elif hasattr(socket, "AF_PACKET") and addr.family == socket.AF_PACKET:
                    print(f"    {C.CYAN}MAC {C.RESET}  {C.GRAY}{addr.address}{C.RESET}")
            if iface in net_io:
                io = net_io[iface]
                print(f"    {C.CYAN}TX{C.RESET} {_fmt_bytes(io.bytes_sent)}  "
                      f"{C.CYAN}RX{C.RESET} {_fmt_bytes(io.bytes_recv)}  "
                      f"{C.GRAY}Pkts:{io.packets_sent}/{io.packets_recv}{C.RESET}")
    except Exception as e:
        print(C.warn(f"Interface info partial: {e}"))

    # DNS resolution if host given
    if args:
        target = args[0]
        print(f"\n  {C.YELLOW}DNS: {target}{C.RESET}")
        try:
            for r in socket.getaddrinfo(target, None):
                ip  = r[4][0]
                fam = "IPv4" if r[0] == socket.AF_INET else "IPv6"
                print(f"    {C.GREEN}{ip}{C.RESET}  {C.GRAY}({fam}){C.RESET}")
        except socket.gaierror as e:
            print(C.error(f"Cannot resolve '{target}': {e}"))

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


def _basic_ip_info():
    """Fallback: show basic IP without psutil."""
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  {C.CYAN}Hostname{C.RESET}: {C.GREEN}{hostname}{C.RESET}")
        print(f"  {C.CYAN}Local IP{C.RESET}: {C.GREEN}{ip}{C.RESET}")
    except Exception:
        print(f"  {C.CYAN}Hostname{C.RESET}: {hostname}")


# ══════════════════════════════════════════════════════════════════════════════
#  NETSTAT ENHANCED
# ══════════════════════════════════════════════════════════════════════════════

def cmd_netstat_enhanced(args: list, state: dict) -> int:
    """netstat-enhanced — Active connections and listening ports."""
    try:
        import psutil
    except ImportError:
        print(C.error("Requires psutil: pip install psutil"))
        return 1

    print(f"\n{C.BLUE}{'═'*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ENHANCED NETSTAT{C.RESET}")
    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")

    conns = psutil.net_connections(kind="inet")

    # Status counts
    status_map = {}
    for c in conns:
        s = c.status or "NONE"
        status_map[s] = status_map.get(s, 0) + 1

    print(f"  {C.YELLOW}Connection States:{C.RESET}")
    for status, count in sorted(status_map.items(), key=lambda x: -x[1]):
        clr = C.GREEN if status == "ESTABLISHED" else C.YELLOW if status == "LISTEN" else C.WHITE
        bar = "█" * min(count, 30)
        print(f"    {clr}{status:<20}{C.RESET} {C.BOLD}{count:<5}{C.RESET} {C.GRAY}{bar}{C.RESET}")

    # Listening ports
    listening = sorted([c for c in conns if c.status == "LISTEN"],
                       key=lambda x: x.laddr.port)
    if listening:
        print(f"\n  {C.YELLOW}Listening Ports ({len(listening)}):{C.RESET}")
        print(f"  {C.BOLD}{C.GRAY}{'PORT':<8}{'PROTO':<6}{'ADDRESS':<25}{'PID':<8}PROCESS{C.RESET}")
        for c in listening:
            proto = "tcp" if c.type == socket.SOCK_STREAM else "udp"
            pid   = str(c.pid) if c.pid else "-"
            try:
                name = psutil.Process(c.pid).name()[:20] if c.pid else "-"
            except Exception:
                name = "-"
            addr = f"{c.laddr.ip}:{c.laddr.port}"
            print(f"  {C.GREEN}{c.laddr.port:<8}{C.RESET}{C.CYAN}{proto:<6}{C.RESET}"
                  f"{C.WHITE}{addr:<25}{C.RESET}{C.GRAY}{pid:<8}{C.RESET}{C.YELLOW}{name}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*70}{C.RESET}\n")
    return 0


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


# ══════════════════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════════════════

NET_COMMANDS: dict = {
    "port-scan":         cmd_port_scan,
    "portscan":          cmd_port_scan,
    "dns-lookup":        cmd_dns_lookup,
    "nslookup":          cmd_dns_lookup,
    "whois":             cmd_whois,
    "ip-info":           cmd_ip_info,
    "ifconfig-enhanced": cmd_ip_info,
    "ip-geo":            cmd_ip_geo,
    "geoip":             cmd_ip_geo,
    "ssl-check":         cmd_ssl_check,
    "ssl-info":          cmd_ssl_check,
    "http-headers":      cmd_http_headers,
    "headers":           cmd_http_headers,
    "netstat-enhanced":  cmd_netstat_enhanced,
    "netstat+":          cmd_netstat_enhanced,
}
