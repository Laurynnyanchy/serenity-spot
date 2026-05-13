#!/usr/bin/env python3
"""
Serenity Spot — Server startup helper
Usage: python start_server.py
"""
import os, sys, subprocess, socket

BOLD="\033[1m"; RED="\033[91m"; GREEN="\033[92m"; YELLOW="\033[93m"; CYAN="\033[96m"; RESET="\033[0m"
def ok(m):   print(f"  {GREEN} {m}{RESET}")
def err(m):  print(f"  {RED} {m}{RESET}")
def warn(m): print(f"  {YELLOW}  {m}{RESET}")
def info(m): print(f"  {CYAN}  {m}{RESET}")

print(f"\n{BOLD}{'='*52}\n  Serenity Spot — Pre-flight Check\n{'='*52}{RESET}\n")
errors = 0

# ── 1. .env ───────────────────────────────────────────
print(f"{BOLD}[1/4] Checking .env file…{RESET}")
if not os.path.exists(".env"):
    err(".env not found!")
    info("Run: cp env.example .env  then fill in your values")
    errors += 1
else:
    ok(".env found")
    from dotenv import load_dotenv; load_dotenv()
    missing = [k for k in ["MYSQL_HOST","MYSQL_USER","MYSQL_PASSWORD","MYSQL_DB","SECRET_KEY"] if not os.getenv(k)]
    if missing: err(f"Missing in .env: {', '.join(missing)}"); errors += 1
    else: ok("All required env vars present")

# ── 2. packages ───────────────────────────────────────
print(f"\n{BOLD}[2/4] Checking Python packages…{RESET}")
missing_pkgs = []
for pkg in ["fastapi","uvicorn","dotenv","httpx","aiomysql","bcrypt","jose"]:
    try: __import__(pkg.replace("-","_"))
    except ImportError: missing_pkgs.append(pkg)
if missing_pkgs:
    err(f"Missing: {', '.join(missing_pkgs)}")
    info("pip install fastapi uvicorn[standard] python-dotenv httpx aiomysql bcrypt python-jose[cryptography]")
    errors += 1
else: ok("All packages installed")

# ── 3. MySQL ──────────────────────────────────────────
print(f"\n{BOLD}[3/4] Testing MySQL connection…{RESET}")
from dotenv import load_dotenv; load_dotenv()

db_host = os.getenv("MYSQL_HOST", "localhost")
db_port = int(os.getenv("MYSQL_PORT", "3306"))
db_user = os.getenv("MYSQL_USER", "root")
db_pass = os.getenv("MYSQL_PASSWORD", "")
db_name = os.getenv("MYSQL_DB", "serenityspot")

# Auto-detect: try the configured host first, then fallback candidates
import asyncio, aiomysql

async def try_connect(host, port, user, password, db):
    conn = await aiomysql.connect(
        host=host, port=port, user=user,
        password=password, db=db, connect_timeout=3
    )
    async with conn.cursor() as cur:
        await cur.execute("SELECT VERSION()")
        row = await cur.fetchone()
    conn.close()
    return row[0]

candidates = [db_host]
if db_host == "localhost" and "127.0.0.1" not in candidates:
    candidates.append("127.0.0.1")
if db_host == "127.0.0.1" and "localhost" not in candidates:
    candidates.append("localhost")

connected_host = None
db_version = None

for host in candidates:
    try:
        db_version = asyncio.run(try_connect(host, db_port, db_user, db_pass, db_name))
        connected_host = host
        break
    except Exception as e:
        last_err = e

if connected_host:
    ok(f"MySQL connected on '{connected_host}' — {db_version}")
    if connected_host != db_host:
        warn(f"Connected via '{connected_host}' but .env says '{db_host}'")
        warn(f"Fix: open your .env and change  MYSQL_HOST={db_host}  →  MYSQL_HOST={connected_host}")
        errors += 1
else:
    err(f"MySQL connection failed: {last_err}")
    print()
    info("Common fixes for XAMPP on Windows:")
    info("  1. Open XAMPP Control Panel and click START next to MySQL")
    info(f"  2. In your .env, change MYSQL_HOST=localhost → MYSQL_HOST=127.0.0.1")
    info(f"  3. Make sure the database exists:")
    info(f"     Open phpMyAdmin → New → Name: {db_name} → Create")
    info(f"     OR run in MySQL shell:")
    info(f"     CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4;")
    errors += 1

# ── 4. port ───────────────────────────────────────────
print(f"\n{BOLD}[4/4] Checking port 8000…{RESET}")
with socket.socket() as s:
    if s.connect_ex(("localhost", 8000)) == 0:
        warn("Port 8000 in use — stop existing server first (Ctrl+C in its terminal)")
    else:
        ok("Port 8000 free")

# ── Summary ───────────────────────────────────────────
print(f"\n{BOLD}{'='*52}{RESET}")
if errors:
    print(f"{RED}{BOLD}  {errors} issue(s) found. Fix them then re-run.{RESET}\n{'='*52}\n")
    sys.exit(1)
else:
    print(f"{GREEN}{BOLD}  All checks passed! Starting server…{RESET}")
    print(f"{'='*52}")
    print(f"\n{CYAN}  API  → http://localhost:8000")
    print(f"  Docs → http://localhost:8000/docs{RESET}\n  Press Ctrl+C to stop.\n")
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"])