"""
commands/network_tools.py — Network diagnostic and analysis tools (v2.0 Masterpiece).

Commands:
  - ip-info: Show IP address information
  - netstat-enhanced: Enhanced network statistics
  - port-scan: Simple TCP port scanner
  - subnet-calc: Subnet calculator
  - dns-lookup: DNS lookup tool
  - whois: WHOIS lookup
  - traceroute: Traceroute utility
  - ping-sweep: Ping sweep for network discovery
"""

import os
import sys
import socket
import subprocess
import concurrent.futures
from datetime import datetime
import struct
import re

from ui.theme import Colors

C = Colors


def cmd_ip_info(args: list, state: dict, terminal=None) -> int:
    """Display detailed IP and network interface information."""
    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}NETWORK / IP INFORMATION{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    hostname = socket.gethostname()
    print(f"\n  {C.CYAN}Hostname{C.RESET}:       {C.WHITE}{hostname}{C.RESET}")

    try:
        fqdn = socket.getfqdn()
        print(f"  {C.CYAN}FQDN{C.RESET}:           {C.WHITE}{fqdn}{C.RESET}")
    except Exception:
        pass

    try:
        import psutil
        net = psutil.net_if_addrs()
        net_io = psutil.net_io_counters(pernic=True)

        print(f"\n  {C.YELLOW}{C.BOLD}Network Interfaces:{C.RESET}")
        for iface, addrs in sorted(net.items()):
            print(f"\n  {C.RED}{C.BOLD}  [{iface}]{C.RESET}")
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    print(f"    {C.CYAN}IPv4{C.RESET}:    {C.GREEN}{addr.address}{C.RESET}/{C.GRAY}{addr.netmask}{C.RESET}")
                elif addr.family == socket.AF_INET6:
                    print(f"    {C.CYAN}IPv6{C.RESET}:    {C.GREEN}{addr.address}{C.RESET}")
                elif addr.family == socket.AF_PACKET:
                    print(f"    {C.CYAN}MAC{C.RESET}:     {C.GRAY}{addr.address}{C.RESET}")

            if iface in net_io:
                io = net_io[iface]
                print(f"    {C.CYAN}RX{C.RESET}:       {C.GREEN}{_fmt_bytes(io.bytes_recv)}{C.RESET}"
                      f"  {C.CYAN}TX{C.RESET}:       {C.GREEN}{_fmt_bytes(io.bytes_sent)}{C.RESET}")

        print(f"\n  {C.YELLOW}{C.BOLD}Routing:{C.RESET}")
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"  {C.WHITE}{result.stdout.strip()}{C.RESET}")
        except Exception:
            pass

        print(f"\n  {C.YELLOW}{C.BOLD}Public IP:{C.RESET}")
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "5", "ifconfig.me"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip():
                print(f"  {C.GREEN}{C.BOLD}{result.stdout.strip()}{C.RESET}")
            else:
                print(f"  {C.GRAY}Could not determine public IP{C.RESET}")
        except Exception:
            print(f"  {C.GRAY}Could not determine public IP (curl not available){C.RESET}")

    except ImportError:
        print(C.warn("Install psutil for full network info"))

    if args:
        target = args[0]
        print(f"\n  {C.YELLOW}{C.BOLD}DNS Resolution for '{target}':{C.RESET}")
        try:
            ips = socket.getaddrinfo(target, None)
            seen = set()
            for result in ips:
                ip = result[4][0]
                if ip not in seen:
                    seen.add(ip)
                    family = "IPv4" if result[0] == socket.AF_INET else "IPv6"
                    print(f"    {C.GREEN}{ip}{C.RESET} ({C.CYAN}{family}{C.RESET})")
        except socket.gaierror:
            print(f"    {C.RED}Could not resolve '{target}'{C.RESET}")

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_netstat_enhanced(args: list, state: dict, terminal=None) -> int:
    """Enhanced network statistics display."""
    try:
        import psutil
    except ImportError:
        print(C.error("This command requires psutil. pip install psutil"))
        return 1

    print(f"\n{C.BLUE}{'='*75}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ENHANCED NETWORK STATISTICS{C.RESET}")
    print(f"{C.BLUE}{'='*75}{C.RESET}")

    io = psutil.net_io_counters()
    print(f"\n  {C.CYAN}Total Connections{C.RESET}:   {C.WHITE}{psutil.net_connections().__len__()}")

    connections = psutil.net_connections(kind='inet')
    status_counts = {}
    for conn in connections:
        s = conn.status if conn.status else "NONE"
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f"\n  {C.YELLOW}{C.BOLD}Connection Status:{C.RESET}")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        color = C.GREEN if status == "ESTABLISHED" else C.YELLOW if status == "LISTEN" else C.WHITE
        print(f"    {color}{status:<20}{C.RESET} {C.BOLD}{count}{C.RESET}")

    listening = [c for c in connections if c.status == "LISTEN"]
    if listening:
        print(f"\n  {C.YELLOW}{C.BOLD}Listening Ports ({len(listening)}):{C.RESET}")
        print(f"  {C.BOLD}{C.GRAY}{'PID':<10}{'Proto':<8}{'Local Address':<30}{'State':<12}{C.RESET}")
        for conn in sorted(listening, key=lambda x: x.laddr.port):
            pid = str(conn.pid) if conn.pid else "-"
            proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            local = f"{conn.laddr.ip}:{conn.laddr.port}"
            print(f"  {C.CYAN}{pid:<10}{C.RESET}{C.WHITE}{proto:<8}{C.RESET}"
                  f"{C.GREEN}{local:<30}{C.RESET}{C.GREEN}{conn.status:<12}{C.RESET}")

    proc_connections = {}
    for conn in connections:
        pid = conn.pid
        if pid:
            proc_connections[pid] = proc_connections.get(pid, 0) + 1

    if proc_connections:
        print(f"\n  {C.YELLOW}{C.BOLD}Top Processes by Connections:{C.RESET}")
        for pid, count in sorted(proc_connections.items(), key=lambda x: -x[1])[:10]:
            try:
                proc = psutil.Process(pid)
                name = proc.name()
            except Exception:
                name = "unknown"
            print(f"    {C.CYAN}{pid:<8}{C.RESET}{C.WHITE}{name:<25}{C.RESET}{C.GREEN}{count} connections{C.RESET}")

    print(f"\n{C.BLUE}{'='*75}{C.RESET}\n")
    return 0


def cmd_port_scan(args: list, state: dict, terminal=None) -> int:
    """TCP port scanner with service detection."""
    if not args:
        print(C.info("Usage: port-scan <host> [ports] [options]"))
        print(C.info("Options:"))
        print(C.info("  port-scan 192.168.1.1           # Scan common ports"))
        print(C.info("  port-scan 192.168.1.1 1-1024    # Scan port range"))
        print(C.info("  port-scan 192.168.1.1 80,443     # Scan specific ports"))
        print(C.info("  port-scan 192.168.1.1 --all      # Scan all 65535 ports"))
        return 0

    target = args[0]
    ports_str = args[1] if len(args) > 1 else "1-1024"
    threads = 100

    for arg in args[2:]:
        if arg.startswith("--threads="):
            threads = int(arg.split("=")[1])

    try:
        if ports_str == "--all":
            ports = range(1, 65536)
        elif "-" in ports_str:
            start, end = ports_str.split("-")
            ports = range(int(start), int(end) + 1)
        elif "," in ports_str:
            ports = [int(p.strip()) for p in ports_str.split(",")]
        else:
            ports = [int(ports_str)]
    except ValueError:
        print(C.error(f"Invalid port specification: {ports_str}"))
        return 1

    SERVICES = {
        20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP", 80: "HTTP",
        110: "POP3", 111: "RPC", 119: "NNTP", 123: "NTP", 135: "MSRPC",
        137: "NetBIOS-NS", 138: "NetBIOS-DGM", 139: "NetBIOS-SSN", 143: "IMAP",
        161: "SNMP", 162: "SNMPTRAP", 389: "LDAP", 443: "HTTPS",
        445: "Microsoft-DS", 465: "SMTPS", 514: "Syslog", 515: "LPD",
        587: "SMTP-SUB", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
        1080: "SOCKS", 1433: "MSSQL", 1434: "MSSQL-UDP", 1521: "Oracle",
        1723: "PPTP", 2049: "NFS", 2082: "cPanel", 2083: "cPanel-SSL",
        2181: "ZooKeeper", 3000: "Dev-Server", 3306: "MySQL", 3389: "RDP",
        5432: "PostgreSQL", 5500: "VNC-proxy", 5900: "VNC", 5901: "VNC-1",
        6379: "Redis", 6443: "Kubernetes", 8000: "HTTP-Alt", 8080: "HTTP-Proxy",
        8443: "HTTPS-Alt", 8888: "HTTP-Alt", 9000: "PHP-FPM", 9090: "WebConsole",
        9200: "Elasticsearch", 9300: "Elasticsearch", 10000: "WebMin", 11211: "Memcached",
        27017: "MongoDB", 27018: "MongoDB", 50000: "SAP", 50070: "Hadoop"
    }

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║              TCP PORT SCAN — {target:<39}║" if len(target) <= 39 else f"  ║              TCP PORT SCAN — {target[:39]}...{C.RESET}")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(C.error(f"Could not resolve: {target}"))
        return 1

    print(f"  {C.CYAN}Resolved{C.RESET}:   {target} -> {ip}")
    print(f"  {C.CYAN}Ports{C.RESET}:     {len(list(ports)) if hasattr(ports, '__len__') else 'all'}")
    print(f"  {C.CYAN}Threads{C.RESET}:   {threads}\n")

    open_ports = []
    scanned = 0
    total = len(list(ports)) if hasattr(ports, '__len__') else 0

    def scan_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            sock.close()
            return port if result == 0 else None
        except Exception:
            return None

    print(f"  {C.YELLOW}Scanning...{C.RESET}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(scan_port, p): p for p in ports}
        for future in concurrent.futures.as_completed(futures):
            scanned += 1
            result = future.result()
            if result:
                open_ports.append(result)
            if total > 0 and scanned % 100 == 0:
                pct = (scanned / total) * 100
                print(f"\r  {C.GRAY}Progress: {scanned}/{total} ({pct:.1f}%) - Open: {len(open_ports)}{C.RESET}", end="")

    print(f"\r  {C.GREEN}Scan complete. {scanned} ports scanned. Found {len(open_ports)} open.{C.RESET}   ")

    if open_ports:
        print(f"\n  {C.GREEN}{C.BOLD}OPEN PORTS:{C.RESET}")
        print(f"  {C.BOLD}{C.GRAY}{'Port':<8}{'Service':<20}{'State':<10}{C.RESET}")
        print(f"  {C.BLUE}{'─'*55}{C.RESET}")
        for port in sorted(open_ports):
            service = SERVICES.get(port, "unknown")
            state_color = C.GREEN if service != "unknown" else C.YELLOW
            print(f"  {C.CYAN}{port:<8}{C.RESET}{C.WHITE}{service:<20}{C.RESET}{state_color}OPEN{C.RESET}")
    else:
        print(f"\n  {C.YELLOW}No open ports found in the specified range.{C.RESET}")

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_subnet_calc(args: list, state: dict, terminal=None) -> int:
    """Subnet calculator. Usage: subnet-calc <IP/CIDR>"""
    if not args:
        print(C.info("Usage: subnet-calc <IP/CIDR>"))
        print(C.info("Examples:"))
        print(C.info("  subnet-calc 192.168.1.0/24"))
        print(C.info("  subnet-calc 10.0.0.0/26"))
        print(C.info("  subnet-calc 172.16.0.0/16"))
        return 0

    try:
        ip_cidr = args[0]
        if "/" not in ip_cidr:
            ip = ip_cidr
            cidr = 24
        else:
            ip, cidr = ip_cidr.split("/")
            cidr = int(cidr)

        # Parse IP
        ip_parts = [int(x) for x in ip.split(".")]
        ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]

        # Calculate subnet mask
        mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
        mask_parts = [(mask_int >> 24) & 0xFF, (mask_int >> 16) & 0xFF,
                      (mask_int >> 8) & 0xFF, mask_int & 0xFF]

        # Calculate wildcard mask
        wildcard_int = ~mask_int & 0xFFFFFFFF
        wildcard_parts = [(wildcard_int >> 24) & 0xFF, (wildcard_int >> 16) & 0xFF,
                          (wildcard_int >> 8) & 0xFF, wildcard_int & 0xFF]

        # Calculate network address
        network_int = ip_int & mask_int
        network_parts = [(network_int >> 24) & 0xFF, (network_int >> 16) & 0xFF,
                        (network_int >> 8) & 0xFF, network_int & 0xFF]

        # Calculate broadcast address
        broadcast_int = network_int | wildcard_int
        broadcast_parts = [(broadcast_int >> 24) & 0xFF, (broadcast_int >> 16) & 0xFF,
                          (broadcast_int >> 8) & 0xFF, broadcast_int & 0xFF]

        # Calculate usable hosts
        total_hosts = 2 ** (32 - cidr)
        usable_hosts = max(0, total_hosts - 2)

        first_usable = network_parts[:]
        last_usable = broadcast_parts[:]
        if usable_hosts > 0:
            first_usable[3] = network_parts[3] + 1
            last_usable[3] = broadcast_parts[3] - 1

        print(f"\n{C.BLUE}{'='*65}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}SUBNET CALCULATION: {ip}/{cidr}{C.RESET}")
        print(f"{C.BLUE}{'='*65}{C.RESET}")

        def row(label, value):
            print(f"  {C.CYAN}{label:<20}{C.RESET}: {C.WHITE}{value}{C.RESET}")

        row("Network", f"{'.'.join(map(str, network_parts))}/{cidr}")
        row("Broadcast", ".".join(map(str, broadcast_parts)))
        row("Subnet Mask", ".".join(map(str, mask_parts)))
        row("Wildcard Mask", ".".join(map(str, wildcard_parts)))
        row("First Usable", ".".join(map(str, first_usable)))
        row("Last Usable", ".".join(map(str, last_usable)))
        row("Total Hosts", str(total_hosts))
        row("Usable Hosts", str(usable_hosts))

        # Calculate CIDR notation ranges
        print(f"\n  {C.YELLOW}{C.BOLD}IP Classes:{C.RESET}")
        first_octet = ip_parts[0]
        if first_octet < 128:
            ip_class = "A"
        elif first_octet < 192:
            ip_class = "B"
        elif first_octet < 224:
            ip_class = "C"
        elif first_octet < 240:
            ip_class = "D (Multicast)"
        else:
            ip_class = "E (Reserved)"

        row("IP Class", ip_class)
        row("Private", "Yes" if _is_private(ip_parts) else "No")

        print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")

    except Exception as e:
        print(C.error(f"Invalid IP/CIDR: {args[0] if args else 'None'}"))
        print(C.error(f"Error: {e}"))
        return 1

    return 0


def _is_private(ip_parts):
    """Check if IP is in private range."""
    if ip_parts[0] == 10:
        return True
    if ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
        return True
    if ip_parts[0] == 192 and ip_parts[1] == 168:
        return True
    return False


def cmd_dns_lookup(args: list, state: dict, terminal=None) -> int:
    """DNS lookup tool. Usage: dns-lookup <domain> [type]"""
    if not args:
        print(C.info("Usage: dns-lookup <domain> [record_type]"))
        print(C.info("Record types: A, AAAA, MX, TXT, NS, CNAME, SOA, PTR"))
        print(C.info("Examples:"))
        print(C.info("  dns-lookup google.com"))
        print(C.info("  dns-lookup google.com MX"))
        return 0

    domain = args[0]
    record_type = args[1].upper() if len(args) > 1 else "A"

    try:
        import dns.resolver
        import dns.exception
    except ImportError:
        print(C.error("dns-python library required. Install with: pip install dnspython"))
        return 1

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DNS LOOKUP: {domain} ({record_type}){C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}\n")

    try:
        answers = dns.resolver.resolve(domain, record_type)
        for rdata in answers:
            if record_type == "MX":
                print(f"  {C.CYAN}MX{C.RESET}:    {C.GREEN}{rdata.preference}{C.RESET} {C.WHITE}{rdata.exchange}{C.RESET}")
            elif record_type == "TXT":
                print(f"  {C.CYAN}TXT{C.RESET}:   {C.GREEN}{rdata.strings[0].decode() if rdata.strings else ''}{C.RESET}")
            elif record_type == "SOA":
                print(f"  {C.CYAN}SOA{C.RESET}:   {C.GREEN}NS: {rdata.mname}  Admin: {rdata.rname}{C.RESET}")
            elif record_type == "NS":
                print(f"  {C.CYAN}NS{C.RESET}:    {C.GREEN}{rdata}{C.RESET}")
            elif record_type == "CNAME":
                print(f"  {C.CYAN}CNAME{C.RESET}: {C.GREEN}{rdata}{C.RESET}")
            elif record_type == "AAAA":
                print(f"  {C.CYAN}AAAA{C.RESET}:  {C.GREEN}{rdata}{C.RESET}")
            else:
                print(f"  {C.CYAN}A{C.RESET}:     {C.GREEN}{rdata}{C.RESET}")

        print(f"\n  {C.GRAY}Found {len(answers)} record(s){C.RESET}")

    except dns.resolver.NXDOMAIN:
        print(C.error(f"Domain not found: {domain}"))
        return 1
    except dns.resolver.NoAnswer:
        print(C.warn(f"No {record_type} records found for {domain}"))
    except Exception as e:
        print(C.error(f"DNS lookup failed: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def cmd_whois_lookup(args: list, state: dict, terminal=None) -> int:
    """WHOIS lookup tool. Usage: whois <domain>"""
    if not args:
        print(C.info("Usage: whois <domain>"))
        return 0

    domain = args[0]
    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}WHOIS LOOKUP: {domain}{C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}\n")

    try:
        import whois
        w = whois.whois(domain)

        def field(label, value):
            if value:
                print(f"  {C.CYAN}{label:<20}{C.RESET}: {C.WHITE}{value}{C.RESET}")

        field("Domain Name", w.domain_name if isinstance(w.domain_name, str) else w.domain_name[0] if w.domain_name else "N/A")
        field("Registrar", w.registrar)
        field("Whois Server", w.whois_server)
        field("DNSSEC", w.dnssec)
        field("Name Servers", w.name_servers if isinstance(w.name_servers, str) else ", ".join(w.name_servers) if w.name_servers else "N/A")

        if w.creation_date:
            field("Created", w.creation_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(w.creation_date, 'strftime') else str(w.creation_date))
        if w.expiration_date:
            field("Expires", w.expiration_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(w.expiration_date, 'strftime') else str(w.expiration_date))
        if w.updated_date:
            field("Updated", w.updated_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(w.updated_date, 'strftime') else str(w.updated_date))

    except ImportError:
        print(C.error("python-whois library required. Install with: pip install python-whois"))
        return 1
    except Exception as e:
        print(C.error(f"WHOIS lookup failed: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def cmd_traceroute(args: list, state: dict, terminal=None) -> int:
    """Traceroute utility. Usage: traceroute <host>"""
    if not args:
        print(C.info("Usage: traceroute <host>"))
        return 0

    target = args[0]
    max_hops = 30
    timeout = 2

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}TRACEROUTE TO: {target}{C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}\n")

    try:
        for ttl in range(1, max_hops + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_IPROTO_ICMP if hasattr(socket, 'IPROTO_ICMP') else 1)
                sock.settimeout(timeout)

                start_time = time.time()
                sock.sendto(b'', (target, 33434 + ttl))
                addr, _ = sock.recvfrom(512)
                elapsed = (time.time() - start_time) * 1000

                try:
                    hostname = socket.gethostbyaddr(addr[0])[0]
                except socket.herror:
                    hostname = addr[0]

                print(f"  {C.CYAN}{ttl:>2}{C.RESET}  {C.GREEN if ttl < max_hops else C.YELLOW}{addr[0]:<20}{C.RESET}  {C.WHITE}{hostname:<40}{C.RESET}  {C.GRAY}{elapsed:.2f}ms{C.RESET}")

                if addr[0] == target:
                    print(f"\n  {C.GREEN}Destination reached!{C.RESET}")
                    break

            except socket.timeout:
                print(f"  {C.CYAN}{ttl:>2}{C.RESET}  {C.YELLOW}*{C.RESET}                    {C.GRAY}Request timed out{C.RESET}")
            except Exception as e:
                print(f"  {C.CYAN}{ttl:>2}{C.RESET}  {C.RED}Error: {e}{C.RESET}")
                break

    except Exception as e:
        print(C.error(f"Traceroute failed: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def cmd_ping_sweep(args: list, state: dict, terminal=None) -> int:
    """Ping sweep for network discovery. Usage: ping-sweep <network/CIDR>"""
    if not args:
        print(C.info("Usage: ping-sweep <network/CIDR>"))
        print(C.info("Examples:"))
        print(C.info("  ping-sweep 192.168.1.0/24"))
        print(C.info("  ping-sweep 10.0.0.0/26"))
        return 0

    network = args[0]
    timeout = 1

    try:
        if "/" not in network:
            print(C.error("Please specify CIDR notation (e.g., 192.168.1.0/24)"))
            return 1

        ip, cidr = network.split("/")
        cidr = int(cidr)

        ip_parts = [int(x) for x in ip.split(".")]
        network_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
        mask = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
        network_int = network_int & mask

        total_hosts = 2 ** (32 - cidr)
        if total_hosts > 256:
            print(C.warn(f"Large network ({total_hosts} hosts). This may take a while..."))

    except Exception as e:
        print(C.error(f"Invalid network specification: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PING SWEEP: {network}{C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}\n")

    alive_hosts = []
    scanned = 0

    def ping_host(ip_int):
        ip_str = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, getattr(socket, 'IPPROTO_ICMP', 1))
            sock.settimeout(timeout)
            sock.sendto(b'', (ip_str, 0))
            sock.recvfrom(512)
            sock.close()
            return ip_str
        except:
            try:
                sock.close()
            except:
                pass
            return None

    print(f"  {C.YELLOW}Scanning...{C.RESET}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(max(0, network_int - 1), network_int + total_hosts):
            futures.append(executor.submit(ping_host, i))
            scanned += 1

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                alive_hosts.append(result)
            print(f"\r  {C.GRAY}Scanned: {scanned}/{total_hosts} - Alive: {len(alive_hosts)}{C.RESET}", end="")

    print(f"\n\n  {C.GREEN}{C.BOLD}ALIVE HOSTS ({len(alive_hosts)}):{C.RESET}")
    if alive_hosts:
        for host in sorted(alive_hosts, key=lambda x: [int(p) for p in x.split('.')]):
            print(f"  {C.CYAN}{host}{C.RESET}")
    else:
        print(f"  {C.GRAY}No hosts found alive{C.RESET}")

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def _fmt_bytes(n: int) -> str:
    """Human-readable byte count."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# Import time for traceroute
import time