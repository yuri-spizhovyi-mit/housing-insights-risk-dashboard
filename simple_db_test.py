import psycopg2
from sqlalchemy import create_engine, text

# Test 1: Direct psycopg2 connection
print("=== Testing psycopg2 connection ===")
try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        database="hird",
        user="postgres",
        password="postgres",
    )
    print("✅ psycopg2 connection successful!")

    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM house_price_index;")
    result = cursor.fetchone()
    print(f"✅ Query successful! house_price_index has {result[0]} rows")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ psycopg2 connection failed: {e}")

# Test 2: SQLAlchemy connection
print("\n=== Testing SQLAlchemy connection ===")
try:
    engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/hird"
    )
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM house_price_index;"))
        count = result.scalar()
        print(
            f"✅ SQLAlchemy connection successful! house_price_index has {count} rows"
        )
except Exception as e:
    print(f"❌ SQLAlchemy connection failed: {e}")

# Test 3: Try with different host formats
print("\n=== Testing different host formats ===")
hosts_to_try = ["127.0.0.1", "localhost", "0.0.0.0"]

for host in hosts_to_try:
    try:
        conn = psycopg2.connect(
            host=host,
            port="5432",
            database="hird",
            user="postgres",
            password="postgres",
        )
        print(f"✅ Connection to {host} successful!")
        conn.close()
        break
    except Exception as e:
        print(f"❌ Connection to {host} failed: {e}")
