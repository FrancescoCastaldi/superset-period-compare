#!/usr/bin/env python3
"""
Synthetic multi-domain fixture generator for Superset Period Compare testing.
Generates realistic generic data (sales, tickets, performance metrics) across 24 months
without any real customer or hospital data.
"""

from datetime import datetime, timedelta
import random
import sqlite3
import sys

CATEGORIES = ["Hardware", "Software", "Cloud Services", "Consulting", "Support"]
REGIONS = ["North", "South", "East", "West", "Central"]
TICKET_SEVERITIES = ["Low", "Medium", "High", "Critical"]


def generate_fixtures(db_path: str = "synthetic_data.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Sales Dataset (standard DATE string and epoch timestamp)
    cur.execute("DROP TABLE IF EXISTS sales_performance")
    cur.execute("""
        CREATE TABLE sales_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TEXT,
            order_timestamp INTEGER,
            category TEXT,
            region TEXT,
            sales_amount REAL,
            order_count INTEGER
        )
    """)

    # 2. Support Tickets Dataset (ISO format with time)
    cur.execute("DROP TABLE IF EXISTS support_tickets")
    cur.execute("""
        CREATE TABLE support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            closed_at TEXT,
            severity TEXT,
            resolution_minutes INTEGER,
            satisfaction_score REAL
        )
    """)

    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 12, 31)
    delta_days = (end_date - start_date).days

    sales_rows = []
    ticket_rows = []

    random.seed(42)

    for i in range(10000):
        day_offset = random.randint(0, delta_days)
        current_day = start_date + timedelta(days=day_offset)

        # Sales row
        order_date_str = current_day.strftime("%Y-%m-%d")
        epoch_ms = int(current_day.timestamp() * 1000)
        cat = random.choice(CATEGORIES)
        reg = random.choice(REGIONS)
        amount = round(random.uniform(50.0, 2500.0), 2)
        count = random.randint(1, 15)
        sales_rows.append((order_date_str, epoch_ms, cat, reg, amount, count))

        # Ticket row
        hour = random.randint(8, 18)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        created_dt = current_day.replace(hour=hour, minute=minute, second=second)
        res_mins = random.randint(15, 1440)
        closed_dt = created_dt + timedelta(minutes=res_mins)
        created_iso = created_dt.strftime("%Y-%m-%dT%H:%M:%S")
        closed_iso = closed_dt.strftime("%Y-%m-%dT%H:%M:%S")
        sev = random.choice(TICKET_SEVERITIES)
        score = round(random.uniform(1.0, 5.0), 1)
        ticket_rows.append((created_iso, closed_iso, sev, res_mins, score))

    cur.executemany("""
        INSERT INTO sales_performance (order_date, order_timestamp, category, region, sales_amount, order_count)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sales_rows)

    cur.executemany("""
        INSERT INTO support_tickets (created_at, closed_at, severity, resolution_minutes, satisfaction_score)
        VALUES (?, ?, ?, ?, ?)
    """, ticket_rows)

    conn.commit()
    conn.close()
    print(f"Successfully generated 10,000 sales records and 10,000 support tickets in {db_path}.")


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "synthetic_data.db"
    generate_fixtures(db_file)
