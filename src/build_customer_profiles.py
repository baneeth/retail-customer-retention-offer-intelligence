"""Create factual customer profiles from completed orders, without churn labels."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "prepared" / "orders_clean.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "customer_profiles.csv"


def main() -> None:
    orders = pd.read_csv(INPUT, parse_dates=["order_at"])
    analysis_date = orders["order_at"].max().normalize()
    orders = orders.sort_values(["customer_id", "order_at", "invoice_no"])
    orders["days_since_previous_order"] = (
        orders.groupby("customer_id")["order_at"].diff().dt.total_seconds() / 86400
    )

    profiles = (
        orders.groupby("customer_id", as_index=False)
        .agg(
            country=("country", "first"),
            first_order_at=("order_at", "min"),
            last_order_at=("order_at", "max"),
            order_count=("invoice_no", "nunique"),
            lifetime_revenue=("order_revenue", "sum"),
            average_order_value=("order_revenue", "mean"),
            total_units=("total_units", "sum"),
            average_days_between_orders=("days_since_previous_order", "mean"),
        )
    )
    profiles["days_since_last_order"] = (analysis_date - profiles["last_order_at"].dt.normalize()).dt.days
    profiles["customer_age_days"] = (analysis_date - profiles["first_order_at"].dt.normalize()).dt.days
    profiles["lifetime_revenue"] = profiles["lifetime_revenue"].round(2)
    profiles["average_order_value"] = profiles["average_order_value"].round(2)
    profiles["average_days_between_orders"] = profiles["average_days_between_orders"].round(1)
    profiles = profiles.sort_values("lifetime_revenue", ascending=False)
    profiles.to_csv(OUTPUT, index=False)

    print(f"Analysis date: {analysis_date.date()}")
    print(f"Created {len(profiles):,} customer profiles.")
    print(profiles.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
