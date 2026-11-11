"""Estimate SKU-level commercial rules from real prices plus editable margin assumptions."""
from pathlib import Path
import pandas as pd
from build_retail_preferences import retail_category

ROOT = Path(__file__).resolve().parents[1]
TRANSACTION_INPUT = ROOT / "outputs" / "prepared" / "transactions_clean.csv"
ASSUMPTION_INPUT = ROOT / "outputs" / "prepared" / "margin_assumptions.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "product_economics.csv"


def margin_tier(margin: float) -> str:
    if margin >= 0.45:
        return "high margin"
    if margin >= 0.40:
        return "medium margin"
    if margin > 0:
        return "low margin"
    return "not eligible"


def main() -> None:
    transactions = pd.read_csv(TRANSACTION_INPUT)
    assumptions = pd.read_csv(ASSUMPTION_INPUT)
    transactions["retail_category"] = transactions.description.map(retail_category)
    products = (
        transactions.groupby(["stock_code", "description", "retail_category"], as_index=False)
        .agg(
            typical_unit_price=("unit_price", "median"),
            total_units_sold=("quantity", "sum"),
            historical_revenue=("revenue", "sum"),
        )
    )
    products = products.merge(assumptions, on="retail_category", how="left", validate="many_to_one")
    products["estimated_unit_cost"] = products.typical_unit_price * (1 - products.estimated_margin_pct)
    products["estimated_historical_gross_profit"] = products.historical_revenue * products.estimated_margin_pct
    # A discount is safe only if estimated profit after discount remains at or above the required floor.
    products["margin_based_discount_cap_pct"] = (
        products.estimated_margin_pct - products.min_retained_gp_pct_of_list_price
    ).clip(lower=0)
    products["safe_discount_cap_pct"] = products[[
        "margin_based_discount_cap_pct", "policy_discount_cap_pct"
    ]].min(axis=1)
    products["margin_tier"] = products.estimated_margin_pct.map(margin_tier)
    products["offer_eligible"] = products.retail_category.ne("service_or_adjustment")
    products[[
        "typical_unit_price", "historical_revenue", "estimated_unit_cost",
        "estimated_historical_gross_profit", "margin_based_discount_cap_pct", "safe_discount_cap_pct"
    ]] = products[[
        "typical_unit_price", "historical_revenue", "estimated_unit_cost",
        "estimated_historical_gross_profit", "margin_based_discount_cap_pct", "safe_discount_cap_pct"
    ]].round(2)
    products.to_csv(OUTPUT, index=False)
    print(products.groupby(["retail_category", "margin_tier"]).size().to_string())
    print(f"Offer-eligible products: {int(products.offer_eligible.sum()):,}")


if __name__ == "__main__":
    main()
