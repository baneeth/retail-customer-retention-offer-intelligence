"""Independent checks for the completed analytical pipeline."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "outputs" / "prepared"
OUTPUT = PREP / "backend_quality_report.json"


def main() -> None:
    transactions = pd.read_csv(PREP / "transactions_clean.csv")
    orders = pd.read_csv(PREP / "orders_clean.csv")
    customers = pd.read_csv(PREP / "customer_lifecycle.csv")
    offers = pd.read_csv(PREP / "offer_catalogue.csv")
    recommendations = pd.read_csv(PREP / "eligible_offer_sets.csv")
    top = pd.read_csv(PREP / "top_offer_recommendations.csv")
    products = pd.read_csv(PREP / "product_economics.csv")
    outcomes = pd.read_csv(PREP / "simulated_offer_outcomes.csv")

    category_caps = products.loc[products.offer_eligible].groupby("retail_category").safe_discount_cap_pct.median()
    discounted = recommendations.loc[recommendations.offered_discount_pct > 0].copy()
    discounted["safe_cap"] = discounted.preferred_category.map(category_caps)

    checks = {
        "transaction_to_order_revenue_reconciles": bool(abs(transactions.revenue.sum() - orders.order_revenue.sum()) < 0.01),
        "order_to_customer_revenue_reconciles": bool(abs(orders.order_revenue.sum() - customers.lifetime_revenue.sum()) < 0.01),
        "customer_count_consistent": bool(customers.customer_id.nunique() == 4338),
        "one_primary_offer_per_customer": bool(int((recommendations.recommendation_role == "primary").sum()) == customers.customer_id.nunique()),
        "top_offer_ranks_are_one_to_three": set(top.offer_rank.unique()).issubset({1, 2, 3}),
        "no_discount_exceeds_safe_cap": bool((discounted.offered_discount_pct <= discounted.safe_cap + 1e-9).all()),
        "offer_ids_valid": set(recommendations.offer_id).issubset(set(offers.offer_id)),
        "simulated_outcomes_labelled": bool(outcomes.is_simulated.astype(bool).all()),
        "only_primary_offers_sent_in_simulation": bool((outcomes.loc[outcomes.delivery_status == "sent", "recommendation_role"] == "primary").all()),
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "controls": {
            "clean_transaction_rows": int(len(transactions)),
            "orders": int(len(orders)),
            "customers": int(customers.customer_id.nunique()),
            "catalogue_offers": int(len(offers)),
            "eligible_offer_records": int(len(recommendations)),
            "reconciled_revenue_gbp": round(float(transactions.revenue.sum()), 2),
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
