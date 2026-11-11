"""Classify regular and bulk buyer behaviour without claiming legal company status."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROFILE_INPUT = ROOT / "outputs" / "prepared" / "customer_profiles.csv"
ORDER_INPUT = ROOT / "outputs" / "prepared" / "orders_clean.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "customer_buyer_types.csv"

# Actual 90th-percentile values from this dataset, calculated in Phase 6.
BULK_AOV_MIN = 667.24
BULK_UNITS_MIN = 416.99


def main() -> None:
    profiles = pd.read_csv(PROFILE_INPUT)
    orders = pd.read_csv(ORDER_INPUT)
    patterns = orders.groupby("customer_id", as_index=False).agg(
        average_units_per_order=("total_units", "mean"),
        maximum_order_units=("total_units", "max"),
        maximum_order_value=("order_revenue", "max"),
    )
    customers = profiles.merge(patterns, on="customer_id", how="left")
    bulk_signal = (
        (customers.average_order_value >= BULK_AOV_MIN)
        | (customers.average_units_per_order >= BULK_UNITS_MIN)
    )
    customers["buyer_type"] = "regular retail customer"
    customers.loc[bulk_signal & (customers.order_count <= 2), "buyer_type"] = "large-order candidate"
    customers.loc[bulk_signal & (customers.order_count >= 3), "buyer_type"] = "recurring bulk/wholesale candidate"
    customers["buyer_type_reason"] = "Order value and unit volume below bulk threshold"
    customers.loc[bulk_signal, "buyer_type_reason"] = (
        "Average order value or average order units is in the top 10% of customers"
    )
    customers[["average_units_per_order", "maximum_order_value"]] = customers[
        ["average_units_per_order", "maximum_order_value"]
    ].round(2)
    customers.to_csv(OUTPUT, index=False)
    print(customers.buyer_type.value_counts().to_string())


if __name__ == "__main__":
    main()
