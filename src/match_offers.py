"""Match predefined offers to customer behaviour and category-level profit safeguards."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER_INPUT = ROOT / "outputs" / "prepared" / "customer_lifecycle.csv"
OFFER_INPUT = ROOT / "outputs" / "prepared" / "offer_catalogue.csv"
PRODUCT_INPUT = ROOT / "outputs" / "prepared" / "product_economics.csv"
ALL_OUTPUT = ROOT / "outputs" / "prepared" / "eligible_offer_sets.csv"
TOP_OUTPUT = ROOT / "outputs" / "prepared" / "top_offer_recommendations.csv"


def eligible(value: str, rule: str) -> bool:
    return rule == "all" or value in rule.split("|")


def category_matches(preferred_category: str, rule: str) -> bool:
    if pd.isna(preferred_category):
        return rule == "all merchandise"
    if rule in {"all merchandise", "preferred category"}:
        return True
    return preferred_category == rule


def main() -> None:
    customers = pd.read_csv(CUSTOMER_INPUT)
    offers = pd.read_csv(OFFER_INPUT)
    products = pd.read_csv(PRODUCT_INPUT)
    category_rules = (
        products.loc[products.offer_eligible]
        .groupby("retail_category", as_index=False)
        .agg(
            preferred_category_margin_pct=("estimated_margin_pct", "median"),
            preferred_category_safe_discount_cap_pct=("safe_discount_cap_pct", "median"),
        )
    )
    customers = customers.merge(
        category_rules,
        left_on="preferred_category",
        right_on="retail_category",
        how="left",
    )

    matched = []
    for customer in customers.itertuples(index=False):
        for offer in offers.itertuples(index=False):
            if not eligible(customer.buyer_type, offer.customer_track):
                continue
            if not eligible(customer.lifecycle_stage, offer.lifecycle_eligibility):
                continue
            if not eligible(customer.value_segment, offer.value_eligibility):
                continue
            if not category_matches(customer.preferred_category, offer.category_eligibility):
                continue

            requested_discount = float(offer.requested_discount_pct)
            actual_discount = requested_discount
            cap_applied = False
            if offer.requires_safe_discount_cap == "yes":
                if pd.isna(customer.preferred_category_safe_discount_cap_pct):
                    continue
                actual_discount = min(requested_discount, customer.preferred_category_safe_discount_cap_pct)
                cap_applied = actual_discount < requested_discount
                if actual_discount <= 0:
                    continue

            discount_cost = (
                customer.average_order_value
                * customer.preferred_category_revenue_share
                * actual_discount
            )
            estimated_offer_cost = discount_cost + float(offer.offer_cost_fixed_gbp)
            estimated_order_gross_profit_after_offer = (
                customer.average_order_value * customer.preferred_category_margin_pct
                - estimated_offer_cost
                if not pd.isna(customer.preferred_category_margin_pct)
                else pd.NA
            )
            preferred_category = customer.preferred_category if not pd.isna(customer.preferred_category) else "unknown"
            reason = (
                f"{customer.lifecycle_stage}; {customer.value_segment}; "
                f"{customer.buyer_type}; preferred category: {preferred_category}"
            )
            matched.append({
                "customer_id": customer.customer_id,
                "buyer_type": customer.buyer_type,
                "value_segment": customer.value_segment,
                "lifecycle_stage": customer.lifecycle_stage,
                "retention_priority": customer.retention_priority,
                "preferred_category": preferred_category,
                "offer_id": offer.offer_id,
                "offer_name": offer.offer_name,
                "offer_type": offer.offer_type,
                "offer_priority": offer.priority,
                "validity_days": offer.validity_days,
                "minimum_order_value_gbp": offer.min_order_value_gbp,
                "requested_discount_pct": requested_discount,
                "offered_discount_pct": round(actual_discount, 3),
                "discount_capped": cap_applied,
                "estimated_offer_cost_gbp": round(estimated_offer_cost, 2),
                "estimated_order_gross_profit_after_offer_gbp": (
                    round(estimated_order_gross_profit_after_offer, 2)
                    if not pd.isna(estimated_order_gross_profit_after_offer)
                    else pd.NA
                ),
                "reason_code": reason,
            })

    recommendations = pd.DataFrame(matched)
    recommendations = recommendations.sort_values(
        ["customer_id", "offer_priority", "estimated_order_gross_profit_after_offer_gbp"],
        ascending=[True, False, False],
    )
    recommendations["offer_rank"] = recommendations.groupby("customer_id").cumcount() + 1
    recommendations["recommendation_role"] = "alternative"
    recommendations.loc[recommendations.offer_rank == 1, "recommendation_role"] = "primary"
    recommendations.to_csv(ALL_OUTPUT, index=False)
    recommendations.loc[recommendations.offer_rank <= 3].to_csv(TOP_OUTPUT, index=False)
    print(f"Customers with at least one eligible offer: {recommendations.customer_id.nunique():,}")
    print(f"Eligible offer recommendations: {len(recommendations):,}")
    print(f"Discounts reduced to safe cap: {int(recommendations.discount_capped.sum()):,}")
    print(recommendations.loc[recommendations.offer_rank <= 3].head(9).to_string(index=False))


if __name__ == "__main__":
    main()
