from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:12345678@localhost:5432/BNPL_Enterprise_DB")

dw_setup_query = """
DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

CREATE TABLE dw.dim_customers (
    customer_id INT PRIMARY KEY,
    full_name VARCHAR(150),
    city VARCHAR(50),
    credit_limit NUMERIC(10, 2)
);

CREATE TABLE dw.dim_merchants (
    merchant_id INT PRIMARY KEY,
    merchant_name VARCHAR(100),
    category VARCHAR(50),
    commission_rate NUMERIC(4, 2)
);

CREATE TABLE dw.dim_date (
    date_key DATE PRIMARY KEY,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    day INT,
    day_of_week INT,
    day_name VARCHAR(20),
    is_weekend BOOLEAN
);

CREATE TABLE dw.fact_orders (
    order_id INT PRIMARY KEY,
    customer_id INT REFERENCES dw.dim_customers(customer_id),
    merchant_id INT REFERENCES dw.dim_merchants(merchant_id),
    order_date_key DATE REFERENCES dw.dim_date(date_key),
    total_amount NUMERIC(10, 2),
    order_time TIMESTAMP,
    duration_months INT,
    interest_rate NUMERIC(4, 2)
);

INSERT INTO dw.dim_customers SELECT customer_id, full_name, city, credit_limit FROM public.customers;
INSERT INTO dw.dim_merchants SELECT merchant_id, merchant_name, category, commission_rate FROM public.merchants;

INSERT INTO dw.dim_date
SELECT 
    datum AS date_key,
    EXTRACT(YEAR FROM datum) AS year,
    EXTRACT(QUARTER FROM datum) AS quarter,
    EXTRACT(MONTH FROM datum) AS month,
    TO_CHAR(datum, 'Month') AS month_name,
    EXTRACT(DAY FROM datum) AS day,
    EXTRACT(DOW FROM datum) + 1 AS day_of_week,
    TO_CHAR(datum, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM datum) IN (5, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2024-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) datum;

INSERT INTO dw.fact_orders
SELECT DISTINCT ON (o.order_id)
    o.order_id, 
    o.customer_id, 
    o.merchant_id, 
    o.order_date::DATE AS order_date_key,
    o.total_amount, 
    o.order_date AS order_time,
    p.duration_months, 
    p.interest_rate
FROM public.orders o
JOIN public.payment_plans p ON o.order_id = p.order_id
ORDER BY o.order_id, p.plan_id;
"""

with engine.begin() as conn:
    conn.execute(text(dw_setup_query))

print("Data warehouse built and populated successfully.")