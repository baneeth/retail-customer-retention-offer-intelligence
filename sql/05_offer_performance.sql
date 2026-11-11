-- Campaign reporting. Never mix simulated rows with live campaign reporting.

select
    r.offer_id,
    max(c.offer_name) as offer_name,
    count(*) filter (where o.delivery_status = 'sent') as sent,
    count(*) filter (where o.customer_response = 'accepted') as accepted,
    count(*) filter (where o.redeemed) as redeemed,
    round(
        count(*) filter (where o.customer_response = 'accepted')::numeric
        / nullif(count(*) filter (where o.delivery_status = 'sent'), 0), 4
    ) as acceptance_rate,
    round(
        count(*) filter (where o.redeemed)::numeric
        / nullif(count(*) filter (where o.delivery_status = 'sent'), 0), 4
    ) as redemption_rate,
    round(sum(coalesce(o.follow_up_revenue_gbp, 0)), 2) as follow_up_revenue_gbp
from analytics.offer_recommendations r
join analytics.offer_catalogue c using (offer_id)
join analytics.offer_outcomes o
  on o.customer_id = r.customer_id and o.offer_id = r.offer_id
where r.recommendation_role = 'primary'
  and o.is_simulated = :is_simulated
group by r.offer_id
order by redemption_rate desc, follow_up_revenue_gbp desc;
