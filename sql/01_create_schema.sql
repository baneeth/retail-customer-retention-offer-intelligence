-- Retail Customer Retention and Offer Intelligence
-- PostgreSQL-compatible analytical schema aligned with the Python outputs.

create schema if not exists analytics;

create table if not exists analytics.transactions_clean (
    invoice_no varchar(20) not null,
    stock_code varchar(30) not null,
    description varchar(255),
    quantity integer not null,
    invoice_at timestamp not null,
    unit_price numeric(12,2) not null,
    customer_id varchar(20) not null,
    country varchar(100),
    revenue numeric(14,2) not null,
    product_category varchar(50),
    estimated_margin_pct numeric(6,4),
    estimated_gross_profit numeric(14,2)
);

create table if not exists analytics.customer_360 (
    customer_id varchar(20) primary key,
    buyer_type varchar(60) not null,
    country varchar(100),
    first_order_at timestamp,
    last_order_at timestamp,
    order_count integer not null,
    lifetime_revenue numeric(14,2) not null,
    average_order_value numeric(14,2) not null,
    average_units_per_order numeric(14,2),
    average_days_between_orders numeric(14,2),
    days_since_last_order integer not null,
    preferred_category varchar(50),
    preferred_product varchar(255),
    value_segment varchar(30) not null,
    lifecycle_stage varchar(50) not null,
    retention_priority varchar(10) not null
);

create table if not exists analytics.offer_catalogue (
    offer_id varchar(40) primary key,
    offer_name varchar(140) not null,
    customer_track varchar(60) not null,
    lifecycle_eligibility text not null,
    value_eligibility text not null,
    category_eligibility varchar(60) not null,
    offer_type varchar(50) not null,
    requested_discount_pct numeric(6,4) not null default 0,
    offer_cost_fixed_gbp numeric(12,2) not null default 0,
    min_order_value_gbp numeric(12,2) not null default 0,
    validity_days integer not null,
    priority integer not null,
    requires_safe_discount_cap boolean not null,
    business_reason text not null
);

create table if not exists analytics.offer_recommendations (
    customer_id varchar(20) not null,
    offer_id varchar(40) not null references analytics.offer_catalogue(offer_id),
    buyer_type varchar(60) not null,
    value_segment varchar(30) not null,
    lifecycle_stage varchar(50) not null,
    retention_priority varchar(10) not null,
    preferred_category varchar(50),
    offered_discount_pct numeric(6,4) not null default 0,
    discount_capped boolean not null default false,
    estimated_offer_cost_gbp numeric(14,2),
    estimated_order_gross_profit_after_offer_gbp numeric(14,2),
    reason_code text not null,
    offer_rank integer not null,
    recommendation_role varchar(20) not null,
    primary key (customer_id, offer_id)
);

create table if not exists analytics.offer_outcomes (
    recommendation_id varchar(40) primary key,
    customer_id varchar(20) not null,
    offer_id varchar(40) not null,
    recommendation_role varchar(20) not null,
    is_simulated boolean not null default true,
    delivery_status varchar(20),
    customer_response varchar(20),
    redeemed boolean,
    sent_at timestamp,
    responded_at timestamp,
    redeemed_at timestamp,
    follow_up_revenue_gbp numeric(14,2),
    feedback_theme varchar(60),
    feedback_sentiment varchar(20),
    learning_signal text
);

create index if not exists ix_transactions_customer
    on analytics.transactions_clean(customer_id, invoice_at);
create index if not exists ix_customer_360_action
    on analytics.customer_360(retention_priority, buyer_type, lifecycle_stage);
create index if not exists ix_recommendations_primary
    on analytics.offer_recommendations(recommendation_role, retention_priority);
