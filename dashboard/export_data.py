from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "dashboard-data.json"

lifecycle = pd.read_csv(ROOT / "outputs" / "prepared" / "customer_lifecycle.csv")
offers = pd.read_csv(ROOT / "outputs" / "prepared" / "top_offer_recommendations.csv")
primary = offers.loc[offers.recommendation_role == "primary"].copy()
performance = pd.read_csv(ROOT / "outputs" / "prepared" / "simulated_offer_performance.csv")
simulation = json.loads((ROOT / "outputs" / "prepared" / "simulated_performance_summary.json").read_text(encoding="utf-8"))
quality = json.loads((ROOT / "outputs" / "prepared" / "backend_quality_report.json").read_text(encoding="utf-8"))
customer = lifecycle.merge(primary[["customer_id", "offer_name", "offer_type", "offered_discount_pct", "estimated_offer_cost_gbp", "estimated_order_gross_profit_after_offer_gbp"]], on="customer_id", how="left")
customer = customer.rename(columns={"offer_name": "primary_offer", "offered_discount_pct": "discount"})
customer["discount"] = customer["discount"].fillna(0)
customer["preferred_category"] = customer["preferred_category"].fillna("unknown")

record_frame = customer[[
    "customer_id", "buyer_type", "value_segment", "lifecycle_stage", "retention_priority",
    "preferred_category", "lifetime_revenue", "average_order_value", "order_count",
    "days_since_last_order", "primary_offer", "offer_type", "discount",
    "estimated_offer_cost_gbp", "estimated_order_gross_profit_after_offer_gbp"
]].sort_values(["retention_priority", "lifetime_revenue"], ascending=[True, False])
record_frame = record_frame.astype(object).where(pd.notna(record_frame), None)
records = record_frame.to_dict("records")

def counts(column):
    return lifecycle[column].value_counts().sort_index().to_dict()

payload = {
    "analysis_date": "2011-12-09",
    "summary": {
        "customers": int(len(lifecycle)),
        "revenue": round(float(lifecycle.lifetime_revenue.sum()), 2),
        "high_priority": int((lifecycle.retention_priority == "high").sum()),
        "bulk_candidates": int((lifecycle.buyer_type == "recurring bulk/wholesale candidate").sum()),
        "recommendations": int(len(offers)),
    },
    "lifecycle_counts": counts("lifecycle_stage"),
    "category_counts": counts("preferred_category"),
    "buyer_counts": counts("buyer_type"),
    "simulation": simulation,
    "quality_status": quality["status"],
    "top_simulated_offers": performance.loc[performance.sent >= 30, [
        "offer_name", "sent", "acceptance_rate", "redemption_rate",
        "simulated_net_gross_profit_gbp"
    ]].head(6).to_dict("records"),
    "records": records,
}
OUT.write_text(json.dumps(payload, default=str, allow_nan=False), encoding="utf-8")
