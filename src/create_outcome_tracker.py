"""Create a blank operational tracker for future offer and feedback results.

No customer response is fabricated: all outcome fields start as pending or blank.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "prepared" / "top_offer_recommendations.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "offer_outcome_tracker.csv"


def main() -> None:
    recommendations = pd.read_csv(INPUT)
    analysis_date = pd.Timestamp("2011-12-09")
    tracker = recommendations[[
        "customer_id", "offer_rank", "recommendation_role", "offer_id", "offer_name",
        "offer_type", "preferred_category", "offered_discount_pct", "minimum_order_value_gbp",
        "estimated_offer_cost_gbp", "estimated_order_gross_profit_after_offer_gbp", "reason_code",
    ]].copy()
    tracker.insert(0, "recommendation_id", [f"REC-{i:06d}" for i in range(1, len(tracker) + 1)])
    tracker.insert(1, "recommended_at", analysis_date.date().isoformat())
    tracker["valid_until"] = (
        analysis_date + pd.to_timedelta(recommendations.validity_days, unit="D")
    ).dt.date.astype(str)
    tracker["delivery_status"] = "not sent"
    tracker["sent_at"] = pd.NA
    tracker["customer_response"] = "pending"
    tracker["responded_at"] = pd.NA
    tracker["redeemed_at"] = pd.NA
    tracker["follow_up_order_at"] = pd.NA
    tracker["follow_up_revenue_gbp"] = pd.NA
    tracker["follow_up_estimated_gross_profit_gbp"] = pd.NA
    tracker["feedback_theme"] = pd.NA
    tracker["feedback_sentiment"] = pd.NA
    tracker["learning_signal"] = "pending outcome"
    tracker.to_csv(OUTPUT, index=False)
    print(f"Created {len(tracker):,} trackable offer records.")
    print(tracker.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
