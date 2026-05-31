import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
from sqlalchemy import create_engine, text

# 1. الاتصال بقاعدة البيانات (الـ OLTP / public schema)
engine = create_engine("postgresql://postgres:12345678@localhost:5432/BNPL_Enterprise_DB")
fake = Faker()

print("🚀 بدء توليد البيانات وحقن المشاكل الحقيقية...")

# 2. توليد بيانات المحلات (Merchants)
merchants_data = [
    {"merchant_name": "B.TECH", "category": "Electronics", "commission_rate": 5.0},
    {"merchant_name": "Zara", "category": "Apparel", "commission_rate": 3.5},
    {"merchant_name": "Amazon", "category": "E-Commerce", "commission_rate": 4.0},
    {"merchant_name": "IKEA", "category": "Furniture", "commission_rate": 6.0},
    {"merchant_name": "Tradeline", "category": "Electronics", "commission_rate": 4.5}
]
df_merchants = pd.DataFrame(merchants_data)
df_merchants.to_sql("merchants", engine, if_exists="append", index=False)

# 3. توليد بيانات المنتجات (Products)
products_pool = {
    1: [("iPhone 15", 45000), ("Samsung TV 55", 22000), ("PlayStation 5", 30000)],
    2: [("Leather Jacket", 3500), ("Casual Shoes", 1800), ("Winter Coat", 5000)],
    3: [("Smart Watch", 2500), ("Wireless Earbuds", 1500), ("Power Bank", 900)],
    4: [("L-Shape Sofa", 40000), ("Office Chair", 4500), ("Dining Table", 15000)],
    5: [("MacBook Air", 60000), ("iPad Pro", 55000), ("AirPods Pro", 11000)]
}

products_data = []
for merchant_id, prods in products_pool.items():
    for name, price in prods:
        products_data.append({"merchant_id": merchant_id, "product_name": name, "price": price})
df_products = pd.DataFrame(products_data)
df_products.to_sql("products", engine, if_exists="append", index=False)

# 4. توليد بيانات العملاء مع حقن المشاكل (Customers)
customers_data = []
cities = ["Cairo", "Alexandria", "Giza", "Tanta", "Mansoura"]

for i in range(1, 10001):
    city = random.choice(cities)
    if i % 7 == 0: city = "cAiRo"           # مشكلة 1: حروف عشوائية كبيرة وصغيرة
    elif i % 11 == 0: city = "alexandria"    # مشكلة 2: حروف صغيرة بالكامل
    elif i % 25 == 0: city = None            # مشكلة 3: قيم مفقودة (Missing Values)

    phone = fake.phone_number()
    if i % 30 == 0: phone = f"010-ERR-{i}"   # مشكلة 4: أرقام تليفونات بايظة فيها نصوص

    credit_limit = random.randint(20000, 100000)
    if i % 50 == 0: credit_limit = -5000.00  # مشكلة 5: حدود ائتمان بالسالب

    customers_data.append({
        "full_name": f"   {fake.name()}   " if i % 5 == 0 else fake.name(), # مشكلة 6: مسافات زيادة
        "city": city,
        "phone_number": phone,
        "credit_limit": credit_limit,
        "signup_date": fake.date_time_between(start_date="-2y", end_date="-1y")
    })
df_customers = pd.DataFrame(customers_data)
df_customers.to_sql("customers", engine, if_exists="append", index=False)

# لقطة سريعة من الـ IDs الحقيقية اللي نزلت في الداتا بيز عشان الـ Foreign Keys متضربش
with engine.connect() as conn:
    customer_ids = [row[0] for row in conn.execute(text("SELECT customer_id FROM customers;")).fetchall()]

# 5. توليد بيانات الطلبات مع حقن المشاكل (Orders)
orders_data = []
for i in range(1, 25001):
    cust_id = random.choice(customer_ids)
    merch_id = random.randint(1, 5)

    total_amount = random.randint(3000, 50000)
    if i % 40 == 0: total_amount = None      # مشكلة 7: مبالغ مفقودة تماماً

    signup_dt = df_customers.iloc[customers_data.index(customers_data[cust_id-1])]["signup_date"] if cust_id <= len(df_customers) else datetime.now()
    order_dt = signup_dt + timedelta(days=random.randint(1, 300))
    if i % 45 == 0: order_dt = signup_dt - timedelta(days=365) # مشكلة 8: تاريخ أوردر قبل تاريخ تسجيل العميل!

    orders_data.append({
        "customer_id": cust_id,
        "merchant_id": merch_id,
        "total_amount": total_amount,
        "order_date": order_dt
    })
df_orders = pd.DataFrame(orders_data)
df_orders.to_sql("orders", engine, if_exists="append", index=False)

# 6. توليد خطط التقسيط (Payment Plans)
plans_data = []
for i in range(1, 25001):
    plans_data.append({
        "order_id": i,
        "duration_months": random.choice([3, 6, 12]),
        "interest_rate": random.choice([0.0, 5.0, 10.0])
    })
df_plans = pd.DataFrame(plans_data)
df_plans.to_sql("payment_plans", engine, if_exists="append", index=False)

# 7. توليد الأقساط وحقن المشاكل (Installments)
installments_data = []
inst_counter = 1

for plan in plans_data:
    order_id = plan["order_id"]
    months = plan["duration_months"]
    order_row = orders_data[order_id - 1]

    t_amt = order_row["total_amount"] if order_row["total_amount"] else 12000
    base_payment = t_amt / months

    for m in range(1, months + 1):
        status = random.choice(["completed", "active", "late"])
        if inst_counter % 150 == 0: status = "unknown_status"      # مشكلة 9: حالات قسط مش مفهومة
        
        payment_amt = base_payment
        if inst_counter % 200 == 0: payment_amt = 99999.00         # مشكلة 10: قسط قيمته شاذة وضخمة جداً (Outlier)

        due_dt = order_row["order_date"] + timedelta(days=30 * m)

        installments_data.append({
            "plan_id": order_id,
            "due_date": due_dt,
            "monthly_payment_amount": payment_amt,
            "installment_status": status
        })
        inst_counter += 1

df_installments = pd.DataFrame(installments_data)
df_installments.to_sql("installments", engine, if_exists="append", index=False)

# 8. دفتر المدفوعات وحقن المشاكل (Repayments Log)
repayments_data = []
for i, inst in enumerate(installments_data, start=1):
    if inst["installment_status"] == "completed":
        pay_dt = inst["due_date"] - timedelta(days=random.randint(1, 15))
        if i % 100 == 0: pay_dt = inst["due_date"] - timedelta(days=365) # مشكلة 11: دفع قسط قبل ميعاد الأوردر بسنة!

        repayments_data.append({
            "installment_id": i,
            "amount_paid": inst["monthly_payment_amount"],
            "payment_date": pay_dt,
            "payment_method": random.choice(["Credit Card", "Fawry", "Cash"])
        })

df_repayments = pd.DataFrame(repayments_data)
df_repayments.to_sql("repayments_log", engine, if_exists="append", index=False)

print("🎯 خلسنا! البيانات الـ Raw المليانة مشاكل اتحقنت بنجاح في الـ public schema.")