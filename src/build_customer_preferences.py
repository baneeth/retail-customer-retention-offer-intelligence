"""Create customer category and product preferences from clean transaction lines."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "prepared" / "transactions_clean.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "customer_preferences.csv"


def main() -> None:
    transactions = pd.read_csv(INPUT)

    category_revenue = (
        transactions.groupby(["customer_id", "product_category"], as_index=False)["revenue"]
        .sum()
        .rename(columns={"revenue": "category_revenue"})
    )
    category_revenue["customer_revenue"] = category_revenue.groupby("customer_id")["category_revenue"].transform("sum")
    category_revenue["category_revenue_share"] = category_revenue["category_revenue"] / category_revenue["customer_revenue"]
    preferred_category = (
        category_revenue.sort_values(["customer_id", "category_revenue"], ascending=[True, False])
        .drop_duplicates("customer_id")
        [["customer_id", "product_category", "category_revenue", "category_revenue_share"]]
        .rename(columns={
            "product_category": "preferred_category",
            "category_revenue": "preferred_category_revenue",
            "category_revenue_share": "preferred_category_revenue_share",
        })
    )

    product_revenue = (
        transactions.groupby(["customer_id", "description"], as_index=False)["revenue"]
        .sum()
        .rename(columns={"revenue": "product_revenue"})
    )
    preferred_product = (
        product_revenue.sort_values(["customer_id", "product_revenue", "description"], ascending=[True, False, True])
        .drop_duplicates("customer_id")
        [["customer_id", "description", "product_revenue"]]
        .rename(columns={"description": "preferred_product", "product_revenue": "preferred_product_revenue"})
    )

    preferences = preferred_category.merge(preferred_product, on="customer_id", how="left")
    preferences["preferred_category_revenue"] = preferences["preferred_category_revenue"].round(2)
    preferences["preferred_category_revenue_share"] = preferences["preferred_category_revenue_share"].round(3)
    preferences["preferred_product_revenue"] = preferences["preferred_product_revenue"].round(2)
    preferences.to_csv(OUTPUT, index=False)

    print(preferences.preferred_category.value_counts().to_string())
    print(preferences.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
