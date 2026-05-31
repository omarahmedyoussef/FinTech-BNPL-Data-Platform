import subprocess
import sys

# تثبيت المكتبات تلقائياً جوه الـ Container عشان نمنع أي ImportError
try:
    from sqlalchemy import create_engine, text
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy", "psycopg2-binary", "pandas"])
    from sqlalchemy import create_engine, text

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# الاتصال بقاعدة البيانات (استخدام host.docker.internal للربط بجهازك الأساسي)
DATABASE_URL = "postgresql://postgres:12345678@host.docker.internal:5432/BNPL_Enterprise_DB"

def run_etl():
    engine = create_engine(DATABASE_URL)
    
    etl_query = """
    -- 1. تحديث بُعد العملاء بالبيانات الجديدة
    INSERT INTO dw.dim_customers (customer_id, full_name, city, credit_limit)
    SELECT customer_id, full_name, city, credit_limit FROM public.customers
    ON CONFLICT (customer_id) DO UPDATE 
    SET full_name = EXCLUDED.full_name, city = EXCLUDED.city, credit_limit = EXCLUDED.credit_limit;

    -- 2. تحديث بُعد المحلات بالبيانات الجديدة
    INSERT INTO dw.dim_merchants (merchant_id, merchant_name, category, commission_rate)
    SELECT merchant_id, merchant_name, category, commission_rate FROM public.merchants
    ON CONFLICT (merchant_id) DO UPDATE 
    SET merchant_name = EXCLUDED.merchant_name, category = EXCLUDED.category, commission_rate = EXCLUDED.commission_rate;

    -- 3. حقن العمليات الجديدة في جدول الحقائق (Fact)
    INSERT INTO dw.fact_orders (order_id, customer_id, merchant_id, order_date_key, total_amount, order_time, duration_months, interest_rate)
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
    WHERE o.order_date >= NOW() - INTERVAL '1 hour'
    ON CONFLICT (order_id) DO NOTHING;
    """
    
    with engine.begin() as conn:
        conn.execute(text(etl_query))
    print("Hourly ETL batch executed successfully.")

default_args = {
    'owner': 'omar',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bnpl_hourly_etl_pipeline',
    default_args=default_args,
    description='Hourly ETL from OLTP to Data Warehouse',
    schedule='@hourly',  # التعديل الصحيح لنسخ Airflow الجديدة
    catchup=False
)

etl_task = PythonOperator(
    task_id='execute_hourly_etl',
    python_callable=run_etl,
    dag=dag,
)

etl_task