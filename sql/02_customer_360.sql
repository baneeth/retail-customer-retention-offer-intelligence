-- Rebuild the behavioural customer 360 from clean line-item transactions.
-- :as_of_date should normally be one day after the dataset's latest invoice.

with orders as (
    select
        customer_id,
        invoice_no,
        min(invoice_at) as order_at,
        max(country) as country,
        sum(quantity) as total_units,
        sum(revenue) as order_revenue
    from analytics.transactions_clean
    group by customer_id, invoice_no
), order_gaps as (
    select
        *,
        extract(day from order_at - lag(order_at) over (
            partition by customer_id order by order_at, invoice_no
        )) as days_from_previous_order
    from orders
), customer_metrics as (
    select
        customer_id,
        max(country) as country,
        min(order_at) as first_order_at,
        max(order_at) as last_order_at,
        count(*) as order_count,
        sum(order_revenue) as lifetime_revenue,
        avg(order_revenue) as average_order_value,
        avg(total_units) as average_units_per_order,
        avg(days_from_previous_order) as average_days_between_orders,
        (:as_of_date::date - max(order_at)::date) as days_since_last_order
    from order_gaps
    group by customer_id
), preferred_category as (
    select customer_id, product_category,
           row_number() over (
               partition by customer_id
               order by sum(revenue) desc, product_category
           ) as category_rank
    from analytics.transactions_clean
    where product_category <> 'service_or_adjustment'
    group by customer_id, product_category
), enriched as (
    select m.*, p.product_category as preferred_category,
           case
               when m.average_order_value >= 667.24 or m.average_units_per_order >= 416.99
                   then true else false
           end as bulk_signal
    from customer_metrics m
    left join preferred_category p
      on m.customer_id = p.customer_id and p.category_rank = 1
)
select
    e.*,
    case
        when bulk_signal and order_count >= 3 then 'recurring bulk/wholesale candidate'
        when bulk_signal then 'large-order candidate'
        else 'regular retail customer'
    end as buyer_type,
    case
        when lifetime_revenue >= 3646.53 then 'high value'
        when lifetime_revenue >= 1353.74 then 'core value'
        when lifetime_revenue >= 674.48 then 'developing value'
        else 'lower value'
    end as value_segment,
    case
        when order_count = 1 and days_since_last_order <= 30 then 'recent first-time buyer'
        when order_count = 1 and days_since_last_order <= 90 then 'unconverted one-time buyer'
        when order_count = 1 then 'inactive one-time buyer'
        when days_since_last_order <= greatest(30, 1.5 * coalesce(average_days_between_orders, 0))
            then 'active repeat buyer'
        when days_since_last_order <= greatest(60, 2.5 * coalesce(average_days_between_orders, 0))
            then 'slowing repeat buyer'
        else 'inactive repeat buyer'
    end as lifecycle_stage
from enriched e;
