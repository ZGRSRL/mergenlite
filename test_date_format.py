#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tarih formatı testi"""

from datetime import datetime, timedelta, timezone

now_utc = datetime.now(timezone.utc)
start_date = now_utc - timedelta(days=60)

print(f"Now UTC: {now_utc}")
print(f"Start (60 days ago): {start_date}")
print(f"Formatted MM/dd/YYYY: {start_date.strftime('%m/%d/%Y')}")

# Bugünün tarihi
today = datetime.now()
print(f"\nToday: {today.strftime('%Y-%m-%d')}")
print(f"60 days ago: {(today - timedelta(days=60)).strftime('%Y-%m-%d')}")
print(f"Formatted: {(today - timedelta(days=60)).strftime('%m/%d/%Y')}")

