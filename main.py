"""
Serenity Spot — FastAPI + MySQL + Daraja M-Pesa

Install:
    pip install fastapi uvicorn[standard] python-dotenv httpx aiomysql bcrypt python-jose[cryptography]

Run:
    uvicorn main:app --reload --port 8000

.env required variables:
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
    MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET
    MPESA_SHORTCODE, MPESA_PASSKEY
    MPESA_CALLBACK_URL, MPESA_ENV
    SECRET_KEY
"""

import base64
import json
import logging
import random
import string
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from os import getenv
from typing import Optional

import aiomysql
import bcrypt
import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("serenity-spot")

# ── CONFIG ────────────────────────────────────────────────────────
MYSQL_HOST     = getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = getenv("MYSQL_PASSWORD", "")
MYSQL_DB       = getenv("MYSQL_DB", "serenityspot")

MPESA_ENV             = getenv("MPESA_ENV", "sandbox")
MPESA_CONSUMER_KEY    = getenv("MPESA_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = getenv("MPESA_CONSUMER_SECRET", "")
MPESA_SHORTCODE       = getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY         = getenv("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
MPESA_CALLBACK_URL    = getenv("MPESA_CALLBACK_URL", "https://yourdomain.com/api/mpesa/callback")

SECRET_KEY  = getenv("SECRET_KEY", "change-this-secret-before-production")
ALGORITHM   = "HS256"
TOKEN_HOURS = 24

DARAJA_BASE = (
    "https://sandbox.safaricom.co.ke"
    if MPESA_ENV == "sandbox"
    else "https://api.safaricom.co.ke"
)

# ── Flutterwave ───────────────────────────────────────────────
FLW_SECRET_KEY   = getenv("FLW_SECRET_KEY", "")   # FLWSECK_TEST-... from dashboard
FLW_PUBLIC_KEY   = getenv("FLW_PUBLIC_KEY", "")   # FLWPUBK_TEST-... (used in frontend)
FLW_VERIFY_URL   = "https://api.flutterwave.com/v3/transactions/{id}/verify"

# ── DB SCHEMA ─────────────────────────────────────────────────────
# Each statement is run independently so one warning/error doesn't abort the rest.
BASE_TABLES = [
    """CREATE TABLE IF NOT EXISTS users (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        first_name    VARCHAR(100) NOT NULL,
        last_name     VARCHAR(100) NOT NULL,
        email         VARCHAR(255) NOT NULL UNIQUE,
        phone         VARCHAR(20)  NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role          ENUM('guest','admin') DEFAULT 'guest',
        is_active     TINYINT(1) DEFAULT 1,
        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS rooms (
        id               INT AUTO_INCREMENT PRIMARY KEY,
        name             VARCHAR(200) NOT NULL DEFAULT '',
        type             VARCHAR(50)  NOT NULL DEFAULT '',
        price            INT          NOT NULL DEFAULT 0,
        max_people       INT          DEFAULT 2,
        badge            VARCHAR(50),
        image_url        TEXT,
        image_url2       TEXT,
        image_url3       TEXT,
        description      TEXT,
        full_description TEXT,
        amenities        JSON,
        rating           DECIMAL(3,1) DEFAULT 0,
        review_count     INT          DEFAULT 0,
        is_available     TINYINT(1)   DEFAULT 1,
        created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS bookings (
        id               VARCHAR(10)  PRIMARY KEY,
        room_id          INT          NOT NULL,
        guest_name       VARCHAR(200) NOT NULL,
        guest_email      VARCHAR(255) NOT NULL,
        guest_phone      VARCHAR(20)  NOT NULL,
        guest_count      INT          DEFAULT 1,
        checkin_date     DATE         NOT NULL,
        checkout_date    DATE         NOT NULL,
        nights           INT          NOT NULL,
        subtotal         INT          NOT NULL DEFAULT 0,
        service_fee      INT          DEFAULT 0,
        total_amount     INT          NOT NULL DEFAULT 0,
        special_requests TEXT,
        status           ENUM('pending','confirmed','cancelled','completed') DEFAULT 'pending',
        created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS payments (
        id                   INT AUTO_INCREMENT PRIMARY KEY,
        booking_id           VARCHAR(10)  NOT NULL,
        method               ENUM('mpesa','card','cash') DEFAULT 'mpesa',
        amount               INT          NOT NULL DEFAULT 0,
        status               ENUM('pending','paid','failed','refunded') DEFAULT 'pending',
        mpesa_phone          VARCHAR(20),
        checkout_request_id  VARCHAR(100),
        merchant_request_id  VARCHAR(100),
        mpesa_receipt        VARCHAR(50),
        failure_reason       TEXT,
        raw_callback         TEXT,
        completed_at         DATETIME,
        created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS reviews (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        room_id     INT          NOT NULL,
        booking_id  VARCHAR(10),
        guest_name  VARCHAR(200) NOT NULL,
        rating      TINYINT      NOT NULL,
        review_text TEXT         NOT NULL,
        status      ENUM('pending','approved','flagged') DEFAULT 'pending',
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS contact_messages (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        name       VARCHAR(200) NOT NULL,
        email      VARCHAR(255) NOT NULL,
        phone      VARCHAR(20),
        subject    VARCHAR(200) NOT NULL,
        message    TEXT         NOT NULL,
        is_read    TINYINT(1) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]

# Columns to add if missing (handles pre-existing tables with old schemas)
COLUMN_MIGRATIONS = {
    "users":    [
        ("first_name",    "VARCHAR(100) NOT NULL DEFAULT ''"),
        ("last_name",     "VARCHAR(100) NOT NULL DEFAULT ''"),
        ("phone",         "VARCHAR(20) NOT NULL DEFAULT ''"),
        ("password_hash", "VARCHAR(255) NOT NULL DEFAULT ''"),
        ("role",          "ENUM('guest','admin') DEFAULT 'guest'"),
        ("is_active",     "TINYINT(1) DEFAULT 1"),
        ("created_at",    "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ],
    "rooms": [
        ("name",             "VARCHAR(200) NOT NULL DEFAULT ''"),
        ("type",             "VARCHAR(50) NOT NULL DEFAULT ''"),
        ("price",            "INT NOT NULL DEFAULT 0"),
        ("max_people",       "INT DEFAULT 2"),
        ("badge",            "VARCHAR(50)"),
        ("image_url",        "TEXT"),
        ("image_url2",       "TEXT"),
        ("image_url3",       "TEXT"),
        ("description",      "TEXT"),
        ("full_description", "TEXT"),
        ("amenities",        "JSON"),
        ("rating",           "DECIMAL(3,1) DEFAULT 0"),
        ("review_count",     "INT DEFAULT 0"),
        ("is_available",     "TINYINT(1) DEFAULT 1"),
        ("created_at",       "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ],
    "bookings": [
        ("guest_name",       "VARCHAR(200) NOT NULL DEFAULT ''"),
        ("guest_email",      "VARCHAR(255) NOT NULL DEFAULT ''"),
        ("guest_phone",      "VARCHAR(20) NOT NULL DEFAULT ''"),
        ("guest_count",      "INT DEFAULT 1"),
        ("checkin_date",     "DATE"),
        ("checkout_date",    "DATE"),
        ("nights",           "INT NOT NULL DEFAULT 1"),
        ("subtotal",         "INT NOT NULL DEFAULT 0"),
        ("service_fee",      "INT DEFAULT 0"),
        ("total_amount",     "INT NOT NULL DEFAULT 0"),
        ("special_requests", "TEXT"),
        ("status",           "ENUM('pending','confirmed','cancelled','completed') DEFAULT 'pending'"),
        ("created_at",       "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ],
    "payments": [
        ("booking_id",           "VARCHAR(10) NOT NULL DEFAULT ''"),
        ("method",               "ENUM('mpesa','card','cash') DEFAULT 'mpesa'"),
        ("amount",               "INT NOT NULL DEFAULT 0"),
        ("status",               "ENUM('pending','paid','failed','refunded') DEFAULT 'pending'"),
        ("mpesa_phone",          "VARCHAR(20)"),
        ("checkout_request_id",  "VARCHAR(100)"),
        ("merchant_request_id",  "VARCHAR(100)"),
        ("mpesa_receipt",        "VARCHAR(50)"),
        ("failure_reason",       "TEXT"),
        ("raw_callback",         "TEXT"),
        ("completed_at",         "DATETIME"),
        ("created_at",           "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ],
    # contact_messages — old tables may use different column names
    "contact_messages": [
        ("name",       "VARCHAR(200) NOT NULL DEFAULT ''"),
        ("email",      "VARCHAR(255) NOT NULL DEFAULT ''"),
        ("phone",      "VARCHAR(20)"),
        ("subject",    "VARCHAR(200) NOT NULL DEFAULT ''"),
        ("message",    "TEXT"),
        ("is_read",    "TINYINT(1) DEFAULT 0"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ],
    "reviews": [
        ("room_id",     "INT NOT NULL DEFAULT 0"),
        ("booking_id",  "VARCHAR(10)"),
        ("guest_name",  "VARCHAR(200) NOT NULL DEFAULT ''"),
        ("rating",      "TINYINT NOT NULL DEFAULT 5"),
        ("review_text", "TEXT"),
        ("status",      "ENUM('pending','approved','flagged') DEFAULT 'pending'"),
        ("created_at",  "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ],
}

async def run_migrations(cur):
    """Create tables if missing, add columns if missing, rebuild VIEW."""

    # 1. Create base tables
    for sql in BASE_TABLES:
        try:
            await cur.execute(sql)
        except Exception as e:
            logger.warning(f"Table create warning (safe to ignore if table exists): {e}")

    # 2. Add missing columns to existing tables
    for table, columns in COLUMN_MIGRATIONS.items():
        try:
            await cur.execute(f"DESCRIBE `{table}`")
            existing = {row[0].lower() for row in await cur.fetchall()}
            for col_name, col_def in columns:
                if col_name.lower() not in existing:
                    try:
                        await cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{col_name}` {col_def}")
                        logger.info(f"✅ Added column {table}.{col_name}")
                    except Exception as e:
                        logger.warning(f"Could not add {table}.{col_name}: {e}")
        except Exception as e:
            logger.warning(f"Could not inspect {table}: {e}")

    # 3. Detect actual rooms column names and build VIEW defensively
    try:
        await cur.execute("DESCRIBE `rooms`")
        room_cols = {row[0].lower(): row[0] for row in await cur.fetchall()}

        # Map logical name → actual column name (handle old naming conventions)
        def find_col(candidates, fallback=None):
            for c in candidates:
                if c.lower() in room_cols:
                    return room_cols[c.lower()]
            return fallback

        name_col   = find_col(["name", "room_name",  "title"])       or "name"
        type_col   = find_col(["type", "room_type",  "category"])    or "type"
        price_col  = find_col(["price","room_price", "amount","rate"])or "price"
        image_col  = find_col(["image_url","image","photo","img"])    or "image_url"

        # Drop and recreate view with discovered column names
        # NOTE: b.* already includes b.status, so we do NOT alias it again
        await cur.execute("DROP VIEW IF EXISTS booking_details")
        await cur.execute(f"""
            CREATE VIEW booking_details AS
            SELECT
                b.*,
                r.`{name_col}`  AS room_name,
                r.`{type_col}`  AS room_type,
                r.`{price_col}` AS room_price,
                r.`{image_col}` AS room_image
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
        """)
        logger.info(f"✅ booking_details VIEW created (name={name_col}, type={type_col}, price={price_col}, image={image_col})")
    except Exception as e:
        logger.error(f"❌ Could not create booking_details VIEW: {e}")
        # App still works — VIEW is only used by admin listing endpoint


# ── APP LIFESPAN ──────────────────────────────────────────────────
pool: aiomysql.Pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    try:
        pool = await aiomysql.create_pool(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4",
            cursorclass=aiomysql.DictCursor,
            autocommit=True, minsize=2, maxsize=10,
        )
        logger.info("✅ Database pool created")

        async with pool.acquire() as conn:
            # Use a plain cursor (not DictCursor) for DESCRIBE so row[0] works
            async with conn.cursor(aiomysql.Cursor) as cur:
                await run_migrations(cur)

        logger.info("✅ Schema migrations applied")

    except Exception as e:
        logger.error(f"❌ DB startup failed: {e}")
        # App still starts — endpoints return 503 until DB is reachable

    yield

    if pool:
        pool.close()
        await pool.wait_closed()
        logger.info("✅ DB pool closed")


# ── APP ───────────────────────────────────────────────────────────
app = FastAPI(title="Serenity Spot API", version="2.1.0", lifespan=lifespan)
# Allow localhost for dev + your Netlify domain for production
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    getenv("FRONTEND_URL", ""),  # Set this to your Netlify URL in Railway env vars
]
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o]  # remove empty

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.netlify\.app",  # allows all netlify subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


# ── DB DEPENDENCY ─────────────────────────────────────────────────
async def get_db():
    if pool is None:
        raise HTTPException(503, "Database not available")
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            yield cur


# ── AUTH HELPERS ──────────────────────────────────────────────────
def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def verify_pw(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def make_token(user_id: int, role: str) -> str:
    exp = datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, SECRET_KEY, ALGORITHM)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db),
):
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except JWTError:
        raise HTTPException(401, "Invalid token")
    await db.execute("SELECT * FROM users WHERE id=%s AND is_active=1", (user_id,))
    user = await db.fetchone()
    if not user:
        raise HTTPException(401, "User not found")
    return user


async def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user


# ── DARAJA HELPERS ────────────────────────────────────────────────
async def mpesa_token() -> str:
    creds = base64.b64encode(
        f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()
    ).decode()
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{DARAJA_BASE}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {creds}"}, timeout=30,
        )
        r.raise_for_status()
        return r.json()["access_token"]


def mpesa_password() -> tuple[str, str]:
    ts  = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{ts}"
    return base64.b64encode(raw.encode()).decode(), ts


def normalize_phone(ph: str) -> str:
    ph = ph.strip().replace(" ", "").replace("-", "")
    if ph.startswith("+"): ph = ph[1:]
    if ph.startswith("0"): ph = "254" + ph[1:]
    if not ph.startswith("254"): ph = "254" + ph
    return ph


def new_booking_id() -> str:
    return "BNB" + "".join(random.choices(string.digits, k=5))


# ── MODELS ────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class BookingIn(BaseModel):
    room_id: int
    checkin: str
    checkout: str
    nights: int
    total: Optional[int] = None   # FIX: was missing from model
    name: str
    phone: str
    email: str
    guests: int
    requests: Optional[str] = ""


class STKIn(BaseModel):
    phone: str
    amount: int
    account_ref: str
    description: str


class ReviewIn(BaseModel):
    room_id: int
    booking_id: Optional[str] = None
    guest_name: str
    rating: int
    review_text: str


class ContactIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    subject: str
    message: str


# ── HEALTH ────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "Serenity Spot API v2.1", "env": MPESA_ENV}


@app.get("/api/health")
async def health(db=Depends(get_db)):
    await db.execute("SELECT 1")
    return {"status": "ok", "db": "connected", "ts": datetime.now().isoformat()}


# ── AUTH ──────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def register(req: RegisterIn, db=Depends(get_db)):
    await db.execute("SELECT id FROM users WHERE email=%s", (req.email.lower(),))
    if await db.fetchone():
        raise HTTPException(400, "Email already registered")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    pw = hash_pw(req.password)
    await db.execute(
        "INSERT INTO users (first_name,last_name,email,phone,password_hash,role) VALUES (%s,%s,%s,%s,%s,'guest')",
        (req.first_name, req.last_name, req.email.lower(), req.phone, pw),
    )
    await db.execute("SELECT * FROM users WHERE email=%s", (req.email.lower(),))
    user = await db.fetchone()
    token = make_token(user["id"], user["role"])
    return {"success": True, "token": token,
            "user": {"id": user["id"], "email": user["email"], "role": user["role"]}}


@app.post("/api/auth/login")
async def login(req: LoginIn, db=Depends(get_db)):
    await db.execute("SELECT * FROM users WHERE email=%s AND is_active=1", (req.email.lower(),))
    user = await db.fetchone()
    if not user or not verify_pw(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token = make_token(user["id"], user["role"])
    return {
        "success": True, "token": token,
        "user": {"id": user["id"],
                 "name": f"{user['first_name']} {user['last_name']}",
                 "email": user["email"], "role": user["role"]}
    }


@app.get("/api/auth/me")
async def me(user=Depends(get_current_user)):
    return {"id": user["id"],
            "name": f"{user['first_name']} {user['last_name']}",
            "email": user["email"], "role": user["role"]}


# ── ROOMS ─────────────────────────────────────────────────────────
@app.get("/api/rooms")
async def list_rooms(db=Depends(get_db)):
    await db.execute("SELECT * FROM rooms ORDER BY id")
    rows = await db.fetchall()
    for r in rows:
        if isinstance(r.get("amenities"), str):
            r["amenities"] = json.loads(r["amenities"])
    return rows


@app.get("/api/rooms/{room_id}")
async def get_room_api(room_id: int, db=Depends(get_db)):
    await db.execute("SELECT * FROM rooms WHERE id=%s", (room_id,))
    row = await db.fetchone()
    if not row:
        raise HTTPException(404, "Room not found")
    if isinstance(row.get("amenities"), str):
        row["amenities"] = json.loads(row["amenities"])
    return row


@app.post("/api/rooms")
async def create_room(data: dict, db=Depends(get_db), _=Depends(require_admin)):
    await db.execute(
        """INSERT INTO rooms (name,type,price,max_people,badge,image_url,image_url2,image_url3,
           description,full_description,amenities,is_available)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (data["name"], data["type"], data["price"], data.get("max_people", 2),
         data.get("badge"), data.get("image_url"), data.get("image_url2"), data.get("image_url3"),
         data.get("description"), data.get("full_description"),
         json.dumps(data.get("amenities", [])), int(data.get("is_available", True)))
    )
    await db.execute("SELECT * FROM rooms WHERE id=LAST_INSERT_ID()")
    return await db.fetchone()


@app.patch("/api/rooms/{room_id}")
async def update_room(room_id: int, data: dict, db=Depends(get_db), _=Depends(require_admin)):
    # FIX: use allowlist mapping to prevent SQL injection via column names
    allowed = {
        "name": "name", "type": "type", "price": "price",
        "max_people": "max_people", "badge": "badge",
        "image_url": "image_url", "description": "description",
        "is_available": "is_available", "amenities": "amenities"
    }
    sets, vals = [], []
    for k, v in data.items():
        col = allowed.get(k)
        if col:
            sets.append(f"`{col}`=%s")
            vals.append(json.dumps(v) if k == "amenities" else v)
    if not sets:
        raise HTTPException(400, "No valid fields provided")
    vals.append(room_id)
    await db.execute(f"UPDATE rooms SET {', '.join(sets)} WHERE id=%s", vals)
    return {"success": True}


@app.delete("/api/rooms/{room_id}")
async def delete_room(room_id: int, db=Depends(get_db), _=Depends(require_admin)):
    await db.execute("DELETE FROM rooms WHERE id=%s", (room_id,))
    return {"success": True}


# ── AVAILABILITY ──────────────────────────────────────────────────
@app.get("/api/rooms/{room_id}/availability")
async def check_avail(room_id: int, checkin: str, checkout: str, db=Depends(get_db)):
    await db.execute(
        """SELECT COUNT(*) AS cnt FROM bookings
           WHERE room_id=%s AND status IN ('pending','confirmed')
           AND NOT (checkout_date <= %s OR checkin_date >= %s)""",
        (room_id, checkin, checkout),
    )
    row = await db.fetchone()
    return {"available": row["cnt"] == 0}


# ── BOOKINGS ──────────────────────────────────────────────────────
@app.post("/api/bookings")
async def create_booking(req: BookingIn, db=Depends(get_db)):
    await db.execute("SELECT * FROM rooms WHERE id=%s AND is_available=1", (req.room_id,))
    room = await db.fetchone()
    if not room:
        raise HTTPException(404, "Room not found or unavailable")

    bid = new_booking_id()
    for _ in range(10):  # FIX: bounded loop to avoid infinite loop
        await db.execute("SELECT id FROM bookings WHERE id=%s", (bid,))
        if not await db.fetchone():
            break
        bid = new_booking_id()

    subtotal    = room["price"] * req.nights
    service_fee = round(subtotal * 0.05)
    total       = subtotal + service_fee

    await db.execute(
        """INSERT INTO bookings
           (id,room_id,guest_name,guest_email,guest_phone,guest_count,
            checkin_date,checkout_date,nights,subtotal,service_fee,total_amount,
            special_requests,status)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')""",
        (bid, req.room_id, req.name, req.email, req.phone, req.guests,
         req.checkin, req.checkout, req.nights, subtotal, service_fee, total,
         req.requests),
    )
    return {"success": True, "booking_id": bid, "total": total}


@app.get("/api/bookings")
async def list_bookings(status: Optional[str] = None, db=Depends(get_db), _=Depends(require_admin)):
    q = "SELECT * FROM booking_details"
    params = ()
    if status:
        # FIX: validate status to prevent SQL injection
        if status not in ("pending", "confirmed", "cancelled", "completed"):
            raise HTTPException(400, "Invalid status value")
        q += " WHERE booking_status=%s"
        params = (status,)
    q += " ORDER BY created_at DESC"
    await db.execute(q, params)
    rows = await db.fetchall()
    return [dict(r) for r in rows]


@app.get("/api/bookings/{bid}")
async def get_booking(bid: str, db=Depends(get_db)):
    await db.execute("SELECT * FROM booking_details WHERE id=%s", (bid,))
    row = await db.fetchone()
    if not row:
        raise HTTPException(404, "Booking not found")
    return dict(row)


@app.patch("/api/bookings/{bid}/status")
async def update_booking_status(bid: str, data: dict, db=Depends(get_db), _=Depends(require_admin)):
    s = data.get("status")
    if s not in ("pending", "confirmed", "cancelled", "completed"):
        raise HTTPException(400, "Invalid status")
    await db.execute("UPDATE bookings SET status=%s WHERE id=%s", (s, bid))
    return {"success": True}


# ── M-PESA ────────────────────────────────────────────────────────
@app.post("/api/mpesa/stk-push")
async def stk_push(req: STKIn, db=Depends(get_db)):
    if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
        raise HTTPException(503, "M-Pesa not configured. Add MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET to .env")
    try:
        token         = await mpesa_token()
        password, ts  = mpesa_password()
        phone         = normalize_phone(req.phone)

        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password, "Timestamp": ts,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": req.amount,
            "PartyA": phone, "PartyB": MPESA_SHORTCODE, "PhoneNumber": phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": req.account_ref[:12],
            "TransactionDesc": req.description[:13],
        }
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{DARAJA_BASE}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=30,
            )
            data = r.json()

        if data.get("ResponseCode") == "0":
            cid = data["CheckoutRequestID"]
            mid = data.get("MerchantRequestID", "")
            await db.execute(
                """INSERT INTO payments
                   (booking_id,method,amount,status,mpesa_phone,checkout_request_id,merchant_request_id)
                   VALUES (%s,'mpesa',%s,'pending',%s,%s,%s)""",
                (req.account_ref, req.amount, phone, cid, mid),
            )
            return {"success": True, "checkout_request_id": cid, "merchant_request_id": mid}
        else:
            raise HTTPException(400, data.get("errorMessage", "STK push failed"))

    except httpx.HTTPError as e:
        raise HTTPException(502, f"Daraja error: {e}")


@app.post("/api/mpesa/callback")
async def mpesa_callback(request: Request, db=Depends(get_db)):
    body     = await request.json()
    stk      = body.get("Body", {}).get("stkCallback", {})
    cid      = stk.get("CheckoutRequestID")
    result   = stk.get("ResultCode")

    if result == 0:
        items   = stk.get("CallbackMetadata", {}).get("Item", [])
        meta    = {i["Name"]: i.get("Value") for i in items}
        receipt = meta.get("MpesaReceiptNumber", "")
        await db.execute(
            """UPDATE payments SET status='paid', mpesa_receipt=%s,
               completed_at=NOW(), raw_callback=%s
               WHERE checkout_request_id=%s""",
            (receipt, json.dumps(body), cid),
        )
        await db.execute("SELECT booking_id FROM payments WHERE checkout_request_id=%s", (cid,))
        row = await db.fetchone()
        if row:
            await db.execute("UPDATE bookings SET status='confirmed' WHERE id=%s", (row["booking_id"],))
    else:
        reason = stk.get("ResultDesc", "Unknown")
        await db.execute(
            "UPDATE payments SET status='failed', failure_reason=%s WHERE checkout_request_id=%s",
            (reason, cid),
        )
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@app.get("/api/mpesa/status/{cid}")
async def payment_status(cid: str, db=Depends(get_db)):
    await db.execute(
        "SELECT status, mpesa_receipt, failure_reason FROM payments WHERE checkout_request_id=%s", (cid,)
    )
    row = await db.fetchone()
    if row:
        if row["status"] == "paid":
            return {"status": "paid", "receipt": row["mpesa_receipt"]}
        if row["status"] == "failed":
            return {"status": "failed", "reason": row["failure_reason"]}

    # Query Daraja directly if not yet reflected in DB
    try:
        token     = await mpesa_token()
        password, ts = mpesa_password()
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{DARAJA_BASE}/mpesa/stkpushquery/v1/query",
                json={"BusinessShortCode": MPESA_SHORTCODE, "Password": password,
                      "Timestamp": ts, "CheckoutRequestID": cid},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=20,
            )
            data = r.json()
        rc = str(data.get("ResultCode", ""))
        if rc == "0":
            await db.execute(
                "UPDATE payments SET status='paid', completed_at=NOW() WHERE checkout_request_id=%s", (cid,)
            )
            return {"status": "paid"}
        if rc in ("1032", "1037"):
            return {"status": "cancelled"}
    except Exception:
        pass
    return {"status": "pending"}


# ── FLUTTERWAVE ────────────────────────────────────────────────────
class FlwVerifyIn(BaseModel):
    transaction_id: int
    tx_ref: str
    booking_id: str
    expected_amount: int


@app.get("/api/flutterwave/config")
async def flw_config():
    """Returns the Flutterwave public key so frontend doesn't need to hardcode it."""
    if not FLW_PUBLIC_KEY:
        raise HTTPException(503, "Flutterwave not configured. Add FLW_PUBLIC_KEY to .env")
    return {"public_key": FLW_PUBLIC_KEY}


@app.post("/api/flutterwave/verify")
async def flw_verify(req: FlwVerifyIn, db=Depends(get_db)):
    """
    Verifies a Flutterwave transaction server-side to prevent spoofing.
    Called by payment.html after the checkout popup closes successfully.
    """
    if not FLW_SECRET_KEY:
        # No secret key configured — log and approve optimistically
        logger.warning("FLW_SECRET_KEY not set — skipping server-side verification")
        await db.execute("UPDATE bookings SET status='confirmed' WHERE id=%s", (req.booking_id,))
        return {"success": True, "warning": "Verification skipped — set FLW_SECRET_KEY in .env"}

    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(
                FLW_VERIFY_URL.format(id=req.transaction_id),
                headers={"Authorization": f"Bearer {FLW_SECRET_KEY}"},
                timeout=20,
            )
            data = r.json()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Flutterwave verification request failed: {e}")

    if data.get("status") != "success":
        raise HTTPException(400, f"Flutterwave returned: {data.get('message', 'Unknown error')}")

    flw_data   = data.get("data", {})
    flw_status = flw_data.get("status", "")
    flw_amount = int(flw_data.get("amount", 0))
    flw_ref    = flw_data.get("tx_ref", "")

    # Security checks
    if flw_status not in ("successful", "completed"):
        raise HTTPException(400, f"Transaction not successful (status: {flw_status})")

    if flw_ref != req.tx_ref:
        raise HTTPException(400, "Transaction reference mismatch — possible fraud attempt")

    # Allow ±1 KES tolerance for rounding
    if abs(flw_amount - req.expected_amount) > 1:
        raise HTTPException(400, f"Amount mismatch: expected {req.expected_amount}, got {flw_amount}")

    # Record payment and confirm booking
    await db.execute(
        """INSERT INTO payments
           (booking_id, method, amount, status, mpesa_receipt, completed_at)
           VALUES (%s, 'card', %s, 'paid', %s, NOW())
           ON DUPLICATE KEY UPDATE status='paid', completed_at=NOW()""",
        (req.booking_id, flw_amount, str(req.transaction_id)),
    )
    await db.execute("UPDATE bookings SET status='confirmed' WHERE id=%s", (req.booking_id,))

    logger.info(f"✅ Flutterwave payment verified: booking={req.booking_id} txn={req.transaction_id}")
    return {"success": True, "transaction_id": req.transaction_id, "amount": flw_amount}



@app.get("/api/rooms/{room_id}/reviews")
async def room_reviews(room_id: int, db=Depends(get_db)):
    await db.execute(
        "SELECT * FROM reviews WHERE room_id=%s AND status='approved' ORDER BY created_at DESC",
        (room_id,),
    )
    return await db.fetchall()


@app.post("/api/reviews")
async def create_review(req: ReviewIn, db=Depends(get_db)):
    if not 1 <= req.rating <= 5:
        raise HTTPException(400, "Rating must be 1–5")
    await db.execute(
        "INSERT INTO reviews (room_id,booking_id,guest_name,rating,review_text) VALUES (%s,%s,%s,%s,%s)",
        (req.room_id, req.booking_id, req.guest_name, req.rating, req.review_text),
    )
    return {"success": True, "message": "Review submitted for moderation"}


@app.get("/api/reviews")
async def all_reviews(status: Optional[str] = None, db=Depends(get_db), _=Depends(require_admin)):
    q = "SELECT r.*, rm.name AS room_name FROM reviews r JOIN rooms rm ON rm.id=r.room_id"
    params = ()
    if status:
        q += " WHERE r.status=%s"; params = (status,)
    q += " ORDER BY r.created_at DESC"
    await db.execute(q, params)
    return await db.fetchall()


@app.patch("/api/reviews/{rid}/status")
async def update_review(rid: int, data: dict, db=Depends(get_db), _=Depends(require_admin)):
    s = data.get("status")
    if s not in ("approved", "flagged", "pending"):
        raise HTTPException(400, "Invalid status")
    await db.execute("UPDATE reviews SET status=%s WHERE id=%s", (s, rid))
    if s == "approved":
        await db.execute("SELECT room_id FROM reviews WHERE id=%s", (rid,))
        row = await db.fetchone()
        if row:
            await db.execute(
                """UPDATE rooms SET
                   rating=(SELECT ROUND(AVG(rating),1) FROM reviews WHERE room_id=%s AND status='approved'),
                   review_count=(SELECT COUNT(*) FROM reviews WHERE room_id=%s AND status='approved')
                   WHERE id=%s""",
                (row["room_id"], row["room_id"], row["room_id"]),
            )
    return {"success": True}


@app.delete("/api/reviews/{rid}")
async def delete_review(rid: int, db=Depends(get_db), _=Depends(require_admin)):
    await db.execute("DELETE FROM reviews WHERE id=%s", (rid,))
    return {"success": True}


# ── CONTACT ───────────────────────────────────────────────────────
@app.post("/api/contact")
async def contact(req: ContactIn, db=Depends(get_db)):
    # Detect actual column names in contact_messages (old tables may differ)
    await db.execute("DESCRIBE `contact_messages`")
    cols = {row["Field"].lower() for row in await db.fetchall()}

    # Build insert with only columns that actually exist
    fields, values = [], []
    mapping = {
        "name": req.name, "email": req.email,
        "phone": req.phone, "subject": req.subject, "message": req.message,
        # handle legacy column name variants
        "sender_name": req.name, "sender_email": req.email,
        "msg": req.message, "body": req.message, "topic": req.subject,
    }
    seen_logical = set()
    logical_groups = [
        (["name","sender_name"],  req.name),
        (["email","sender_email"],req.email),
        (["phone"],               req.phone),
        (["subject","topic"],     req.subject),
        (["message","msg","body"],req.message),
    ]
    for candidates, value in logical_groups:
        for c in candidates:
            if c in cols:
                fields.append(f"`{c}`")
                values.append(value)
                break

    if not fields:
        raise HTTPException(500, "contact_messages table has unexpected schema")

    placeholders = ",".join(["%s"] * len(fields))
    await db.execute(
        f"INSERT INTO contact_messages ({','.join(fields)}) VALUES ({placeholders})",
        values,
    )
    return {"success": True, "message": "Message received. We'll respond within 1 hour."}


@app.get("/api/contact/messages")
async def list_messages(unread_only: bool = False, db=Depends(get_db), _=Depends(require_admin)):
    q = "SELECT * FROM contact_messages"
    if unread_only:
        q += " WHERE is_read=0"
    q += " ORDER BY created_at DESC"
    await db.execute(q)
    return await db.fetchall()


@app.patch("/api/contact/messages/{mid}/read")
async def mark_read(mid: int, db=Depends(get_db), _=Depends(require_admin)):
    await db.execute("UPDATE contact_messages SET is_read=1 WHERE id=%s", (mid,))
    return {"success": True}


# ── ADMIN STATS ───────────────────────────────────────────────────
@app.get("/api/admin/stats")
async def admin_stats(db=Depends(get_db), _=Depends(require_admin)):
    async def q(sql, p=()):
        await db.execute(sql, p)
        r = await db.fetchone()
        return list(r.values())[0] if r else 0

    return {
        "total_bookings":   await q("SELECT COUNT(*) FROM bookings"),
        "confirmed":        await q("SELECT COUNT(*) FROM bookings WHERE status='confirmed'"),
        "pending_bookings": await q("SELECT COUNT(*) FROM bookings WHERE status='pending'"),
        "total_revenue":    await q("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'"),
        "total_guests":     await q("SELECT COUNT(*) FROM users WHERE role='guest'"),
        "pending_reviews":  await q("SELECT COUNT(*) FROM reviews WHERE status='pending'"),
        "unread_messages":  await q("SELECT COUNT(*) FROM contact_messages WHERE is_read=0"),
        "available_rooms":  await q("SELECT COUNT(*) FROM rooms WHERE is_available=1"),
    }


@app.get("/api/admin/users")
async def list_users(db=Depends(get_db), _=Depends(require_admin)):
    await db.execute(
        "SELECT id,first_name,last_name,email,phone,role,is_active,created_at FROM users ORDER BY created_at DESC"
    )
    return await db.fetchall()


@app.patch("/api/admin/users/{uid}")
async def update_user(uid: int, data: dict, db=Depends(get_db), _=Depends(require_admin)):
    if "role" in data:
        if data["role"] not in ("guest", "admin"):
            raise HTTPException(400, "Invalid role")
        await db.execute("UPDATE users SET role=%s WHERE id=%s", (data["role"], uid))
    if "is_active" in data:
        await db.execute("UPDATE users SET is_active=%s WHERE id=%s", (int(bool(data["is_active"])), uid))
    return {"success": True}


# ── FIRST-RUN ADMIN SETUP ──────────────────────────────────────────
class AdminSetupIn(BaseModel):
    email: str
    setup_key: str   # must match ADMIN_SETUP_KEY in .env


@app.post("/api/admin/promote")
async def promote_to_admin(req: AdminSetupIn, db=Depends(get_db)):
    """
    One-time endpoint to promote an existing user to admin.
    Requires ADMIN_SETUP_KEY in your .env file.
    Usage: POST /api/admin/promote  {"email":"you@example.com","setup_key":"yourkey"}
    """
    expected = getenv("ADMIN_SETUP_KEY", "")
    if not expected:
        raise HTTPException(503, "ADMIN_SETUP_KEY not set in .env — add it to enable this endpoint")
    if req.setup_key != expected:
        raise HTTPException(403, "Invalid setup key")

    await db.execute("SELECT id, email, role FROM users WHERE email=%s", (req.email.lower(),))
    user = await db.fetchone()
    if not user:
        raise HTTPException(404, f"No user found with email: {req.email}")

    await db.execute("UPDATE users SET role='admin' WHERE id=%s", (user["id"],))
    return {"success": True, "message": f"{req.email} is now an admin. You can remove ADMIN_SETUP_KEY from .env."}