import motor.motor_asyncio
from config import MONGO_URI, DB_NAME
import logging
import sys
from datetime import datetime, timedelta

# ==========================================================
# LOGGING
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)

# ==========================================================
# MONGO CONNECTION
# ==========================================================
client = None
db = None

if not MONGO_URI:
    logging.error("❌ MONGO_URI empty hai! config.py check karo.")
    sys.exit(1)

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    logging.info("✅ MongoDB connected successfully!")
except Exception as e:
    logging.error(f"❌ MongoDB connection failed: {e}")
    sys.exit(1)

# ==========================================================
# 👋 WELCOME SYSTEM
# ==========================================================
async def set_welcome_message(chat_id, text: str):
    await db.welcome.update_one(
        {"chat_id": chat_id},
        {"$set": {"message": text}},
        upsert=True
    )

async def get_welcome_message(chat_id):
    data = await db.welcome.find_one({"chat_id": chat_id})
    return data.get("message") if data else None

async def set_welcome_status(chat_id, status: bool):
    await db.welcome.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )

async def get_welcome_status(chat_id) -> bool:
    data = await db.welcome.find_one({"chat_id": chat_id})
    return bool(data.get("enabled", True)) if data else True

# ==========================================================
# 🔒 LOCK SYSTEM
# ==========================================================
async def set_lock(chat_id, lock_type, status: bool):
    await db.locks.update_one(
        {"chat_id": chat_id},
        {"$set": {f"locks.{lock_type}": status}},
        upsert=True
    )

async def get_locks(chat_id):
    data = await db.locks.find_one({"chat_id": chat_id})
    return data.get("locks", {}) if data else {}

# ==========================================================
# ⚠️ WARN SYSTEM
# ==========================================================
async def add_warn(chat_id: int, user_id: int) -> int:
    data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
    count = data.get("count", 0) + 1 if data else 1

    await db.warns.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"count": count}},
        upsert=True
    )
    return count

async def get_warns(chat_id: int, user_id: int) -> int:
    data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
    return data.get("count", 0) if data else 0

async def reset_warns(chat_id: int, user_id: int):
    await db.warns.delete_one({"chat_id": chat_id, "user_id": user_id})

# ==========================================================
# 👤 USER SYSTEM (Broadcast)
# ==========================================================
async def add_user(user_id: int, first_name: str):
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"first_name": first_name}},
        upsert=True
    )

async def get_all_users():
    cursor = db.users.find({}, {"_id": 0, "user_id": 1})
    return [doc["user_id"] async for doc in cursor if "user_id" in doc]

# ==========================================================
# 🛡️ ANTI-CHEATER SETTINGS
# ==========================================================
async def set_anticheater(chat_id: int, status: bool):
    await db.anticheater_settings.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )

async def get_anticheater(chat_id: int) -> bool:
    data = await db.anticheater_settings.find_one({"chat_id": chat_id})
    return bool(data.get("enabled", False)) if data else False

# ==========================================================
# 👮 ADMIN ACTION COUNTER (BAN + KICK)
# ==========================================================
ANTI_LIMIT_HOURS = 24

async def add_admin_action(chat_id: int, admin_id: int) -> int:
    now = datetime.utcnow()

    data = await db.admin_actions.find_one(
        {"chat_id": chat_id, "admin_id": admin_id}
    )

    # First action or expired window
    if not data or now - data["last_reset"] > timedelta(hours=ANTI_LIMIT_HOURS):
        await db.admin_actions.update_one(
            {"chat_id": chat_id, "admin_id": admin_id},
            {"$set": {"count": 1, "last_reset": now}},
            upsert=True
        )
        return 1

    # Increment count
    new_count = data["count"] + 1
    await db.admin_actions.update_one(
        {"chat_id": chat_id, "admin_id": admin_id},
        {"$set": {"count": new_count}}
    )
    return new_count

async def reset_admin(chat_id: int, admin_id: int):
    await db.admin_actions.delete_one(
        {"chat_id": chat_id, "admin_id": admin_id}
    )

# ==========================================================
# 🧹 CLEANUP (Optional)
# ==========================================================
async def clear_group_data(chat_id: int):
    await db.welcome.delete_one({"chat_id": chat_id})
    await db.locks.delete_one({"chat_id": chat_id})
    await db.warns.delete_many({"chat_id": chat_id})
    await db.anticheater_settings.delete_one({"chat_id": chat_id})
    await db.admin_actions.delete_many({"chat_id": chat_id})
        upsert=True
    )

async def get_anticheater(chat_id: int) -> bool:
    """Check karne ke liye ki anti-cheater on hai ya nahi"""
    data = await db.anticheater_settings.find_one({"chat_id": chat_id})
    return data.get("enabled", False) if data else False

async def add_admin_action(chat_id: int, admin_id: int) -> int:
    """Admin ke actions (ban/kick) ko count karne ke liye"""
    data = await db.admin_actions.find_one_and_update(
        {"chat_id": chat_id, "admin_id": admin_id},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )
    return data.get("count", 0)

async def reset_admin(chat_id: int, admin_id: int):
    """Admin ke actions reset karne ke liye"""
    await db.admin_actions.delete_one({"chat_id": chat_id, "admin_id": admin_id})
    
