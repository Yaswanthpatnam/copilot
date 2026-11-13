import os
import sys
import socket
import uvicorn
from main import app


def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    """Checks whether the requested port is already bound by another process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def get_local_ip() -> str:
    """Determines the LAN IP address for mobile phone access."""
    try:
        # Create a dummy UDP socket to find the default outbound interface IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def print_banner(host: str, port: int, local_ip: str):
    print("\n" + "=" * 70)
    print(" 🏭 KAVERI PRECISION COMPONENTS (HOSUR PLANT) — AI COPILOT")
    print("=" * 70)
    print(f" Local Web Access:    http://localhost:{port}")
    print(f" Phone / Network IP:  http://{local_ip}:{port}")
    print("=" * 70)
    print(" Supervise from your mobile device by visiting the Network IP above.")
    print(" Press Ctrl+C to terminate.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    host = "0.0.0.0"
    
    # Allow custom port via CLI argument or environment variable
    default_port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        target_port = int(sys.argv[1])
    else:
        target_port = int(os.environ.get("PORT", default_port))

    # Auto-detect port collision and cleanly select next available port if 8080 is locked
    if is_port_in_use(target_port, host):
        print(f"[!] Warning: Port {target_port} is already in use by another process.")
        fallback_port = target_port + 1
        print(f"[*] Automatically falling back to available port {fallback_port}...")
        target_port = fallback_port

    local_ip = get_local_ip()
    print_banner(host, target_port, local_ip)
    uvicorn.run("main:app", host=host, port=target_port, reload=False, log_level="info")
