import os
import requests
import netrc

NETRC_PATH = os.path.expanduser("~/.netrc")
print(f"🔍 Checking .netrc at: {NETRC_PATH}")

# --- Step 1: Debug: check file exists ---
if not os.path.exists(NETRC_PATH):
    print("❌ .netrc file not found!")
    exit(1)

# --- Step 2: Parse .netrc ---
try:
    n = netrc.netrc(NETRC_PATH)
    auth = n.authenticators("urs.earthdata.nasa.gov")
    if auth:
        print(f"✅ Found entry for urs.earthdata.nasa.gov in .netrc")
        print(f"   Username: {auth[0]}")
        print(f"   (Password hidden)")
    else:
        print("❌ No entry for urs.earthdata.nasa.gov in .netrc")
        exit(1)
except Exception as e:
    print("❌ Error parsing .netrc:", e)
    exit(1)

# --- Step 3: Make debug request ---
url = "https://urs.earthdata.nasa.gov/profile"

with requests.Session() as s:
    s.auth = (auth[0], auth[2])  # (username, password)

    print(f"🌍 Sending request to: {url}")
    try:
        resp = s.get(url, timeout=30)
        print("🔎 Request headers sent:")
        for k, v in resp.request.headers.items():
            print(f"   {k}: {v}")

        print(f"\n📡 HTTP status: {resp.status_code}")
        print(f"📍 Final URL (after redirects): {resp.url}")

        print("\n🔎 Response headers:")
        for k, v in resp.headers.items():
            print(f"   {k}: {v}")

        # Only print first 500 chars of HTML (to avoid huge dumps)
        print("\n🔎 Response body (truncated):")
        print(resp.text[:500])

        if resp.ok:
            print("\n✅ Success! Earthdata login worked.")
        else:
            print("\n⚠️ Authentication failed.")

    except Exception as e:
        print("❌ Error making request:", e)
