#!/usr/bin/env python3
"""
ChainPulse — Multi-Chain On-Chain Analysis CLI
Whale tracking | DeFi health | Token distribution | Smart money signals
"""

import argparse
import sys
from modules.whale_tracker import WhaleTracker
from modules.defi_health import DeFiHealthAnalyzer
from modules.token_distribution import TokenDistributionAnalyzer
from modules.smart_money import SmartMoneyDetector
from modules.cross_chain import CrossChainAggregator
from utils.display import banner, success, error, info
from utils.report_exporter import export_report

def main():
    banner()

    parser = argparse.ArgumentParser(
        prog="chainpulse",
        description="Advanced Multi-Chain On-Chain Analysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chainpulse whale --chain eth --threshold 500 --top 20
  chainpulse defi --protocol uniswap --metric tvl
  chainpulse token --address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 --chain eth
  chainpulse smartmoney --chain eth --lookback 30
  chainpulse aggregate --chains eth,btc,sol --export pdf
  chainpulse wallet --address 0xabc... --chain eth --full
        """
    )
    parser.add_argument("--export", choices=["json", "csv", "pdf"], help="Export report format")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Analysis module")

    # ── Whale Tracker ─────────────────────────────────────────────────────────
    whale_parser = subparsers.add_parser("whale", help="Track large wallet movements")
    whale_parser.add_argument("--chain", default="eth", choices=["eth", "btc", "sol", "bnb", "arb"], help="Blockchain")
    whale_parser.add_argument("--threshold", type=float, default=100, help="Min transaction size (USD, thousands)")
    whale_parser.add_argument("--top", type=int, default=10, help="Top N wallets to display")
    whale_parser.add_argument("--lookback", type=int, default=24, help="Hours to look back")
    whale_parser.add_argument("--alert", action="store_true", help="Flag anomalous movements")

    # ── DeFi Health ───────────────────────────────────────────────────────────
    defi_parser = subparsers.add_parser("defi", help="DeFi protocol health metrics")
    defi_parser.add_argument("--protocol", help="Protocol name (uniswap, aave, curve...)")
    defi_parser.add_argument("--metric", choices=["tvl", "volume", "fees", "utilization", "all"], default="all")
    defi_parser.add_argument("--chain", default="eth")
    defi_parser.add_argument("--compare", nargs="+", help="Compare multiple protocols")

    # ── Token Distribution ────────────────────────────────────────────────────
    token_parser = subparsers.add_parser("token", help="Token holder & distribution analysis")
    token_parser.add_argument("--address", required=True, help="Token contract address")
    token_parser.add_argument("--chain", default="eth")
    token_parser.add_argument("--top-holders", type=int, default=20, help="Analyze top N holders")
    token_parser.add_argument("--gini", action="store_true", help="Calculate Gini coefficient")
    token_parser.add_argument("--whale-threshold", type=float, default=1.0, help="Whale % threshold")

    # ── Smart Money ───────────────────────────────────────────────────────────
    sm_parser = subparsers.add_parser("smartmoney", help="Smart money wallet detection")
    sm_parser.add_argument("--chain", default="eth")
    sm_parser.add_argument("--lookback", type=int, default=30, help="Days to look back")
    sm_parser.add_argument("--min-pnl", type=float, default=200, help="Min realized PnL %")
    sm_parser.add_argument("--track-new", action="store_true", help="Flag new positions opened")

    # ── Cross-Chain Aggregator ────────────────────────────────────────────────
    agg_parser = subparsers.add_parser("aggregate", help="Cross-chain macro view")
    agg_parser.add_argument("--chains", default="eth,btc", help="Comma-separated chains")
    agg_parser.add_argument("--metric", choices=["flows", "activity", "dominance", "all"], default="all")

    # ── Wallet Profiler ───────────────────────────────────────────────────────
    wallet_parser = subparsers.add_parser("wallet", help="Deep wallet profiling")
    wallet_parser.add_argument("--address", required=True, help="Wallet address")
    wallet_parser.add_argument("--chain", default="eth")
    wallet_parser.add_argument("--full", action="store_true", help="Full historical analysis")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        result = None

        if args.command == "whale":
            tracker = WhaleTracker(chain=args.chain, verbose=args.verbose)
            result = tracker.run(
                threshold_k=args.threshold,
                top_n=args.top,
                lookback_hours=args.lookback,
                alert=args.alert
            )

        elif args.command == "defi":
            analyzer = DeFiHealthAnalyzer(chain=args.chain, verbose=args.verbose)
            result = analyzer.run(
                protocol=args.protocol,
                metric=args.metric,
                compare=args.compare
            )

        elif args.command == "token":
            analyzer = TokenDistributionAnalyzer(chain=args.chain, verbose=args.verbose)
            result = analyzer.run(
                address=args.address,
                top_holders=args.top_holders,
                calc_gini=args.gini,
                whale_threshold=args.whale_threshold
            )

        elif args.command == "smartmoney":
            detector = SmartMoneyDetector(chain=args.chain, verbose=args.verbose)
            result = detector.run(
                lookback_days=args.lookback,
                min_pnl=args.min_pnl,
                track_new=args.track_new
            )

        elif args.command == "aggregate":
            chains = [c.strip() for c in args.chains.split(",")]
            agg = CrossChainAggregator(chains=chains, verbose=args.verbose)
            result = agg.run(metric=args.metric)

        elif args.command == "wallet":
            from modules.wallet_profiler import WalletProfiler
            profiler = WalletProfiler(chain=args.chain, verbose=args.verbose)
            result = profiler.run(address=args.address, full=args.full)

        if result and args.export:
            export_report(result, format=args.export, command=args.command)

    except KeyboardInterrupt:
        print("\n")
        info("Analysis interrupted by user.")
    except Exception as e:
        error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
