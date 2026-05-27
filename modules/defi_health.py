"""
modules/defi_health.py — DeFi protocol health & risk analysis
TVL trends, utilization rates, fee revenue, liquidity depth scoring
"""

import math
from datetime import datetime
from utils.display import (
    section, success, info, warn, error, make_table,
    format_usd, format_pct, metric_card, chain_badge
)
from utils import fetcher


PROTOCOL_SLUGS = {
    "uniswap": "uniswap",
    "aave": "aave-v3",
    "curve": "curve-dex",
    "compound": "compound-finance",
    "maker": "makerdao",
    "lido": "lido",
    "balancer": "balancer-v2",
    "gmx": "gmx",
    "synthetix": "synthetix",
    "convex": "convex-finance",
    "yearn": "yearn-finance",
    "sushiswap": "sushiswap",
    "pancakeswap": "pancakeswap",
    "dydx": "dydx",
}


class DeFiHealthAnalyzer:
    def __init__(self, chain="eth", verbose=False):
        self.chain = chain
        self.verbose = verbose

    def run(self, protocol=None, metric="all", compare=None):
        section(f"DeFi Health Analyzer  |  {chain_badge(self.chain)}")

        if compare:
            return self._compare_protocols(compare, metric)
        elif protocol:
            return self._single_protocol(protocol, metric)
        else:
            return self._chain_overview(metric)

    def _chain_overview(self, metric):
        info(f"Fetching top DeFi protocols on {self.chain.upper()}...")

        all_protocols = fetcher.get_all_protocols()
        if not all_protocols:
            warn("Could not fetch protocol data.")
            return {}

        # Filter by chain and sort by TVL
        chain_name_map = {
            "eth": "Ethereum", "bnb": "BSC", "arb": "Arbitrum",
            "sol": "Solana", "pol": "Polygon"
        }
        chain_name = chain_name_map.get(self.chain, self.chain.capitalize())

        chain_protocols = [
            p for p in all_protocols
            if isinstance(p.get("chains"), list) and chain_name in p["chains"]
        ]
        chain_protocols.sort(key=lambda x: x.get("tvl", 0), reverse=True)

        top10 = chain_protocols[:10]
        total_tvl = sum(p.get("tvl", 0) for p in top10)

        print()
        metric_card("Total TVL (Top 10)", format_usd(total_tvl))
        metric_card("Protocols Tracked", str(len(chain_protocols)))
        print()

        rows = []
        for i, p in enumerate(top10):
            tvl = p.get("tvl", 0)
            change_1d = p.get("change_1d", 0) or 0
            change_7d = p.get("change_7d", 0) or 0
            category = p.get("category", "Unknown")
            health = self._health_score(p)

            rows.append([
                str(i + 1),
                p.get("name", "?")[:22],
                category[:15],
                format_usd(tvl),
                format_pct(change_1d, color=False),
                format_pct(change_7d, color=False),
                self._health_label(health),
            ])

        make_table(
            f"Top DeFi Protocols on {chain_name}",
            ["#", "Protocol", "Category", "TVL", "1D Δ", "7D Δ", "Health"],
            rows
        )

        self._stablecoin_snapshot()

        result = {"command": "defi", "chain": self.chain, "protocols": top10, "total_tvl": total_tvl}
        success("DeFi health scan complete.")
        return result

    def _single_protocol(self, protocol, metric):
        slug = PROTOCOL_SLUGS.get(protocol.lower(), protocol.lower())
        info(f"Fetching detailed data for {protocol.upper()} (slug: {slug})")

        data = fetcher.get_protocol_tvl(slug)
        if not data:
            warn(f"Protocol '{slug}' not found. Try one of: {', '.join(PROTOCOL_SLUGS.keys())}")
            return {}

        print()
        name = data.get("name", protocol)
        tvl = data.get("tvl", 0)
        change_1d = data.get("change_1d", 0) or 0
        change_7d = data.get("change_7d", 0) or 0
        category = data.get("category", "Unknown")
        chains = data.get("chains", [])
        description = data.get("description", "")

        section(f"  {name}  |  {category}")
        if description:
            info(description[:180] + ("..." if len(description) > 180 else ""))
        print()

        metric_card("Total TVL", format_usd(tvl), delta=change_1d)
        metric_card("7-Day Change", "", delta=change_7d)
        metric_card("Active Chains", str(len(chains)))
        print()

        if metric in ("tvl", "all"):
            self._tvl_trend(data)

        if metric in ("fees", "all"):
            self._fee_analysis(slug, name)

        # Chain breakdown
        chain_tvls = data.get("chainTvls", {})
        if chain_tvls:
            section("TVL by Chain")
            chain_rows = []
            for cname, cdata in sorted(chain_tvls.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:8]:
                val = cdata if isinstance(cdata, (int, float)) else (cdata.get("tvl", 0) if isinstance(cdata, dict) else 0)
                share = val / tvl * 100 if tvl else 0
                chain_rows.append([cname, format_usd(val), f"{share:.1f}%"])
            make_table("Chain Distribution", ["Chain", "TVL", "Share"], chain_rows)

        health = self._health_score(data)
        section("Protocol Health Score")
        self._print_health_breakdown(health, data)

        result = {"command": "defi", "protocol": protocol, "data": data}
        success(f"{name} analysis complete.")
        return result

    def _compare_protocols(self, protocols, metric):
        section(f"Protocol Comparison  |  {', '.join(protocols)}")
        results = []
        for p in protocols:
            slug = PROTOCOL_SLUGS.get(p.lower(), p.lower())
            data = fetcher.get_protocol_tvl(slug)
            if data:
                results.append((p, data))
            else:
                warn(f"No data for {p}")

        if not results:
            error("No protocol data retrieved.")
            return {}

        rows = []
        for name, d in results:
            tvl = d.get("tvl", 0)
            c1d = d.get("change_1d", 0) or 0
            c7d = d.get("change_7d", 0) or 0
            health = self._health_score(d)
            rows.append([
                name.capitalize(),
                format_usd(tvl),
                format_pct(c1d, color=False),
                format_pct(c7d, color=False),
                str(len(d.get("chains", []))),
                self._health_label(health),
            ])

        make_table("Protocol Comparison", ["Protocol", "TVL", "1D Δ", "7D Δ", "Chains", "Health"], rows)

        # Winner analysis
        best_tvl = max(results, key=lambda x: x[1].get("tvl", 0))
        best_growth = max(results, key=lambda x: x[1].get("change_7d", 0) or 0)
        info(f"Largest by TVL: {best_tvl[0].capitalize()} ({format_usd(best_tvl[1].get('tvl', 0))})")
        info(f"Fastest growing (7D): {best_growth[0].capitalize()} ({format_pct(best_growth[1].get('change_7d', 0) or 0, color=False)})")

        result = {"command": "defi", "comparison": [r[0] for r in results]}
        success("Protocol comparison complete.")
        return result

    def _tvl_trend(self, data):
        section("TVL Trend (30D)")
        tvl_history = data.get("tvl", [])
        if isinstance(tvl_history, list) and len(tvl_history) > 1:
            recent = tvl_history[-30:]
            step = max(1, len(recent) // 8)
            for entry in recent[::step]:
                date = datetime.fromtimestamp(entry.get("date", 0)).strftime("%Y-%m-%d")
                val = entry.get("totalLiquidityUSD", 0)
                bar_len = int(val / max(recent[-1].get("totalLiquidityUSD", 1), 1) * 30)
                print(f"  {date}  {'█' * bar_len}  {format_usd(val)}")
        else:
            info("TVL history not available in this format.")

    def _fee_analysis(self, slug, name):
        section(f"Fee Revenue  |  {name}")
        fee_data = fetcher.get_protocol_fees(slug)
        if fee_data:
            total_24h = fee_data.get("total24h", 0) or 0
            total_7d = fee_data.get("total7d", 0) or 0
            total_30d = fee_data.get("total30d", 0) or 0
            metric_card("Fees (24H)", format_usd(total_24h))
            metric_card("Fees (7D)", format_usd(total_7d))
            metric_card("Fees (30D)", format_usd(total_30d))
            print()
        else:
            info("Fee data not available for this protocol.")

    def _stablecoin_snapshot(self):
        section("Stablecoin Market Snapshot")
        data = fetcher.get_stablecoin_data()
        if not data:
            return
        coins = sorted(
            data.get("peggedAssets", []),
            key=lambda x: x.get("circulating", {}).get("peggedUSD", 0),
            reverse=True
        )[:6]
        rows = []
        for c in coins:
            circ = c.get("circulating", {}).get("peggedUSD", 0)
            name = c.get("name", "?")[:18]
            symbol = c.get("symbol", "?")
            chains = len(c.get("chains", []))
            peg_type = c.get("pegType", "USD")
            rows.append([name, symbol, format_usd(circ), str(chains), peg_type])
        make_table("Top Stablecoins", ["Name", "Symbol", "Circulating", "Chains", "Peg"], rows)

    def _health_score(self, protocol_data):
        score = 50  # baseline
        tvl = protocol_data.get("tvl", 0)
        change_7d = protocol_data.get("change_7d", 0) or 0
        chains = len(protocol_data.get("chains", []))

        if tvl > 1e9: score += 20
        elif tvl > 1e8: score += 10
        elif tvl < 1e6: score -= 20

        if change_7d > 5: score += 10
        elif change_7d > 0: score += 5
        elif change_7d < -20: score -= 20
        elif change_7d < -10: score -= 10

        if chains > 5: score += 10
        elif chains > 2: score += 5

        return min(max(score, 0), 100)

    def _health_label(self, score):
        if score >= 75: return "🟢 Healthy"
        if score >= 50: return "🟡 Moderate"
        if score >= 25: return "🟠 Risky"
        return "🔴 Critical"

    def _print_health_breakdown(self, score, data):
        label = self._health_label(score)
        print(f"  Overall Score: {score}/100  {label}")
        print()
        tvl = data.get("tvl", 0)
        change_7d = data.get("change_7d", 0) or 0
        chains = len(data.get("chains", []))

        checks = [
            ("TVL > $100M", tvl > 1e8),
            ("TVL > $1B", tvl > 1e9),
            ("7D Growth Positive", change_7d > 0),
            ("Multi-chain Presence", chains > 2),
            ("Established (Chains > 5)", chains > 5),
        ]
        for check, passed in checks:
            icon = "✓" if passed else "✗"
            print(f"  [{icon}] {check}")
        print()
