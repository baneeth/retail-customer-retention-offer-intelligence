-- Load the governed 27-offer catalogue produced with this project.
-- psql example, run from the project root:
-- \copy analytics.offer_catalogue from 'outputs/prepared/offer_catalogue.csv' csv header
--
-- The CSV is the source of truth so Python and SQL use exactly the same offer IDs,
-- lifecycle rules, costs, discount requests, validity periods, and reason text.

truncate table analytics.offer_catalogue;

-- If the SQL client cannot use \copy, import these columns in this exact order:
-- offer_id, offer_name, customer_track, lifecycle_eligibility,
-- value_eligibility, category_eligibility, offer_type,
-- requested_discount_pct, offer_cost_fixed_gbp, min_order_value_gbp,
-- validity_days, priority, requires_safe_discount_cap, business_reason.

-- Post-load controls:
select count(*) as catalogue_offer_count
from analytics.offer_catalogue;

select customer_track, count(*) as offers
from analytics.offer_catalogue
group by customer_track
order by customer_track;
