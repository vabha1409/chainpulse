"""
utils/fetcher.py — Multi-source data fetcher with caching and fallback
Supports: Etherscan, Blockstream, CoinGecko, DeFiLlama, Moralis
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta
from utils.display import info, warn

CACHE_DIR = Path(__file__).parent.parent / "data" / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

API_KEYS = {
    "etherscan":  os.getenv("ETHERSCAN_API_KEY", ""),
    "moralis":    os.getenv("MORALIS_API_KEY", ""),
    "covalent":   os.getenv("COVALENT_API_KEY", ""),
    "alchemy":    os.getenv("ALCHEMY_API_KEY", ""),
    "bscscan":    os.getenv("BSCSCAN_API_KEY", ""),
    "arbiscan":   os.getenv("ARBISCAN_API_KEY", ""),
}

CHAIN_ID_MAP = {
    "eth": 1, "bnb": 56, "arb": 42161,
    "pol": 137, "avax": 43114, "base": 8453,
}

DEFILLAMA_BASE = "https://api.llama.fi"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BLOCKSTREAM_BASE = "https://blockstream.info/api"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ChainPulse/1.0 (on-chain-analysis)"})


def _cache_key(url, params=None):
    raw = url + json.dumps(params or {}, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_get(key, ttl_minutes=10):
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        age = time.time() - path.stat().st_mtime
        if age < ttl_minutes * 60:
            with open(path) as f:
                return json.load(f)
    return None


def _cache_set(key, data):
    path = CACHE_DIR / f"{key}.json"
    with open(path, "w") as f:
        json.dump(data, f)


def fetch(url, params=None, headers=None, ttl=10, retries=3, label=None):
    """
    Fetch URL with caching, retries, and rate-limit handling.
    Returns parsed JSON or None on failure.
    """
    key = _cache_key(url, params)
    cached = _cache_get(key, ttl_minutes=ttl)
    if cached is not None:
        return cached

    for attempt in range(retries):
        try:
            resp = SESSION.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2 ** attempt))
                warn(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            _cache_set(key, data)
            return data
        except requests.exceptions.Timeout:
            warn(f"Timeout on attempt {attempt+1}/{retries}" + (f" [{label}]" if label else ""))
        except requests.exceptions.HTTPError as e:
            warn(f"HTTP error: {e}")
            break
        except Exception as e:
            warn(f"Fetch error: {e}")
            break

    return None


# ── DeFiLlama helpers ─────────────────────────────────────────────────────────

def get_protocol_tvl(protocol_slug):
    """Get TVL history for a protocol (DeFiLlama)."""
    return fetch(f"{DEFILLAMA_BASE}/protocol/{protocol_slug}", ttl=30, label="defillama-tvl")

def get_all_protocols():
    """List all tracked protocols."""
    return fetch(f"{DEFILLAMA_BASE}/protocols", ttl=60, label="defillama-protocols")

def get_chain_tvl(chain):
    """TVL for all protocols on a chain."""
    return fetch(f"{DEFILLAMA_BASE}/v2/historicalChainTvl/{chain.capitalize()}", ttl=30)

def get_protocol_fees(protocol_slug):
    return fetch(f"https://api.llama.fi/summary/fees/{protocol_slug}", ttl=30)

def get_stablecoin_data():
    return fetch("https://stablecoins.llama.fi/stablecoins?includePrices=true", ttl=60)


# ── CoinGecko helpers ─────────────────────────────────────────────────────────

def get_token_price(token_id, vs="usd"):
    return fetch(
        f"{COINGECKO_BASE}/simple/price",
        params={"ids": token_id, "vs_currencies": vs, "include_24hr_change": "true",
                "include_market_cap": "true", "include_24hr_vol": "true"},
        ttl=5, label="coingecko-price"
    )

def get_top_coins(limit=100):
    return fetch(
        f"{COINGECKO_BASE}/coins/markets",
        params={"vs_currency": "usd", "order": "market_cap_desc",
                "per_page": limit, "page": 1, "sparkline": False},
        ttl=15, label="coingecko-markets"
    )

def get_coin_history(coin_id, days=30):
    return fetch(
        f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        ttl=60, label="coingecko-history"
    )

def get_global_stats():
    return fetch(f"{COINGECKO_BASE}/global", ttl=15, label="coingecko-global")


# ── Etherscan helpers ─────────────────────────────────────────────────────────

def etherscan_call(module, action, extra_params=None, chain="eth"):
    base_urls = {
        "eth": "https://api.etherscan.io/api",
        "bnb": "https://api.bscscan.com/api",
        "arb": "https://api.arbiscan.io/api",
        "pol": "https://api.polygonscan.com/api",
    }
    key_names = {"eth": "etherscan", "bnb": "bscscan", "arb": "arbiscan"}
    base = base_urls.get(chain, base_urls["eth"])
    api_key = API_KEYS.get(key_names.get(chain, "etherscan"), "")

    params = {"module": module, "action": action, "apikey": api_key}
    if extra_params:
        params.update(extra_params)
    return fetch(base, params=params, ttl=5, label=f"etherscan-{action}")

def get_wallet_txns(address, chain="eth", start_block=0):
    return etherscan_call(
        "account", "txlist",
        {"address": address, "startblock": start_block,
         "endblock": 99999999, "sort": "desc"},
        chain=chain
    )

def get_token_holders(token_address, chain="eth"):
    # Token holder distribution via Etherscan token tracker page data
    return etherscan_call(
        "token", "tokenholderlist",
        {"contractaddress": token_address, "page": 1, "offset": 100},
        chain=chain
    )

def get_wallet_balance(address, chain="eth"):
    return etherscan_call("account", "balance", {"address": address, "tag": "latest"}, chain=chain)

def get_token_txns(address, contract, chain="eth"):
    return etherscan_call(
        "account", "tokentx",
        {"address": address, "contractaddress": contract, "sort": "desc"},
        chain=chain
    )


# ── Bitcoin / Blockstream ─────────────────────────────────────────────────────

def get_btc_address(address):
    return fetch(f"{BLOCKSTREAM_BASE}/address/{address}", ttl=5, label="btc-address")

def get_btc_mempool():
    return fetch(f"{BLOCKSTREAM_BASE}/mempool", ttl=1, label="btc-mempool")

def get_btc_fee_estimates():
    return fetch(f"{BLOCKSTREAM_BASE}/fee-estimates", ttl=2, label="btc-fees")

def get_btc_recent_blocks(limit=10):
    return fetch(f"{BLOCKSTREAM_BASE}/blocks", ttl=5, label="btc-blocks")


# ── Solana RPC ────────────────────────────────────────────────────────────────

def solana_rpc(method, params=None):
    url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    try:
        resp = SESSION.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result")
    except Exception as e:
        warn(f"Solana RPC error: {e}")
        return None

def get_sol_account(address):
    return solana_rpc("getAccountInfo", [address, {"encoding": "jsonParsed"}])
