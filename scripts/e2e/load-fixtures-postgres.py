#!/usr/bin/env python3
"""
Loads the synthetic data of synthetic-data-generator.py into a PostgreSQL database
with typed columns (DATE and TIMESTAMP), suited to Superset time filters.

Usage (inside the Superset container, where psycopg2 is already installed):
    python load-fixtures-postgres.py --host db-light --user superset --password superset --database pcdata

The database is created if missing. The tables are recreated on every run.
No real data: only the random data of the generator, with a fixed seed.
"""

import argparse
import importlib.util
import os
import sqlite3
import tempfile

import psycopg2
from psycopg2 import sql


def load_generator():
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "synthetic_data_generator", os.path.join(here, "synthetic-data-generator.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_database(args):
    conn = psycopg2.connect(host=args.host, port=args.port, user=args.user, password=args.password, dbname="postgres")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (args.database,))
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(args.database)))
            print(f"Database {args.database} created")
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="db-light")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--user", default="superset")
    parser.add_argument("--password", default="superset")
    parser.add_argument("--database", default="pcdata")
    args = parser.parse_args()

    generator = load_generator()
    tmp_db = os.path.join(tempfile.mkdtemp(), "synthetic_data.db")
    generator.generate_fixtures(tmp_db)

    src = sqlite3.connect(tmp_db)
    sales = src.execute(
        "SELECT order_date, order_timestamp, category, region, sales_amount, order_count FROM sales_performance"
    ).fetchall()
    tickets = src.execute(
        "SELECT created_at, closed_at, severity, resolution_minutes, satisfaction_score FROM support_tickets"
    ).fetchall()
    src.close()

    ensure_database(args)
    conn = psycopg2.connect(host=args.host, port=args.port, user=args.user, password=args.password, dbname=args.database)
    with conn, conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS sales_performance")
        cur.execute("DROP TABLE IF EXISTS support_tickets")
        cur.execute(
            """
            CREATE TABLE sales_performance (
                id SERIAL PRIMARY KEY,
                order_date DATE NOT NULL,
                order_ts TIMESTAMP NOT NULL,
                category TEXT,
                region TEXT,
                sales_amount NUMERIC(12, 2),
                order_count INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE support_tickets (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL,
                closed_at TIMESTAMP,
                severity TEXT,
                resolution_minutes INTEGER,
                satisfaction_score NUMERIC(3, 1)
            )
            """
        )
        cur.executemany(
            """
            INSERT INTO sales_performance (order_date, order_ts, category, region, sales_amount, order_count)
            VALUES (%s, to_timestamp(%s / 1000.0) AT TIME ZONE 'UTC', %s, %s, %s, %s)
            """,
            sales,
        )
        cur.executemany(
            """
            INSERT INTO support_tickets (created_at, closed_at, severity, resolution_minutes, satisfaction_score)
            VALUES (%s, %s, %s, %s, %s)
            """,
            tickets,
        )
        cur.execute("CREATE INDEX ix_sales_order_date ON sales_performance (order_date)")
        cur.execute("CREATE INDEX ix_tickets_created_at ON support_tickets (created_at)")
        cur.execute("SELECT count(*), min(order_date), max(order_date) FROM sales_performance")
        print("sales_performance:", cur.fetchone())
        cur.execute("SELECT count(*), min(created_at), max(created_at) FROM support_tickets")
        print("support_tickets:", cur.fetchone())
    conn.close()


if __name__ == "__main__":
    main()
