"""Build product preferences for the actual gift, homeware, and stationery catalogue."""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "prepared" / "transactions_clean.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "customer_retail_preferences.csv"


def retail_category(description: str) -> str:
    text = (description or "").upper()
    if re.search(r"POSTAGE|CARRIAGE|MANUAL|BANK CHARGES|DOTCOM", text):
        return "service_or_adjustment"
    if re.search(r"CHRISTMAS|EASTER|VALENTINE|HALLOWEEN|BUNTING|PARTY", text):
        return "seasonal_event"
    if re.search(r"PAPER|CARD|ENVELOPE|NOTE|PEN|PENCIL|CALENDAR|DIARY|RULER|ERASER", text):
        return "paper_stationery"
    if re.search(r"BAG|WRAP|RIBBON|TAG|TISSUE|KEYRING|PURSE", text):
        return "gift_accessories"
    if re.search(r"MUG|TEA|CAKE|BOWL|PLATE|CUP|JAR|BOTTLE|TRAY|TIN|LUNCH|PICNIC|JAM", text):
        return "kitchen_dining"
    if re.search(r"CANDLE|LANTERN|LIGHT|T-LIGHT|ORNAMENT|FRAME|CLOCK|DOORMAT|WALL|BIRD|HEART", text):
        return "home_decor_lighting"
    if re.search(r"STORAGE|BASKET|HOOK|HANGER|DRAWER|CABINET", text):
        return "storage_organisation"
    return "gifts_novelty"


def main() -> None:
    transactions = pd.read_csv(INPUT)
    transactions["retail_category"] = transactions["description"].map(retail_category)
    merchandise = transactions.loc[transactions.retail_category != "service_or_adjustment"].copy()

    category_revenue = (
        merchandise.groupby(["customer_id", "retail_category"], as_index=False)["revenue"].sum()
        .rename(columns={"revenue": "category_revenue"})
    )
    category_revenue["customer_merchandise_revenue"] = category_revenue.groupby("customer_id")["category_revenue"].transform("sum")
    category_revenue["category_revenue_share"] = category_revenue.category_revenue / category_revenue.customer_merchandise_revenue
    preferred_category = (
        category_revenue.sort_values(["customer_id", "category_revenue", "retail_category"], ascending=[True, False, True])
        .drop_duplicates("customer_id")
        [["customer_id", "retail_category", "category_revenue", "category_revenue_share"]]
        .rename(columns={
            "retail_category": "preferred_category",
            "category_revenue": "preferred_category_revenue",
            "category_revenue_share": "preferred_category_revenue_share",
        })
    )
    product_revenue = (
        merchandise.groupby(["customer_id", "description"], as_index=False)["revenue"].sum()
        .rename(columns={"revenue": "product_revenue"})
    )
    preferred_product = (
        product_revenue.sort_values(["customer_id", "product_revenue", "description"], ascending=[True, False, True])
        .drop_duplicates("customer_id")
        .rename(columns={"description": "preferred_product", "product_revenue": "preferred_product_revenue"})
        [["customer_id", "preferred_product", "preferred_product_revenue"]]
    )
    preferences = preferred_category.merge(preferred_product, on="customer_id", how="left")
    preferences["preferred_category_revenue"] = preferences.preferred_category_revenue.round(2)
    preferences["preferred_category_revenue_share"] = preferences.preferred_category_revenue_share.round(3)
    preferences["preferred_product_revenue"] = preferences.preferred_product_revenue.round(2)
    preferences.to_csv(OUTPUT, index=False)
    print(preferences.preferred_category.value_counts().to_string())


if __name__ == "__main__":
    main()
