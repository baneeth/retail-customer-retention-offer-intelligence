"""Create one analytical record per completed customer order."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "prepared" / "transactions_clean.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "orders_clean.csv"


def main() -> None:
    transactions = pd.read_csv(INPUT, parse_dates=["invoice_at"])
    orders = (
        transactions.groupby(["invoice_no", "customer_id"], as_index=False)
        .agg(
            order_at=("invoice_at", "min"),
            country=("country", "first"),
            order_revenue=("revenue", "sum"),
            estimated_order_gross_profit=("estimated_gross_profit", "sum"),
            item_lines=("stock_code", "size"),
            distinct_products=("stock_code", "nunique"),
            total_units=("quantity", "sum"),
        )
        .sort_values(["customer_id", "order_at", "invoice_no"])
    )
    orders["order_revenue"] = orders["order_revenue"].round(2)
    orders["estimated_order_gross_profit"] = orders["estimated_order_gross_profit"].round(2)
    orders.to_csv(OUTPUT, index=False)
    print(f"Created {len(orders):,} orders for {orders.customer_id.nunique():,} customers.")
    print(orders.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
