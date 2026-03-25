from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

# ✅ CORS (important for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 Cache system
cache_data = {}
cache_time = {}
CACHE_DURATION = 30  # seconds


def fetch_nse(symbol):

    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()

    # Step 1: Get cookies
    session.get("https://www.nseindia.com", headers=headers, timeout=5)

    # Step 2: Fetch data
    response = session.get(url, headers=headers, timeout=5)

    # 🔍 Debug: check response
    if response.status_code != 200:
        raise Exception("NSE blocked request")

    try:
        data = response.json()
    except:
        raise Exception("Invalid JSON (blocked by NSE)")

    # 🔴 Check if correct data
    if "records" not in data:
        raise Exception("NSE returned invalid structure")

    result = []

    for row in data["records"]["data"]:
        if "CE" in row and "PE" in row:
            result.append({
                "strike": row["strikePrice"],
                "ce": row["CE"]["lastPrice"],
                "pe": row["PE"]["lastPrice"],
                "ceOI": row["CE"]["openInterest"],
                "peOI": row["PE"]["openInterest"]
            })

    return result

import time

# retry once
response = session.get(url, headers=headers, timeout=5)

if response.status_code != 200:
    time.sleep(1)
    response = session.get(url, headers=headers, timeout=5)

@app.get("/")
def home():
    return {"status": "API running 🚀"}


@app.get("/option-chain")
def get_option_chain(symbol: str = "NIFTY"):

    now = time.time()

    # 🔥 Return cached data if available
    if symbol in cache_data and (now - cache_time[symbol]) < CACHE_DURATION:
        return {
            "source": "cache",
            "data": cache_data[symbol]
        }

    try:
        data = fetch_nse(symbol)

        cache_data[symbol] = data
        cache_time[symbol] = now

        return {
            "source": "live",
            "data": data
        }

except Exception as e:
    return {
        "error": str(e),
        "message": "NSE blocked or failed",
        "data": cache_data.get(symbol, [])
    }
