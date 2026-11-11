"""Evaluate the clearly labelled simulated campaign results.

This analysis demonstrates how a production learning loop would work. It must not
be represented as actual campaign performance.
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SIM_INPUT = ROOT / "outputs" / "prepared" / "simulated_offer_outcomes.csv"
REC_INPUT = ROOT / "outputs" / "prepared" / "top_offer_recommendations.csv"
CUSTOMER_INPUT = ROOT / "outputs" / "prepared" / "customer_lifecycle.csv"
MARGIN_INPUT = ROOT / "outputs" / "prepared" / "margin_assumptions.csv"
OFFER_OUTPUT = ROOT / "outputs" / "prepared" / "simulated_offer_performance.csv"
SEGMENT_OUTPUT = ROOT / "outputs" / "prepared" / "simulated_segment_performance.csv"
RULE_OUTPUT = ROOT / "outputs" / "prepared" / "simulated_learning_rules.csv"
SUMMARY_OUTPUT = ROOT / "outputs" / "prepared" / "simulated_performance_summary.json"


def summarize(group: pd.DataFrame) -> pd.Series:
    sent = int((group.delivery_status == "sent").sum())
    accepted = int((group.customer_response == "accepted").sum())
    redeemed = int(group.redeemed.sum())
    revenue = float(group.follow_up_revenue_gbp.fillna(0).sum())
    gross_profit = float(group.simulated_net_gross_profit_gbp.fillna(0).sum())
    return pd.Series({
        "sent": sent,
        "accepted": accepted,
        "redeemed": redeemed,
        "acceptance_rate": accepted / sent if sent else 0,
        "redemption_rate": redeemed / sent if sent else 0,
        "redemption_rate_after_acceptance": redeemed / accepted if accepted else 0,
        "positive_feedback": int((group.feedback_sentiment == "positive").sum()),
        "negative_feedback": int((group.feedback_sentiment == "negative").sum()),
        "simulated_follow_up_revenue_gbp": revenue,
        "simulated_net_gross_profit_gbp": gross_profit,
    })


def main() -> None:
    outcomes = pd.read_csv(SIM_INPUT)
    recommendations = pd.read_csv(REC_INPUT)
    customers = pd.read_csv(CUSTOMER_INPUT)[[
        "customer_id", "buyer_type", "value_segment", "lifecycle_stage",
        "retention_priority", "preferred_category"
    ]]
    margins = pd.read_csv(MARGIN_INPUT)[["retail_category", "estimated_margin_pct"]]

    if not outcomes.is_simulated.astype(bool).all():
        raise ValueError("Every outcome row must be explicitly labelled as simulated")

    recommendation_fields = recommendations[[
        "customer_id", "offer_id", "recommendation_role", "offer_type",
        "estimated_offer_cost_gbp"
    ]].drop_duplicates(["customer_id", "offer_id", "recommendation_role"])
    data = outcomes.merge(
        recommendation_fields,
        on=["customer_id", "offer_id", "recommendation_role"],
        how="left",
        validate="one_to_one",
    ).merge(customers, on="customer_id", how="left", validate="many_to_one")
    data = data.merge(
        margins,
        left_on="preferred_category",
        right_on="retail_category",
        how="left",
        validate="many_to_one",
    )
    data["simulated_net_gross_profit_gbp"] = data.follow_up_revenue_gbp.fillna(0) * data.estimated_margin_pct
    data.loc[data.redeemed, "simulated_net_gross_profit_gbp"] -= data.loc[data.redeemed, "estimated_offer_cost_gbp"].fillna(0)

    sent = data.loc[data.delivery_status == "sent"].copy()
    offer_performance = sent.groupby(["offer_id", "offer_name", "offer_type"], dropna=False).apply(summarize, include_groups=False).reset_index()
    segment_performance = sent.groupby(["buyer_type", "lifecycle_stage"], dropna=False).apply(summarize, include_groups=False).reset_index()

    overall = summarize(sent)
    overall_redemption = float(overall.redemption_rate)
    rules = offer_performance.copy()
    rules["learning_action"] = "maintain and test"
    rules.loc[(rules.sent >= 30) & (rules.redemption_rate >= overall_redemption + 0.05) & (rules.simulated_net_gross_profit_gbp > 0), "learning_action"] = "prioritise for controlled test"
    rules.loc[(rules.sent >= 30) & (rules.redemption_rate <= overall_redemption - 0.05), "learning_action"] = "review targeting or replace"
    rules.loc[rules.sent < 30, "learning_action"] = "insufficient sample"
    rules["evidence_status"] = "simulated - requires live validation"

    rate_cols = ["acceptance_rate", "redemption_rate", "redemption_rate_after_acceptance"]
    money_cols = ["simulated_follow_up_revenue_gbp", "simulated_net_gross_profit_gbp"]
    for frame in (offer_performance, segment_performance, rules):
        frame[rate_cols] = frame[rate_cols].round(4)
        frame[money_cols] = frame[money_cols].round(2)

    offer_performance.sort_values(["redemption_rate", "simulated_net_gross_profit_gbp"], ascending=False).to_csv(OFFER_OUTPUT, index=False)
    segment_performance.sort_values(["redemption_rate", "simulated_net_gross_profit_gbp"], ascending=False).to_csv(SEGMENT_OUTPUT, index=False)
    rules[[
        "offer_id", "offer_name", "sent", "acceptance_rate", "redemption_rate",
        "simulated_net_gross_profit_gbp", "learning_action", "evidence_status"
    ]].sort_values(["learning_action", "redemption_rate"], ascending=[True, False]).to_csv(RULE_OUTPUT, index=False)

    summary = {
        "is_simulated": True,
        "sent": int(overall.sent),
        "accepted": int(overall.accepted),
        "redeemed": int(overall.redeemed),
        "acceptance_rate": round(float(overall.acceptance_rate), 4),
        "redemption_rate": round(float(overall.redemption_rate), 4),
        "positive_feedback": int(overall.positive_feedback),
        "negative_feedback": int(overall.negative_feedback),
        "simulated_follow_up_revenue_gbp": round(float(overall.simulated_follow_up_revenue_gbp), 2),
        "simulated_net_gross_profit_gbp": round(float(overall.simulated_net_gross_profit_gbp), 2),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
