"""
commands/network.py — Pure-Python Network Tools for Kali Terminal v1.0

Commands:
  scan <host> [start_port] [end_port] [--timeout T] — TCP port scanner
  ping_sweep <subnet/24>                             — ICMP ping sweep
  dns <domain> [record_type]                         — DNS lookups
  myip                                               — Show your IPs
  banner_grab <host> <port>                          — Grab service banner
  http_headers <url>                                 — Show HTTP headers
  whois_lookup <domain>                              — WHOIS info
"""

import os
import sys
import socket
import threading
import time
import ipaddress
import concurrent.futures

from ui.theme import Colors
from utils.formatters import table, bar

C = Colors


# ══════════════════════════════════════════════════════════════════════
#  Port Scanner
# ══════════════════════════════════════════════════════════════════════

COMMON_PORTS = {
    21:    "FTP",        22:    "SSH",        23:    "Telnet",
    25:    "SMTP",       53:    "DNS",        67:    "DHCP",
    68:    "DHCP",       80:    "HTTP",       110:   "POP3",
    111:   "RPC",        119:   "NNTP",       123:   "NTP",
    135:   "RPC",        139:   "NetBIOS",    143:   "IMAP",
    161:   "SNMP",       194:   "IRC",        389:   "LDAP",
    443:   "HTTPS",      445:   "SMB",        465:   "SMTPS",
    514:   "Syslog",     515:   "LPD",        587:   "SMTP",
    631:   "IPP",        636:   "LDAPS",      993:   "IMAPS",
    995:   "POP3S",      1080:  "SOCKS",      1194:  "OpenVPN",
    1433:  "MSSQL",      1521:  "Oracle",     1723:  "PPTP",
    2049:  "NFS",        2181:  "ZooKeeper",  2375:  "Docker",
    2376:  "Docker-TLS", 3000:  "Node.js",    3306:  "MySQL",
    3389:  "RDP",        4444:  "Metasploit", 5000:  "Flask",
    5432:  "PostgreSQL", 5900:  "VNC",        5984:  "CouchDB",
    6379:  "Redis",      6443:  "K8s API",    7001:  "WebLogic",
    8000:  "HTTP-Alt",   8080:  "HTTP-Alt",   8081:  "HTTP-Alt",
    8443:  "HTTPS-Alt",  8888:  "Jupyter",    9000:  "SonarQube",
    9090:  "Prometheus", 9200:  "Elasticsearch",9300: "ES-cluster",
    11211: "Memcached",  27017: "MongoDB",    27018: "MongoDB",
    50070: "HDFS",
}


def _scan_port(host: str, port: int, timeout: float) -> tuple:
    """Try to TCP connect to host:port. Returns (port, open, banner)."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            # Try to grab banner
            banner = ""
            try:
                sock.settimeout(0.5)
                data = sock.recv(256)
                banner = data.decode("utf-8", errors="ignore").strip()[:60]
            except Exception:
                pass
            return (port, True, banner)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return (port, False, "")


def cmd_scan(args: list, state: dict) -> int:
    """
    scan <host> [start_port] [end_port] [--timeout T] [--threads N]

    Python-based TCP port scanner with service detection.
    """
    if not args:
        print(C.error("Usage: scan <host> [start_port] [end_port] [--timeout 0.5] [--threads 200]"))
        return 1

    # Parse args
    host       = args[0]
    start_port = 1
    end_port   = 1024
    timeout    = 0.5
    n_threads  = 200

    i = 1
    positional = []
    while i < len(args):
        if args[i] == "--timeout" and i + 1 < len(args):
            try:
                timeout = float(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif args[i] == "--threads" and i + 1 < len(args):
            try:
                n_threads = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if len(positional) >= 1:
        try:
            start_port = int(positional[0])
        except ValueError:
            print(C.error(f"Invalid port: {positional[0]}"))
            return 1
    if len(positional) >= 2:
        try:
            end_port = int(positional[1])
        except ValueError:
            print(C.error(f"Invalid port: {positional[1]}"))
            return 1

    # Resolve host
    print(f"\n{C.BOLD}{C.BLUE}╔══ PORT SCAN ══════════════════════════════════════╗{C.RESET}")
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(C.error(f"Cannot resolve host: {host}"))
        return 1

    print(f"{C.BLUE}║{C.RESET}  Target   : {C.CYAN}{host}{C.RESET} ({C.GREEN}{ip}{C.RESET})")
    print(f"{C.BLUE}║{C.RESET}  Ports    : {C.YELLOW}{start_port}–{end_port}{C.RESET}  ({end_port - start_port + 1} ports)")
    print(f"{C.BLUE}║{C.RESET}  Timeout  : {C.WHITE}{timeout}s{C.RESET}  Threads: {C.WHITE}{n_threads}{C.RESET}")
    print(f"{C.BLUE}╚{'═'*50}╝{C.RESET}\n")

    ports = list(range(start_port, end_port + 1))
    open_ports = []
    start_time = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = {
                executor.submit(_scan_port, ip, p, timeout): p
                for p in ports
            }

            done = 0
            total = len(futures)
            for future in concurrent.futures.as_completed(futures):
                done += 1
                port, is_open, banner = future.result()
                if is_open:
                    open_ports.append((port, banner))
                    svc = COMMON_PORTS.get(port, "unknown")
                    svc_str = C.paint(f"{svc:<12}", C.GREEN)
                    banner_str = C.paint(banner[:40], C.GRAY) if banner else ""
                    print(f"  {C.GREEN}[OPEN]{C.RESET}  "
                          f"{C.CYAN}{port:<6}{C.RESET}  {svc_str}  {banner_str}")

                # Progress bar every 100 ports
                if done % 100 == 0 or done == total:
                    pct = done / total * 100
                    b = bar(pct, width=30, label=False)
                    sys.stdout.write(
                        f"\r  {C.GRAY}Scanning... {b} {C.CYAN}{pct:.0f}%{C.RESET}  "
                    )
                    sys.stdout.flush()

    except KeyboardInterrupt:
        print(f"\n{C.warn('Scan interrupted by user.')}")

    elapsed = time.time() - start_time
    print(f"\n\n{C.BLUE}{'─'*55}{C.RESET}")

    if open_ports:
        print(f"  {C.BOLD}{C.GREEN}Found {len(open_ports)} open port(s){C.RESET} in {C.YELLOW}{elapsed:.2f}s{C.RESET}")
        print()
        rows = []
        for port, banner in sorted(open_ports):
            svc = COMMON_PORTS.get(port, "—")
            rows.append((str(port), svc, banner[:35] or "—"))
        print(table(rows, headers=["PORT", "SERVICE", "BANNER"],
                    title="OPEN PORTS"))
    else:
        print(f"  {C.warn('No open ports found.')}  Elapsed: {elapsed:.2f}s")

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  Ping Sweep
# ══════════════════════════════════════════════════════════════════════

def _ping_host(ip: str) -> tuple:
    """Ping a single host. Returns (ip, alive)."""
    try:
        import subprocess
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", str(ip)],
            capture_output=True, timeout=2
        )
        return (str(ip), result.returncode == 0)
    except Exception:
        return (str(ip), False)


def cmd_ping_sweep(args: list, state: dict) -> int:
    """
    ping_sweep <subnet/cidr>
    Example: ping_sweep 192.168.1.0/24
    """
    if not args:
        print(C.error("Usage: ping_sweep <subnet/cidr>  e.g. ping_sweep 192.168.1.0/24"))
        return 1

    try:
        network = ipaddress.ip_network(args[0], strict=False)
    except ValueError as e:
        print(C.error(f"Invalid network: {e}"))
        return 1

    hosts = list(network.hosts())
    if len(hosts) > 256:
        print(C.warn(f"Large network ({len(hosts)} hosts). Limiting to /24 range."))
        hosts = hosts[:256]

    print(f"\n{C.BOLD}{C.BLUE}[ PING SWEEP ]{C.RESET}  Target: {C.CYAN}{args[0]}{C.RESET}  "
          f"Hosts: {C.YELLOW}{len(hosts)}{C.RESET}\n")

    alive = []
    start = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(_ping_host, ip): ip for ip in hosts}
            done = 0
            for future in concurrent.futures.as_completed(futures):
                ip_str, is_alive = future.result()
                done += 1
                if is_alive:
                    alive.append(ip_str)
                    try:
                        hostname = socket.gethostbyaddr(ip_str)[0]
                    except Exception:
                        hostname = ""
                    print(f"  {C.GREEN}[UP]{C.RESET}  {C.CYAN}{ip_str:<18}{C.RESET}  {C.GRAY}{hostname}{C.RESET}")

                sys.stdout.write(
                    f"\r  {C.GRAY}Progress: {done}/{len(hosts)} — Alive: {len(alive)}{C.RESET}  "
                )
                sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n{C.warn('Sweep interrupted.')}")

    elapsed = time.time() - start
    print(f"\n\n{C.BLUE}{'─'*50}{C.RESET}")
    print(f"  {C.BOLD}{C.GREEN}{len(alive)} host(s) alive{C.RESET}  |  Elapsed: {C.YELLOW}{elapsed:.2f}s{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════
#  DNS Lookup
# ══════════════════════════════════════════════════════════════════════

def cmd_dns(args: list, state: dict) -> int:
    """
    dns <domain> [record_type]
    record_type: A, AAAA, MX, NS, TXT, CNAME, SOA (requires dnspython if installed)
    """
    if not args:
        print(C.error("Usage: dns <domain> [A|AAAA|MX|NS|TXT|CNAME]"))
        return 1

    domain = args[0]
    rtype  = args[1].upper() if len(args) > 1 else "A"

    print(f"\n{C.BOLD}{C.BLUE}[ DNS LOOKUP ]{C.RESET}  {C.CYAN}{domain}{C.RESET}  Type: {C.YELLOW}{rtype}{C.RESET}\n")

    try:
        import dns.resolver  # type: ignore
        answers = dns.resolver.resolve(domain, rtype)
        rows = []
        for rdata in answers:
            rows.append((domain, rtype, str(rdata)))
        print(table(rows, headers=["DOMAIN", "TYPE", "VALUE"], title="DNS RECORDS"))

    except ImportError:
        # Fallback to socket for basic A record
        if rtype in ("A", "AAAA"):
            try:
                af = socket.AF_INET6 if rtype == "AAAA" else socket.AF_INET
                results = socket.getaddrinfo(domain, None, af)
                rows = [(domain, rtype, r[4][0]) for r in results]
                print(table(rows, headers=["DOMAIN", "TYPE", "VALUE"],
                            title="DNS RECORDS (basic)"))
                print(C.info("Install dnspython for full DNS support: pip install dnspython"))
            except socket.gaierror as e:
                print(C.error(f"DNS resolution failed: {e}"))
                return 1
        else:
            print(C.warn(f"Type {rtype} requires: pip install dnspython"))
            # Try system dig
            import subprocess
            r = subprocess.run(["dig", domain, rtype, "+short"],
                               capture_output=True, text=True)
            if r.returncode == 0 and r.stdout:
                print(f"{C.CYAN}dig output:{C.RESET}\n{r.stdout}")
            else:
                print(C.error("Cannot resolve. Install dnspython for full DNS support."))
                return 1

    except Exception as e:
        print(C.error(f"DNS error: {e}"))
        return 1

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  My IP
# ══════════════════════════════════════════════════════════════════════

def cmd_myip(args: list, state: dict) -> int:
    """Show all network interfaces and their IP addresses."""
    print(f"\n{C.BOLD}{C.BLUE}[ NETWORK INTERFACES ]{C.RESET}\n")

    rows = []
    try:
        import psutil
        for iface, addrs in psutil.net_if_addrs().items():
            stats = psutil.net_if_stats().get(iface)
            status = (C.paint("UP", C.GREEN) if stats and stats.isup
                      else C.paint("DOWN", C.RED))
            for addr in addrs:
                family_map = {2: "IPv4", 10: "IPv6", 17: "MAC"}
                family = family_map.get(addr.family, str(addr.family))
                rows.append((iface, family, addr.address, status))
    except ImportError:
        # Fallback
        try:
            import subprocess
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True)
            print(result.stdout)
            return 0
        except Exception:
            print(C.error("Cannot list interfaces. Install psutil: pip install psutil"))
            return 1

    if rows:
        print(table(rows, headers=["INTERFACE", "FAMILY", "ADDRESS", "STATUS"],
                    title="IP ADDRESSES"))
    else:
        print(C.warn("No interfaces found."))

    # External IP (best effort)
    try:
        import urllib.request
        with urllib.request.urlopen("https://api.ipify.org", timeout=3) as resp:
            ext_ip = resp.read().decode()
        print(f"\n  {C.BOLD}{C.WHITE}External IP:{C.RESET} {C.GREEN}{ext_ip}{C.RESET}")
    except Exception:
        pass

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  Banner Grab
# ══════════════════════════════════════════════════════════════════════

def cmd_banner_grab(args: list, state: dict) -> int:
    """banner_grab <host> <port> — Grab a service banner via TCP."""
    if len(args) < 2:
        print(C.error("Usage: banner_grab <host> <port>"))
        return 1
    try:
        host = args[0]
        port = int(args[1])
    except ValueError:
        print(C.error("Port must be a number"))
        return 1

    print(f"\n{C.BOLD}{C.BLUE}[ BANNER GRAB ]{C.RESET}  {C.CYAN}{host}:{port}{C.RESET}\n")
    try:
        with socket.create_connection((host, port), timeout=5) as s:
            s.settimeout(3)
            # Send a generic probe
            probes = [b"HEAD / HTTP/1.0\r\n\r\n", b"\r\n", b""]
            banner = ""
            for probe in probes:
                if probe:
                    s.send(probe)
                try:
                    data = s.recv(4096)
                    banner = data.decode("utf-8", errors="replace")
                    if banner.strip():
                        break
                except socket.timeout:
                    break

            if banner:
                print(f"{C.GREEN}Banner received:{C.RESET}\n")
                for line in banner.splitlines()[:20]:
                    print(f"  {C.WHITE}{line}{C.RESET}")
            else:
                print(C.warn("No banner received (port open but no response)."))
    except (socket.timeout, ConnectionRefusedError):
        print(C.error(f"Connection refused or timed out: {host}:{port}"))
        return 1
    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  HTTP Headers
# ══════════════════════════════════════════════════════════════════════

def cmd_http_headers(args: list, state: dict) -> int:
    """http_headers <url> — Show HTTP response headers."""
    if not args:
        print(C.error("Usage: http_headers <url>"))
        return 1

    url = args[0]
    if not url.startswith("http"):
        url = "http://" + url

    print(f"\n{C.BOLD}{C.BLUE}[ HTTP HEADERS ]{C.RESET}  {C.CYAN}{url}{C.RESET}\n")

    try:
        import urllib.request
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "KaliTerminal/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  {C.BOLD}{C.GREEN}HTTP {resp.status} {resp.reason}{C.RESET}\n")
            rows = []
            for key, val in resp.headers.items():
                rows.append((key, val))
            print(table(rows, headers=["HEADER", "VALUE"], title="RESPONSE HEADERS"))
    except Exception as e:
        print(C.error(f"Request failed: {e}"))
        return 1

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  Network Builtins Dispatch
# ══════════════════════════════════════════════════════════════════════

NETWORK_COMMANDS = {
    "scan":         cmd_scan,
    "ping_sweep":   cmd_ping_sweep,
    "dns":          cmd_dns,
    "myip":         cmd_myip,
    "banner_grab":  cmd_banner_grab,
    "http_headers": cmd_http_headers,
}
