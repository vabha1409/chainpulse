"""
modules/cross_chain.py — Cross-chain macro aggregator
Net flows, capital rotation, chain dominance, inter-chain bridge activity
"""

from datetime import datetime
from utils.display import (
    section, success, info, warn, make_table,
    format_usd, format_pct, metric_card, chain_badge
)
from utils import fetcher

CHAIN_COINGECKO_IDS = {
    "eth": "ethereum",
    "btc": "bitcoin",
    "sol": "solana",
    "bnb": "binancecoin",
    "arb": "arbitrum",
    "pol": "matic-network",
    "avax": "avalanche-2",
    "base": "ethereum",  # Base uses ETH
}

CHAIN_DEFILLAMA_NAMES = {
    "eth": "Ethereum",
    "bnb": "BSC",
    "arb": "Arbitrum",
    "sol": "Solana",
    "pol": "Polygon",
    "avax": "Avalanche",
    "base": "Base",
}


class CrossChainAggregator:
    def __init__(self, chains=None, verbose=False):
        self.chains = chains or ["eth", "btc"]
        self.verbose = verbose

    def run(self, metric="all"):
        chains_display = " | ".join(chain_badge(c) for c in self.chains)
        section(f"Cross-Chain Aggregator  |  {chains_display}")

        prices = self._fetch_all_prices()
        tvl_data = self._fetch_chain_tvls()
        global_data = self._fetch_global_metrics()

        if metric in ("flows", "all"):
            self._display_price_performance(prices)

        if metric in ("activity", "all"):
            self._display_tvl_comparison(tvl_data)

        if metric in ("dominance", "all"):
            self._display_dominance(global_data, prices)

        self._display_macro_signals(prices, tvl_data, global_data)
        self._display_rotation_opportunities(prices, tvl_data)

        result = {
            "command": "aggregate",
            "chains": self.chains,
            "prices": prices,
            "timestamp": datetime.utcnow().isoformat()
        }
        success("Cross-chain aggregation complete.")
        return result

    def _fetch_all_prices(self):
        ids = list({CHAIN_COINGECKO_IDS.get(c, c) for c in self.chains})
        ids_str = ",".join(ids)
        data = fetcher.fetch(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ids_str,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_7d_change": "true",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
            },
            ttl=5, label="cross-chain-prices"
        )
        return data or {}

    def _fetch_chain_tvls(self):
        """Fetch TVL for each chain from DeFiLlama."""
        all_protocols = fetcher.get_all_protocols() or []
        chain_tvl = {}
        for c in self.chains:
            if c == "btc":
                # BTC DeFi is minimal, skip TVL
                chain_tvl["btc"] = {"tvl": 0, "protocols": 0}
                continue
            name = CHAIN_DEFILLAMA_NAMES.get(c, c.capitalize())
            total = sum(
                p.get("tvl", 0)
                for p in all_protocols
                if name in (p.get("chains") or [])
            )
            count = sum(
                1 for p in all_protocols
                if name in (p.get("chains") or [])
            )
            chain_tvl[c] = {"tvl": total, "protocols": count}
        return chain_tvl

    def _fetch_global_metrics(self):
        return fetcher.get_global_stats() or {}

    def _display_price_performance(self, prices):
        section("Price Performance by Chain")
        rows = []
        for chain in self.chains:
            cg_id = CHAIN_COINGECKO_IDS.get(chain, chain)
            p = prices.get(cg_id, {})
            price = p.get("usd", 0)
            change_24h = p.get("usd_24h_change", 0) or 0
            change_7d = p.get("usd_7d_change", 0) or 0
            vol_24h = p.get("usd_24h_vol", 0) or 0
            mcap = p.get("usd_market_cap", 0) or 0

            rows.append([
                chain_badge(chain),
                format_usd(price),
                format_pct(change_24h, color=False),
                format_pct(change_7d, color=False),
                format_usd(vol_24h),
                format_usd(mcap),
            ])

        make_table(
            "Native Asset Performance",
            ["Chain", "Price", "24H Δ", "7D Δ", "Volume 24H", "Market Cap"],
            rows
        )

    def _display_tvl_comparison(self, tvl_data):
        section("DeFi TVL by Chain")
        total_tvl = sum(d["tvl"] for d in tvl_data.values())
        rows = []
        for chain, data in sorted(tvl_data.items(), key=lambda x: x[1]["tvl"], reverse=True):
            tvl = data["tvl"]
            share = tvl / max(total_tvl, 1) * 100
            protocols = data["protocols"]
            bar = "█" * min(int(share / 2), 30)
            rows.append([
                chain_badge(chain),
                format_usd(tvl),
                f"{share:.1f}%",
                str(protocols),
                bar,
            ])

        make_table(
            "Chain TVL Comparison",
            ["Chain", "Total TVL", "DeFi Share", "Protocols", "Dominance"],
            rows
        )
        print()
        metric_card("Total Cross-Chain TVL", format_usd(total_tvl))
        print()

    def _display_dominance(self, global_data, prices):
        section("Market Dominance")
        data = global_data.get("data", {})
        dominance = data.get("market_cap_percentage", {})

        rows = []
        dom_pairs = sorted(dominance.items(), key=lambda x: x[1], reverse=True)[:8]
        for coin, pct in dom_pairs:
            rows.append([coin.upper(), f"{pct:.2f}%"])

        make_table("Market Cap Dominance", ["Asset", "Dominance %"], rows)

        total_mcap = data.get("total_market_cap", {}).get("usd", 0)
        btc_dom = dominance.get("btc", 0)
        eth_dom = dominance.get("eth", 0)
        alt_dom = 100 - btc_dom - eth_dom

        print()
        metric_card("Total Crypto Market Cap", format_usd(total_mcap))
        metric_card("BTC Dominance", f"{btc_dom:.1f}%")
        metric_card("ETH Dominance", f"{eth_dom:.1f}%")
        metric_card("Altcoin Dominance", f"{alt_dom:.1f}%")
        print()

    def _display_macro_signals(self, prices, tvl_data, global_data):
        section("Macro On-Chain Signals")

        data = global_data.get("data", {})
        btc_dom = data.get("market_cap_percentage", {}).get("btc", 50)
        eth_dom = data.get("market_cap_percentage", {}).get("eth", 17)

        # BTC dominance signal
        if btc_dom > 55:
            warn(f"BTC dominance HIGH ({btc_dom:.1f}%) — risk-off environment, alts likely underperforming")
        elif btc_dom < 40:
            info(f"BTC dominance LOW ({btc_dom:.1f}%) — alt season conditions, risk-on environment")
        else:
            info(f"BTC dominance NEUTRAL ({btc_dom:.1f}%) — mixed market conditions")

        # ETH/BTC flippening watch
        eth_cg = CHAIN_COINGECKO_IDS.get("eth", "ethereum")
        btc_cg = CHAIN_COINGECKO_IDS.get("btc", "bitcoin")
        eth_price = prices.get(eth_cg, {}).get("usd", 0)
        btc_price = prices.get(btc_cg, {}).get("usd", 1)
        if eth_price and btc_price:
            ratio = eth_price / btc_price
            info(f"ETH/BTC ratio: {ratio:.4f}  ({'accumulating relative strength' if ratio > 0.065 else 'BTC outperforming'})")

        # TVL momentum
        eth_tvl = tvl_data.get("eth", {}).get("tvl", 0)
        if eth_tvl > 50e9:
            info(f"ETH DeFi TVL strong at {format_usd(eth_tvl)} — ecosystem activity healthy")

        # Fear & Greed proxy (using 24h vol change)
        total_vol = data.get("total_volume", {}).get("usd", 0)
        total_mcap = data.get("total_market_cap", {}).get("usd", 1)
        vol_mcap_ratio = total_vol / total_mcap
        if vol_mcap_ratio > 0.1:
            warn(f"High volume/mcap ratio ({vol_mcap_ratio:.2%}) — elevated volatility, possible trend day")
        else:
            info(f"Volume/mcap ratio: {vol_mcap_ratio:.2%} — normal market conditions")

    def _display_rotation_opportunities(self, prices, tvl_data):
        section("Capital Rotation Signals")

        performers = []
        for chain in self.chains:
            cg_id = CHAIN_COINGECKO_IDS.get(chain, chain)
            p = prices.get(cg_id, {})
            change_7d = p.get("usd_7d_change", 0) or 0
            tvl = tvl_data.get(chain, {}).get("tvl", 0)
            performers.append((chain, change_7d, tvl))

        performers.sort(key=lambda x: x[1])

        if len(performers) >= 2:
            laggard = performers[0]
            leader = performers[-1]
            if leader[1] - laggard[1] > 10:
                info(f"Rotation opportunity: {chain_badge(laggard[0])} lagging "
                     f"({format_pct(laggard[1], color=False)}) vs {chain_badge(leader[0])} "
                     f"({format_pct(leader[1], color=False)}) over 7D — watch for mean reversion")
            else:
                info("Chains moving in sync — no significant rotation signal detected.")
