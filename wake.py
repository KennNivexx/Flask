import requests
import time
import os

RAILWAY_URL = os.environ.get("RAILWAY_URL")  # ganti sesuai domain Railway

if not RAILWAY_URL:
    print("ERROR: RAILWAY_URL belum di-set")
    exit(1)

print(f"[WAKE-UP] Pinging {RAILWAY_URL} every 60s")

while True:
    try:
        r = requests.get(RAILWAY_URL)
        if r.status_code == 200:
            print("[WAKE-UP] Ping successful")
        else:
            print(f"[WAKE-UP] Ping returned {r.status_code}")
    except Exception as e:
        print(f"[WAKE-UP] Ping failed: {e}")
    time.sleep(60)
