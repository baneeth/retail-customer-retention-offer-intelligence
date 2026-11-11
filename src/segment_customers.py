"""Assign transparent value and purchasing-pattern segments; no churn judgement."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROFILE_INPUT = ROOT / "outputs" / "prepared" / "customer_profiles.csv"
ORDER_INPUT = ROOT / "outputs" / "prepared" / "orders_clean.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "customer_segments.csv"

HIGH_VALUE_MIN = 3646.53  # 90th percentile of lifetime revenue
CORE_VALUE_MIN = 1353.74  # 70th percentile
DEVELOPING_VALUE_MIN = 674.48  # 50th percentile
BULK_AOV_MIN = 667.24  # 90th percentile of customer average order value
BULK_UNITS_MIN = 416.99  # 90th percentile of customer average units/order


def value_segment(revenue: float) -> str:
    if revenue >= HIGH_VALUE_MIN:
        return "high value"
    if revenue >= CORE_VALUE_MIN:
        return "core value"
    if revenue >= DEVELOPING_VALUE_MIN:
        return "developing value"
    return "lower value"


def relationship_segment(order_count: int) -> str:
    if order_count == 1:
        return "one-time buyer"
    if order_count <= 4:
        return "repeat buyer"
    return "frequent buyer"


def main() -> None:
    profiles = pd.read_csv(PROFILE_INPUT)
    orders = pd.read_csv(ORDER_INPUT)
    order_pattern = orders.groupby("customer_id", as_index=False).agg(
        average_units_per_order=("total_units", "mean"),
        average_distinct_products=("distinct_products", "mean"),
    )
    customers = profiles.merge(order_pattern, on="customer_id", how="left")
    customers["value_segment"] = customers["lifetime_revenue"].map(value_segment)
    customers["relationship_segment"] = customers["order_count"].map(relationship_segment)
    customers["buying_pattern"] = "standard purchase pattern"
    bulk = (
        (customers["average_order_value"] >= BULK_AOV_MIN)
        | (customers["average_units_per_order"] >= BULK_UNITS_MIN)
    )
    customers.loc[bulk, "buying_pattern"] = "bulk purchase pattern"
    customers["average_units_per_order"] = customers["average_units_per_order"].round(1)
    customers["average_distinct_products"] = customers["average_distinct_products"].round(1)
    customers.to_csv(OUTPUT, index=False)

    print(customers.groupby(["value_segment", "relationship_segment"]).size().to_string())
    print(f"Bulk-pattern customers: {int(bulk.sum()):,}")


if __name__ == "__main__":
    main()
