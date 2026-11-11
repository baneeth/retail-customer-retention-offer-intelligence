"""Create demonstrative offer outcomes without altering real-source or operational-tracker data.

Every row in the output has is_simulated=True. The model is deterministic so results
are reproducible, and should be replaced by actual campaign events in production.
"""
from pathlib import Path
import random
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECOMMENDATION_INPUT = ROOT / "outputs" / "prepared" / "top_offer_recommendations.csv"
LIFECYCLE_INPUT = ROOT / "outputs" / "prepared" / "customer_lifecycle.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "simulated_offer_outcomes.csv"

RNG = random.Random(20260920)


def acceptance_probability(row: pd.Series) -> float:
    by_stage = {
        "recent first-time buyer": 0.25,
        "unconverted one-time buyer": 0.31,
        "inactive one-time buyer": 0.20,
        "active repeat buyer": 0.30,
        "slowing repeat buyer": 0.39,
        "inactive repeat buyer": 0.44,
    }
    probability = by_stage[row.lifecycle_stage]
    if row.value_segment in {"high value", "core value"}:
        probability += 0.06
    if row.buyer_type == "recurring bulk/wholesale candidate":
        probability += 0.08
    if row.offer_type in {"service_benefit", "account_benefit", "payment_benefit", "delivery_service"}:
        probability += 0.04
    return min(probability, 0.70)


def feedback_for(accepted: bool) -> tuple[object, object]:
    if not accepted or RNG.random() > 0.32:
        return pd.NA, pd.NA
    pick = RNG.random()
    if pick < 0.72:
        return "positive_experience", "positive"
    if pick < 0.80:
        return "delivery_delay", "negative"
    if pick < 0.88:
        return "quality_issue", "negative"
    if pick < 0.94:
        return "price_value_concern", "negative"
    return "product_unavailable", "negative"


def main() -> None:
    recommendations = pd.read_csv(RECOMMENDATION_INPUT)
    customer_aov = pd.read_csv(LIFECYCLE_INPUT)[["customer_id", "average_order_value"]]
    rows = recommendations.merge(customer_aov, on="customer_id", how="left")
    primary = rows.recommendation_role.eq("primary")
    results = []
    start = pd.Timestamp("2011-12-10")

    for i, row in rows.iterrows():
        sent = bool(primary.iloc[i])
        accepted = sent and RNG.random() < acceptance_probability(row)
        redeemed = accepted and RNG.random() < (0.78 if row.offered_discount_pct > 0 else 0.57)
        sent_at = start + pd.Timedelta(days=RNG.randint(0, 20)) if sent else pd.NaT
        responded_at = sent_at + pd.Timedelta(days=RNG.randint(1, 12)) if accepted else pd.NaT
        redeemed_at = responded_at + pd.Timedelta(days=RNG.randint(0, 7)) if redeemed else pd.NaT
        follow_up_revenue = round(row.average_order_value * RNG.uniform(0.85, 1.35), 2) if redeemed else pd.NA
        feedback_theme, feedback_sentiment = feedback_for(accepted)
        results.append({
            "recommendation_id": f"SIM-REC-{i + 1:06d}",
            "customer_id": row.customer_id,
            "offer_id": row.offer_id,
            "offer_name": row.offer_name,
            "recommendation_role": row.recommendation_role,
            "is_simulated": True,
            "delivery_status": "sent" if sent else "not sent",
            "customer_response": "accepted" if accepted else ("ignored" if sent else "not sent"),
            "redeemed": redeemed,
            "sent_at": sent_at,
            "responded_at": responded_at,
            "redeemed_at": redeemed_at,
            "follow_up_revenue_gbp": follow_up_revenue,
            "feedback_theme": feedback_theme,
            "feedback_sentiment": feedback_sentiment,
            "learning_signal": "repeat purchase after redemption" if redeemed else ("offer accepted but not redeemed" if accepted else "no observed response"),
        })
    pd.DataFrame(results).to_csv(OUTPUT, index=False)
    simulated = pd.DataFrame(results)
    print(f"Sent primary offers: {int((simulated.delivery_status == 'sent').sum()):,}")
    print(f"Accepted offers: {int((simulated.customer_response == 'accepted').sum()):,}")
    print(f"Redeemed offers: {int(simulated.redeemed.sum()):,}")
    print(f"Feedback events: {int(simulated.feedback_theme.notna().sum()):,}")


if __name__ == "__main__":
    main()
