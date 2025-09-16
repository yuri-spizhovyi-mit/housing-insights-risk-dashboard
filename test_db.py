#!/usr/bin/env python3
"""
Test database connection and access
"""

import os
import sys
from ml.src.etl.db import get_conn, get_engine


def test_psycopg2_connection():
    """Test raw psycopg2 connection"""
    print("Testing psycopg2 connection...")
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"✅ psycopg2 connection successful!")
            print(f"   PostgreSQL version: {version}")

        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user;")
            db_name, user = cur.fetchone()
            print(f"   Database: {db_name}, User: {user}")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ psycopg2 connection failed: {e}")
        return False


def test_sqlalchemy_connection():
    """Test SQLAlchemy engine connection"""
    print("\nTesting SQLAlchemy connection...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test;"))
            test_value = result.scalar()
            print(f"✅ SQLAlchemy connection successful!")
            print(f"   Test query result: {test_value}")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False


def test_listings_table():
    """Test if listings_raw table exists and is accessible"""
    print("\nTesting listings_raw table access...")
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'listings_raw'
                );
            """)
            table_exists = cur.fetchone()[0]

            if table_exists:
                print("✅ listings_raw table exists")

                # Get table info
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'listings_raw'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print(f"   Table has {len(columns)} columns:")
                for col_name, col_type in columns:
                    print(f"     - {col_name}: {col_type}")

                # Count rows
                cur.execute("SELECT COUNT(*) FROM public.listings_raw;")
                row_count = cur.fetchone()[0]
                print(f"   Current row count: {row_count}")

            else:
                print("❌ listings_raw table does not exist")
                return False

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Table access failed: {e}")
        return False


def test_environment_variables():
    """Check what database environment variables are set"""
    print("\nChecking environment variables...")
    db_vars = [
        "DATABASE_URL",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
    ]

    for var in db_vars:
        value = os.getenv(var)
        if value:
            # Mask password for security
            if "PASSWORD" in var:
                value = "*" * len(value)
            print(f"   {var}: {value}")
        else:
            print(f"   {var}: (not set)")


def main():
    print("=== Database Connection Test ===\n")

    # Check environment
    test_environment_variables()

    # Test connections
    psycopg2_ok = test_psycopg2_connection()
    sqlalchemy_ok = test_sqlalchemy_connection()

    # Test table access
    if psycopg2_ok:
        table_ok = test_listings_table()
    else:
        table_ok = False

    # Summary
    print("\n=== Test Summary ===")
    print(f"psycopg2 connection: {'✅ PASS' if psycopg2_ok else '❌ FAIL'}")
    print(f"SQLAlchemy connection: {'✅ PASS' if sqlalchemy_ok else '❌ FAIL'}")
    print(f"Table access: {'✅ PASS' if table_ok else '❌ FAIL'}")

    if not (psycopg2_ok and sqlalchemy_ok):
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check database credentials in environment variables")
        print("   3. Verify database exists and user has access")
        print("   4. Check if database is on a different port (default: 5432)")


if __name__ == "__main__":
    main()
