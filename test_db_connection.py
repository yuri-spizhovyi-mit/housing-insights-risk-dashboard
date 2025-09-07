import psycopg2
import os

# Test with new user
try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5433",
        database="hird",
        user="testuser",
        password="testpass",
    )
    print("✅ Test user connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Test user connection failed: {e}")

# Test direct connection
try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        database="hird",
        user="postgres",
        password="postgres",
    )
    print("✅ Direct connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Direct connection failed: {e}")

# Test with localhost
try:
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="hird",
        user="postgres",
        password="postgres",
    )
    print("✅ Localhost connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Localhost connection failed: {e}")
