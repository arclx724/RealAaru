import motor.motor_asyncio
from config import MONGO_URI, DB_NAME
import logging

# setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    logging.info("✅ MongoDB connected successfully!")
except Exception as e:
    logging.error(f"❌ Failed to connect to MongoDB: {e}")

# ==========================================================
# 🟢 WELCOME MESSAGE SYSTEM
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
    if not data:  # default ON
        return True
    return bool(data.get("enabled", True))

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
    warns = data.get("count", 0) + 1 if data else 1

    await db.warns.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"count": warns}},
        upsert=True
    )
    return warns

async def get_warns(chat_id: int, user_id: int) -> int:
    data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
    return data.get("count", 0) if data else 0

async def reset_warns(chat_id: int, user_id: int):
    await db.warns.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"count": 0}},
        upsert=True
    )

# ==========================================================
# 🧹 CLEANUP UTILS (Optional)
# ==========================================================

async def clear_group_data(chat_id: int):
    await db.welcome.delete_one({"chat_id": chat_id})
    await db.locks.delete_one({"chat_id": chat_id})
    await db.warns.delete_many({"chat_id": chat_id})


# ==========================================================
# 👤 USER SYSTEM (for broadcast)
# ==========================================================
async def add_user(user_id, first_name):
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"first_name": first_name}},
        upsert=True
    )

async def get_all_users():
    cursor = db.users.find({}, {"_id": 0, "user_id": 1})
    users = []
    async for document in cursor:
        # Make sure the document has 'user_id'
        if "user_id" in document:
            users.append(document["user_id"])
    return users

# ==========================================================
# 🛡️ ANTI-CHEATER SYSTEM
# ==========================================================

async def set_anticheater(chat_id: int, status: bool):
    """Anti-cheater mode ko on ya off karne ke liye"""
    await db.anticheater_settings.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )

async def get_anticheater(chat_id: int) -> bool:
    """Check karne ke liye ki anti-cheater on hai ya nahi"""
    data = await db.anticheater_settings.find_one({"chat_id": chat_id})
    return data.get("enabled", False) if data else False

async def add_admin_action(chat_id: int, admin_id: int) -> int:
    """Admin ke actions (ban/kick) ko count karne ke liye"""
    # Action count badhane ke liye $inc ka use karein
    data = await db.admin_actions.find_one_and_update(
        {"chat_id": chat_id, "admin_id": admin_id},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )
    return data.get("count", 0)

async def reset_admin(chat_id: int, admin_id: int):
    """Admin ke actions reset karne ke liye (jab wo demote ho jaye)"""
    await db.admin_actions.delete_one({"chat_id": chat_id, "admin_id": admin_id})
    
