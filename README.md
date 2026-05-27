# ⛓ ChainPulse — Multi-Chain On-Chain Analysis Toolkit

> Advanced CLI toolkit for professional crypto on-chain analysis.
> Whale tracking · DeFi health · Token distribution · Smart money detection · Cross-chain aggregation

---

## Features

| Module | Command | What it does |
|---|---|---|
| **Whale Tracker** | `whale` | Detects large wallet movements, flags anomalous flows, accumulation signals |
| **DeFi Health** | `defi` | TVL trends, fee revenue, protocol health scores, stablecoin snapshot |
| **Token Distribution** | `token` | Holder breakdown, Gini coefficient, whale concentration, risk flags |
| **Smart Money** | `smartmoney` | Identifies historically profitable wallets, consensus portfolio signals |
| **Cross-Chain Aggregator** | `aggregate` | Price performance, TVL comparison, BTC dominance, rotation signals |
| **Wallet Profiler** | `wallet` | Deep behavioral analysis, wallet classification, activity timeline |

---

## Installation

```bash
git clone https://github.com/yourname/chainpulse
cd chainpulse
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

---

## Usage

### Whale Tracker
```bash
# Scan ETH for transactions >$500K in last 24 hours, top 20, with anomaly alerts
python chainpulse.py whale --chain eth --threshold 500 --top 20 --alert

# Track Bitcoin whale movements
python chainpulse.py whale --chain btc --threshold 1000 --lookback 48
```

### DeFi Health
```bash
# Full chain DeFi overview
python chainpulse.py defi --chain eth

# Analyze a specific protocol
python chainpulse.py defi --protocol uniswap --metric all

# Compare protocols side-by-side
python chainpulse.py defi --compare uniswap aave curve
```

### Token Distribution
```bash
# Analyze USDC on Ethereum with Gini coefficient
python chainpulse.py token \
  --address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 \
  --chain eth \
  --gini \
  --top-holders 50 \
  --whale-threshold 2.0
```

### Smart Money Detection
```bash
# Find wallets with >300% PnL in last 30 days, track new positions
python chainpulse.py smartmoney --chain eth --lookback 30 --min-pnl 300 --track-new
```

### Cross-Chain Aggregation
```bash
# Full macro view across ETH, BTC, SOL, ARB
python chainpulse.py aggregate --chains eth,btc,sol,arb --metric all

# TVL comparison only
python chainpulse.py aggregate --chains eth,bnb,arb --metric tvl
```

### Wallet Profiling
```bash
# Quick profile
python chainpulse.py wallet --address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --chain eth

# Full history deep dive
python chainpulse.py wallet --address 0x... --chain eth --full
```

### Export Reports
```bash
# Any command + --export [json|csv|pdf]
python chainpulse.py whale --chain eth --threshold 500 --export json
python chainpulse.py defi --protocol aave --export pdf
```

---

## Data Sources

| Source | Data | Rate Limit (Free) |
|---|---|---|
| **DeFiLlama** | TVL, protocol data, fees, stablecoins | No key needed |
| **CoinGecko** | Prices, market caps, dominance | 30 calls/min |
| **Etherscan** | ETH transactions, token holders, balances | 5 calls/sec |
| **BscScan** | BNB Chain data | 5 calls/sec |
| **Arbiscan** | Arbitrum data | 5 calls/sec |
| **Blockstream** | Bitcoin UTXO, mempool | No key needed |
| **Solana RPC** | Solana accounts, transactions | Public mainnet |

---

## Architecture

```
chainpulse/
├── chainpulse.py           # CLI entry point (argparse)
├── modules/
│   ├── whale_tracker.py    # Large tx detection + anomaly scoring
│   ├── defi_health.py      # Protocol health + TVL analysis
│   ├── token_distribution.py # Holder analysis + Gini coefficient
│   ├── smart_money.py      # Profitable wallet detection + copy signals
│   ├── cross_chain.py      # Cross-chain aggregation + rotation signals
│   └── wallet_profiler.py  # Deep behavioral wallet analysis
├── utils/
│   ├── fetcher.py          # Multi-source API fetcher with caching
│   ├── display.py          # Rich terminal output helpers
│   └── report_exporter.py  # JSON/CSV/HTML export
├── data/
│   └── .cache/             # Auto-created response cache (TTL-based)
├── reports/                # Exported reports land here
├── requirements.txt
└── .env.example
```

---

## Key Concepts Demonstrated

- **Gini Coefficient** — mathematical measure of token wealth concentration
- **Smart Money Scoring** — composite PnL + win-rate + timing signal
- **Anomaly Detection** — z-score based flagging of unusual whale flows
- **Capital Rotation Signals** — cross-chain relative strength analysis
- **Wallet Classification** — bot vs. DeFi power user vs. HODLer
- **Multi-source Fallback** — graceful degradation when APIs are unavailable
- **Response Caching** — TTL-based disk cache to respect API rate limits

---

## Extending ChainPulse

### Add a new chain
In `utils/fetcher.py`, add to `CHAIN_ID_MAP` and `CHAIN_COINGECKO_IDS`.

### Add a new analysis module
1. Create `modules/your_module.py` with a class following the pattern
2. Add subparser in `chainpulse.py`
3. Import and wire up in the `main()` function

### Add real whale data (production upgrade)
Replace `_fetch_eth_whales()` in `whale_tracker.py` with:
- **Alchemy** `alchemy_getAssetTransfers` for real large transfers
- **Dune Analytics** API for indexed on-chain data
- **The Graph** subgraph queries via GraphQL

---

## Disclaimer

This tool is for educational and research purposes only.
Not financial advice. Always DYOR before making investment decisions.

---

*Built with Python · DeFiLlama · CoinGecko · Etherscan · Blockstream*
