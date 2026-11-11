"""Prepare the UCI Online Retail source for print-retail retention analysis.

Original transaction values are retained. Derived categories and margin estimates
are explicitly labelled as analytical assumptions.
"""
from pathlib import Path
import json
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work" / "online_retail" / "Online Retail.xlsx"
OUTPUT = ROOT / "outputs" / "prepared"


def category_for(description: str) -> str:
    text = (description or "").upper()
    if re.search(r"PAPER|CARD|ENVELOPE|WRAP|LABEL|TAPE|BAG", text):
        return "paper_packaging"
    if re.search(r"PEN|PENCIL|NOTEBOOK|NOTE PAD|STATIONERY|RULER|ERASER|CLIP|FILE", text):
        return "stationery"
    if re.search(r"DESK|OFFICE|CALENDAR|DIARY|MAGNET|MUG|STORAGE", text):
        return "office_supplies"
    if re.search(r"CHRISTMAS|EASTER|HALLOWEEN|VALENTINE|BIRTHDAY", text):
        return "seasonal_gifts"
    return "other_retail"


MARGIN_BY_CATEGORY = {
    "paper_packaging": 0.35,
    "stationery": 0.42,
    "office_supplies": 0.38,
    "seasonal_gifts": 0.45,
    "other_retail": 0.40,
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_excel(SOURCE)
    raw.columns = ["invoice_no", "stock_code", "description", "quantity", "invoice_at", "unit_price", "customer_id", "country"]

    audit = {
        "source_rows": len(raw),
        "date_min": str(raw.invoice_at.min()),
        "date_max": str(raw.invoice_at.max()),
        "missing_customer_id_rows": int(raw.customer_id.isna().sum()),
        "missing_description_rows": int(raw.description.isna().sum()),
        "cancelled_invoice_rows": int(raw.invoice_no.astype(str).str.startswith("C").sum()),
        "non_positive_quantity_rows": int((raw.quantity <= 0).sum()),
        "non_positive_price_rows": int((raw.unit_price <= 0).sum()),
    }

    clean = raw.loc[
        raw.customer_id.notna()
        & raw.description.notna()
        & ~raw.invoice_no.astype(str).str.startswith("C")
        & (raw.quantity > 0)
        & (raw.unit_price > 0)
    ].copy()
    clean.customer_id = clean.customer_id.astype("int64").astype(str)
    clean["revenue"] = (clean.quantity * clean.unit_price).round(2)
    clean["product_category"] = clean.description.map(category_for)
    clean["estimated_margin_pct"] = clean.product_category.map(MARGIN_BY_CATEGORY)
    clean["estimated_gross_profit"] = (clean.revenue * clean.estimated_margin_pct).round(2)
    audit["clean_rows"] = len(clean)
    audit["clean_customers"] = int(clean.customer_id.nunique())
    audit["clean_orders"] = int(clean.invoice_no.nunique())
    audit["clean_revenue"] = round(float(clean.revenue.sum()), 2)
    audit["estimated_gross_profit"] = round(float(clean.estimated_gross_profit.sum()), 2)

    clean.to_csv(OUTPUT / "transactions_clean.csv", index=False)
    (OUTPUT / "data_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
