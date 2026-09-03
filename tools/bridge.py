"""Socket client for the BlenderMCP addon listening on 127.0.0.1:9876."""
import socket, json, sys

HOST, PORT = "127.0.0.1", 9876


def send(cmd_type, params=None, timeout=180):
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    try:
        s.sendall(json.dumps({"type": cmd_type, "params": params or {}}).encode())
        chunks = b""
        while True:
            chunk = s.recv(1 << 20)
            if not chunk:
                break
            chunks += chunk
            try:
                return json.loads(chunks.decode())
            except json.JSONDecodeError:
                continue
        raise RuntimeError("connection closed before a complete response")
    finally:
        s.close()


def run(code, timeout=180):
    """Execute Python inside Blender. Raises on error, returns stdout text."""
    r = send("execute_code", {"code": code}, timeout)
    if r.get("status") != "success":
        raise RuntimeError(r.get("message") or json.dumps(r))
    res = r.get("result")
    return res.get("result", res) if isinstance(res, dict) else res


if __name__ == "__main__":
    print(run(sys.stdin.read()))
