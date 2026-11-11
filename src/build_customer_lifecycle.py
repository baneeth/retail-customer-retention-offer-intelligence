"""Create transparent lifecycle and activity signals; this is not a predictive churn model."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROFILE_INPUT = ROOT / "outputs" / "prepared" / "customer_profiles.csv"
BUYER_INPUT = ROOT / "outputs" / "prepared" / "customer_buyer_types.csv"
PREFERENCE_INPUT = ROOT / "outputs" / "prepared" / "customer_retail_preferences.csv"
OUTPUT = ROOT / "outputs" / "prepared" / "customer_lifecycle.csv"


def lifecycle(row: pd.Series) -> str:
    if row.order_count == 1:
        if row.days_since_last_order <= 30:
            return "recent first-time buyer"
        if row.days_since_last_order <= 90:
            return "unconverted one-time buyer"
        return "inactive one-time buyer"
    if row.days_since_last_order <= max(30, 1.5 * row.average_days_between_orders):
        return "active repeat buyer"
    if row.days_since_last_order <= max(60, 2.5 * row.average_days_between_orders):
        return "slowing repeat buyer"
    return "inactive repeat buyer"


def priority(row: pd.Series) -> str:
    # More valuable customers are surfaced first when their activity is deteriorating.
    if row.lifecycle_stage in {"inactive repeat buyer", "inactive one-time buyer"}:
        return "high" if row.value_segment in {"high value", "core value"} else "medium"
    if row.lifecycle_stage in {"slowing repeat buyer", "unconverted one-time buyer"}:
        return "medium" if row.value_segment in {"high value", "core value"} else "low"
    return "none"


def main() -> None:
    profiles = pd.read_csv(PROFILE_INPUT)
    buyers = pd.read_csv(BUYER_INPUT)
    preferences = pd.read_csv(PREFERENCE_INPUT)
    customers = buyers.drop(columns=[c for c in profiles.columns if c != "customer_id"], errors="ignore")
    customers = customers.merge(profiles, on="customer_id", how="left")
    customers = customers.merge(preferences, on="customer_id", how="left")

    # Value segmentation uses the documented Phase 6 revenue thresholds.
    customers["value_segment"] = "lower value"
    customers.loc[customers.lifetime_revenue >= 674.48, "value_segment"] = "developing value"
    customers.loc[customers.lifetime_revenue >= 1353.74, "value_segment"] = "core value"
    customers.loc[customers.lifetime_revenue >= 3646.53, "value_segment"] = "high value"
    customers["lifecycle_stage"] = customers.apply(lifecycle, axis=1)
    customers["days_late_vs_usual_cycle"] = (
        customers.days_since_last_order - customers.average_days_between_orders
    ).round(1)
    customers.loc[customers.order_count == 1, "days_late_vs_usual_cycle"] = pd.NA
    customers["retention_priority"] = customers.apply(priority, axis=1)
    customers.to_csv(OUTPUT, index=False)
    print(customers.lifecycle_stage.value_counts().to_string())
    print("\nRetention priority")
    print(customers.retention_priority.value_counts().to_string())


if __name__ == "__main__":
    main()
