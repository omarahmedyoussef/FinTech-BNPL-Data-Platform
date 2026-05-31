import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:12345678@localhost:5432/BNPL_Enterprise_DB")

df_customers = pd.read_sql("SELECT * FROM customers", engine)
df_merchants = pd.read_sql("SELECT * FROM merchants", engine)
df_products = pd.read_sql("SELECT * FROM products", engine)
df_orders = pd.read_sql("SELECT * FROM orders", engine)
df_plans = pd.read_sql("SELECT * FROM payment_plans", engine)
df_installments = pd.read_sql("SELECT * FROM installments", engine)
df_repayments = pd.read_sql("SELECT * FROM repayments_log", engine)

df_customers["full_name"] = df_customers["full_name"].astype(str).str.strip()
df_customers["city"] = df_customers["city"].astype(str).str.strip().str.capitalize()
df_customers["city"] = df_customers["city"].replace("None", "Unknown")
df_customers["phone_number"] = df_customers["phone_number"].str.replace("ERR", "00")
df_customers.loc[df_customers["credit_limit"] < 0, "credit_limit"] = df_customers["credit_limit"] * -1

mean_order_amount = df_orders["total_amount"].mean()
df_orders["total_amount"] = df_orders["total_amount"].fillna(mean_order_amount)

df_orders = pd.merge(df_orders, df_customers[["customer_id", "signup_date"]], on="customer_id", how="inner")
wrong_date_mask = df_orders["order_date"] < df_orders["signup_date"]
df_orders.loc[wrong_date_mask, "order_date"] = df_orders["signup_date"] + pd.Timedelta(hours=1)
df_orders = df_orders.drop(columns=["signup_date"])

mean_installment = df_installments.loc[df_installments["monthly_payment_amount"] < 50000, "monthly_payment_amount"].mean()
df_installments.loc[df_installments["monthly_payment_amount"] > 50000, "monthly_payment_amount"] = mean_installment

valid_statuses = ["completed", "active", "late"]
df_installments.loc[~df_installments["installment_status"].isin(valid_statuses), "installment_status"] = "active"

df_repayments = pd.merge(df_repayments, df_installments[["installment_id", "due_date"]], on="installment_id", how="inner")
wrong_repay_mask = (df_repayments["due_date"] - df_repayments["payment_date"]) > pd.Timedelta(days=360)
df_repayments.loc[wrong_repay_mask, "payment_date"] = df_repayments["due_date"] - pd.Timedelta(days=1)
df_repayments = df_repayments.drop(columns=["due_date"])

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE repayments_log RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE installments RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE payment_plans RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE orders RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE merchants RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE;"))

df_customers.to_sql("customers", engine, if_exists="append", index=False)
df_merchants.to_sql("merchants", engine, if_exists="append", index=False)
df_products.to_sql("products", engine, if_exists="append", index=False)
df_orders.to_sql("orders", engine, if_exists="append", index=False)
df_plans.to_sql("payment_plans", engine, if_exists="append", index=False)
df_installments.to_sql("installments", engine, if_exists="append", index=False)
df_repayments.to_sql("repayments_log", engine, if_exists="append", index=False)

print("Data cleaning complete.")