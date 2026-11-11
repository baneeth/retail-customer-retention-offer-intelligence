# Retail Customer Retention and Offer Intelligence

A complete portfolio data-analytics project that turns real transaction history into a customer-level action queue. It profiles regular shoppers and bulk-buying candidates, detects changes in purchase activity, assigns multiple eligible predefined offers, protects product margin, and records the outcome fields needed for later learning.

## What the finished system does

1. Cleans the public UCI Online Retail transaction workbook.
2. Connects many invoices to the same known customer through `CustomerID`.
3. Aggregates line items into orders and orders into a Customer 360 table.
4. Separates regular retail, large-order, and recurring bulk/wholesale behaviour.
5. Derives value, lifecycle, product preference, and retention-priority segments.
6. Applies category-level margin assumptions and safe discount caps.
7. Matches each customer to as many as three eligible offers from a 27-offer catalogue.
8. Selects exactly one primary offer and keeps alternatives for human review.
9. Creates an outcome tracker and a clearly labelled simulated learning sandbox.
10. Presents the action queue and summary metrics in a local interactive dashboard.

## Headline results

| Measure | Result | Status |
|---|---:|---|
| Source rows | 541,909 | Real source data |
| Clean transaction rows | 397,884 | Derived from real data |
| Completed orders | 18,532 | Derived from real data |
| Identified customers | 4,338 | Derived from real data |
| Reconciled revenue | £8,911,407.90 | Derived from real data |
| Estimated gross profit | £3,499,601.36 | Assumption-based estimate |
| Regular retail customers | 3,767 | Rule-based classification |
| Large-order candidates | 305 | Rule-based classification |
| Recurring bulk/wholesale candidates | 266 | Rule-based classification |
| Catalogue offers | 27 | Business rules |
| Eligible customer-offer records | 10,722 | Rule-engine output |
| Primary offers | 4,338 | One per customer |
| Backend quality status | PASS | Nine automated checks |

The campaign response file is intentionally simulated because the public dataset contains no real offer sends, redemptions, reviews, or feedback. Its 32.02% acceptance and 23.26% redemption rates demonstrate the evaluation design; they are not claims about real customer behaviour.

## Dataset and customer identity

Source: [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), a UK non-store retailer's transactions from 1 December 2010 to 9 December 2011.

`CustomerID` is stable across invoices, so multiple orders can be joined to one customer. Rows without a customer ID cannot safely be linked to a person; 135,080 such source rows are documented and excluded from customer-level analysis. The project also removes cancellations, non-positive quantities, and non-positive prices. No attempt is made to guess an identity from names, addresses, or product combinations.

## Customer and product diversity

Buyer-type thresholds use the customer-level 90th percentiles from this dataset:

- average order value at least £667.24, or average units per order at least 416.99, creates a bulk signal;
- one or two orders with a bulk signal becomes a large-order candidate;
- three or more orders with a bulk signal becomes a recurring bulk/wholesale candidate;
- everyone else remains a regular retail customer.

This describes observed buying behaviour, not verified legal company status.

Products are mapped to seven merchandise categories plus a service/adjustment group: gifts and novelty, home decor and lighting, kitchen and dining, gift accessories, seasonal/event, paper and stationery, and storage/organisation. Category preferences are based on each customer's revenue mix.

## Offer design

The catalogue includes relationship, convenience, service, bundle, discount, and account-management offers. It is not a single-discount recommender.

| Customer situation | Predefined choices |
|---|---|
| Recent first-time | loyalty points, free delivery, preferred-category trial |
| One-time, not converted | reminder, starter bundle, delivery conversion |
| Active regular repeat | loyalty points, category bundle, seasonal access, VIP service |
| Slowing regular repeat | reminder, category reactivation, free delivery |
| Inactive regular | category bundle, delivery, personalised win-back, gift with purchase |
| Service failure | recovery credit, only after confirmed negative feedback |
| Large-order candidate | business account invitation, volume incentive, priority fulfilment |
| Recurring bulk | tiered pricing, priority fulfilment, monthly invoicing, reorder planning, account review, scheduled delivery |

Requested discounts are checked against the preferred category's policy cap. Categories range from an 8% cap for kitchen/dining and storage to a 15% cap for gift accessories and seasonal/event items. Unknown merchandise categories never receive a margin-controlled discount.

## Architecture

```text
UCI workbook
    -> clean transaction lines
    -> order table
    -> Customer 360 + preferences + economics
    -> buyer type + value + lifecycle + priority
    -> offer eligibility + margin guardrail + ranking
    -> primary and alternative recommendations
    -> outcome tracker
    -> simulated learning sandbox (separate and labelled)
    -> interactive local dashboard
```

Python performs the reproducible file pipeline. PostgreSQL-compatible SQL demonstrates how the same model can be implemented in a warehouse. The frontend is buildless HTML/CSS/JavaScript so it can be reviewed locally without a deployment or database connection.

## Repository guide

- `src/` - preparation, Customer 360, segmentation, offer matching, simulation, evaluation, and validation.
- `sql/` - analytical schema, Customer 360 query, catalogue loading, recommendation query, performance reporting, and data contracts.
- `outputs/prepared/` - clean and derived CSV/JSON products.
- `dashboard/` - finished local dashboard and its data exporter.
- `work/` - original public source workbook and local working files.

The Git repository includes the original public workbook, the offer and margin rule inputs, and the finished dashboard. Large generated CSVs and the delivery ZIP are left out of Git; `python src/run_pipeline.py` recreates the analytical outputs.

## Run the project

Python 3.11 or newer is recommended.

```powershell
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

For a faster rebuild after the source workbook has already been cleaned:

```powershell
python src/run_pipeline.py --skip-audit
```

Run only the automated backend controls:

```powershell
python src/validate_backend.py
```

Open the dashboard locally:

```powershell
cd dashboard
python -m http.server 8765
```

Then visit `http://127.0.0.1:8765/`. A web server is required because the dashboard fetches `dashboard-data.json`; opening `index.html` directly can be blocked by browser file-security rules.

## Important analytical boundaries

- Transaction behaviour is real; margins, offer costs, feedback, and campaign outcomes are not present in UCI and are explicitly marked as assumptions or simulations.
- The activity rules are transparent business heuristics, not a trained churn-probability model.
- Bulk labels are candidates inferred from behaviour, not confirmed businesses.
- Simulated outcomes are useful for testing the measurement loop, not for claiming ROI.
- A production system would replace assumed margins and simulated outcomes with ERP, CRM, support, and campaign-platform data.
