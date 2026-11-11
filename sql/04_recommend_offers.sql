-- Rank eligible predefined offers, then retain the top three per customer.

with eligible as (
    select
        c.customer_id,
        c.buyer_type,
        c.value_segment,
        c.lifecycle_stage,
        c.retention_priority,
        c.preferred_category,
        c.average_order_value,
        o.*
    from analytics.customer_360 c
    join analytics.offer_catalogue o
      on (o.customer_track = 'all' or o.customer_track = c.buyer_type)
     and (
         o.lifecycle_eligibility = 'all'
         or c.lifecycle_stage = any(regexp_split_to_array(o.lifecycle_eligibility, '\\|'))
     )
     and (
         o.value_eligibility = 'all'
         or c.value_segment = any(regexp_split_to_array(o.value_eligibility, '\\|'))
     )
     and (
         o.category_eligibility = 'all merchandise'
         or o.category_eligibility = 'preferred category' and c.preferred_category is not null
         or o.category_eligibility = c.preferred_category
     )
    where c.average_order_value >= o.min_order_value_gbp
), scored as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by priority desc,
                     case retention_priority
                         when 'high' then 4 when 'medium' then 3
                         when 'low' then 2 else 1 end desc,
                     offer_cost_fixed_gbp asc,
                     offer_id
        ) as offer_rank
    from eligible
)
select
    customer_id,
    offer_id,
    offer_name,
    buyer_type,
    value_segment,
    lifecycle_stage,
    retention_priority,
    preferred_category,
    requested_discount_pct,
    offer_cost_fixed_gbp,
    offer_rank,
    case when offer_rank = 1 then 'primary' else 'alternative' end as recommendation_role,
    concat(
        upper(replace(retention_priority, ' ', '_')), ':',
        upper(replace(lifecycle_stage, ' ', '_')), ':',
        upper(replace(offer_type, ' ', '_'))
    ) as reason_code
from scored
where offer_rank <= 3
order by customer_id, offer_rank;
