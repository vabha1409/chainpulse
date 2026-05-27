"""
utils/report_exporter.py — Export analysis results to JSON, CSV, or PDF
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from utils.display import success, warn, info

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def export_report(data, format="json", command="analysis"):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"chainpulse_{command}_{timestamp}"

    if format == "json":
        _export_json(data, filename)
    elif format == "csv":
        _export_csv(data, filename)
    elif format == "pdf":
        _export_pdf_or_html(data, filename, command)


def _export_json(data, filename):
    path = REPORTS_DIR / f"{filename}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    success(f"Report exported: {path}")


def _export_csv(data, filename):
    path = REPORTS_DIR / f"{filename}.csv"
    # Flatten top-level list if present
    rows = None
    for key in ["whales", "protocols", "wallets", "holders"]:
        if key in data and isinstance(data[key], list):
            rows = data[key]
            break

    if rows:
        with open(path, "w", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        success(f"CSV exported: {path}")
    else:
        warn("No tabular data to export to CSV. Falling back to JSON.")
        _export_json(data, filename)


def _export_pdf_or_html(data, filename, command):
    """Generate an HTML report (PDF export requires browser or wkhtmltopdf)."""
    path = REPORTS_DIR / f"{filename}.html"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    chain = data.get("chain", "multi-chain")
    cmd_title = command.replace("_", " ").title()

    rows_html = ""
    for key in ["whales", "protocols", "wallets", "holders"]:
        if key in data and isinstance(data[key], list) and data[key]:
            items = data[key]
            headers = list(items[0].keys())
            rows_html += f"<h2>{key.title()}</h2><table><thead><tr>"
            rows_html += "".join(f"<th>{h}</th>" for h in headers)
            rows_html += "</tr></thead><tbody>"
            for item in items[:50]:
                rows_html += "<tr>" + "".join(f"<td>{item.get(h, '')}</td>" for h in headers) + "</tr>"
            rows_html += "</tbody></table>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ChainPulse — {cmd_title} Report</title>
<style>
  body {{ font-family: 'Courier New', monospace; background: #0a0a0f; color: #e0e0e0; margin: 40px; }}
  h1 {{ color: #00ffd4; border-bottom: 1px solid #00ffd433; padding-bottom: 12px; }}
  h2 {{ color: #7ecdff; margin-top: 32px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
  th {{ background: #1a1a2e; color: #7ecdff; padding: 8px 12px; text-align: left; border: 1px solid #333; }}
  td {{ padding: 6px 12px; border: 1px solid #222; }}
  tr:nth-child(even) {{ background: #111; }}
  .meta {{ color: #888; font-size: 13px; margin-bottom: 24px; }}
  .badge {{ display: inline-block; background: #00ffd422; color: #00ffd4; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
</style>
</head>
<body>
  <h1>⛓ ChainPulse — {cmd_title}</h1>
  <p class="meta">
    Generated: {timestamp} &nbsp;|&nbsp;
    Chain: <span class="badge">{chain.upper()}</span> &nbsp;|&nbsp;
    Module: <span class="badge">{command}</span>
  </p>
  {rows_html if rows_html else "<p>No tabular data. Raw data follows:</p><pre>" + json.dumps(data, indent=2, default=str) + "</pre>"}
  <hr style="border-color: #333; margin-top: 48px;">
  <p style="color: #555; font-size: 12px;">ChainPulse v1.0 — For informational purposes only. Not financial advice.</p>
</body>
</html>"""

    with open(path, "w") as f:
        f.write(html)
    success(f"HTML report exported: {path}")
    info("To convert to PDF: open in browser → Print → Save as PDF")
    info("Or install: pip install weasyprint && weasyprint report.html report.pdf")
