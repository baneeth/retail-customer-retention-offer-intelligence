-- Data contracts expected to return zero failing rows.

select customer_id, count(*) as primary_offers
from analytics.offer_recommendations
where recommendation_role = 'primary'
group by customer_id
having count(*) <> 1;

select r.customer_id, r.offer_id
from analytics.offer_recommendations r
left join analytics.offer_catalogue c using (offer_id)
where c.offer_id is null;

select recommendation_id
from analytics.offer_outcomes
where is_simulated is null;

select customer_id, min(offer_rank), max(offer_rank), count(*)
from analytics.offer_recommendations
group by customer_id
having min(offer_rank) <> 1 or max(offer_rank) > 3 or count(*) > 3;
