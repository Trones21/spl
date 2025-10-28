#poetry run python3 ./tests/rpc.py

import httpx, json

url = "https://mainnet.helius-rpc.com/?api-key=7deb69c9-fd8c-485a-825e-ced0f56a08e4"
payload = {"jsonrpc":"2.0","id":1,"method":"getVersion","params":[]}
r = httpx.post(url, json=payload, timeout=10)
print(r.status_code)
print(r.headers.get("content-type"))
print(r.text[:400])