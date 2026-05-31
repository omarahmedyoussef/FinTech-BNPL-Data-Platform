-- 1. جدول العملاء
CREATE TABLE Customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(150),
    city VARCHAR(50),
    phone_number VARCHAR(50),
    credit_limit NUMERIC(10, 2),
    signup_date TIMESTAMP
);

-- 2. جدول المحلات/الشركاء
CREATE TABLE Merchants (
    merchant_id SERIAL PRIMARY KEY,
    merchant_name VARCHAR(100),
    category VARCHAR(50),
    commission_rate NUMERIC(4, 2) -- نسبة عمولة الشركة من المحل
);

-- 3. جدول المنتجات
CREATE TABLE Products (
    product_id SERIAL PRIMARY KEY,
    merchant_id INT REFERENCES Merchants(merchant_id),
    product_name VARCHAR(150),
    price NUMERIC(10, 2)
);

-- 4. جدول الطلبات (العمليات)
CREATE TABLE Orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES Customers(customer_id),
    merchant_id INT REFERENCES Merchants(merchant_id),
    total_amount NUMERIC(10, 2),
    order_date TIMESTAMP
);

-- 5. جدول خطط التقسيط المتاحة
CREATE TABLE Payment_Plans (
    plan_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES Orders(order_id),
    duration_months INT, -- 3 شهور، 6 شهور، 12 شهر
    interest_rate NUMERIC(4, 2) -- نسبة الفائدة المضافة
);

-- 6. جدول الأقساط الزمني
CREATE TABLE Installments (
    installment_id SERIAL PRIMARY KEY,
    plan_id INT REFERENCES Payment_Plans(plan_id),
    due_date TIMESTAMP,
    monthly_payment_amount NUMERIC(10, 2),
    installment_status VARCHAR(20) -- active, completed, late, unknown_status
);

-- 7. دفتر المدفوعات الحقيقية
CREATE TABLE Repayments_Log (
    repayment_id SERIAL PRIMARY KEY,
    installment_id INT REFERENCES Installments(installment_id),
    amount_paid NUMERIC(10, 2),
    payment_date TIMESTAMP,
    payment_method VARCHAR(30) -- Cash, Credit Card, Fawry
);