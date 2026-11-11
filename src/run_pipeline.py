"""Run the complete analytical pipeline in dependency order."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CORE_STAGES = [
    "audit_and_prepare.py",
    "build_orders.py",
    "build_customer_profiles.py",
    "segment_customers.py",
    "classify_buyer_type.py",
    "build_customer_preferences.py",
    "build_retail_preferences.py",
    "build_product_economics.py",
    "build_customer_lifecycle.py",
    "match_offers.py",
    "create_outcome_tracker.py",
]

SIMULATION_STAGES = [
    "simulate_offer_outcomes.py",
    "evaluate_offer_performance.py",
]


def run(script: Path) -> None:
    print(f"\n=== {script.name} ===", flush=True)
    subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Reuse outputs/prepared/transactions_clean.csv instead of reading the source workbook.",
    )
    parser.add_argument(
        "--skip-simulation",
        action="store_true",
        help="Build recommendations without illustrative campaign outcomes.",
    )
    args = parser.parse_args()

    stages = CORE_STAGES.copy()
    if args.skip_audit:
        stages.remove("audit_and_prepare.py")
    if not args.skip_simulation:
        stages.extend(SIMULATION_STAGES)
    stages.append("validate_backend.py")

    for name in stages:
        run(ROOT / "src" / name)

    if not args.skip_simulation:
        run(ROOT / "dashboard" / "export_data.py")

    report_path = ROOT / "outputs" / "prepared" / "backend_quality_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["status"] != "PASS":
        raise SystemExit("Pipeline finished, but backend validation did not pass.")
    print("\nPipeline complete. Backend quality status: PASS")


if __name__ == "__main__":
    main()
