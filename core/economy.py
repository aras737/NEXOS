import datetime
import random

from core.storage import load_economy, save_economy


DAILY_REWARD = 500
WORK_MIN_REWARD = 80
WORK_MAX_REWARD = 260
DAILY_COOLDOWN = datetime.timedelta(hours=24)
WORK_COOLDOWN = datetime.timedelta(minutes=30)

JOBS = [
    "sunucu reklam panosunu duzenledin",
    "NEXOS sistemlerini kontrol ettin",
    "moderasyon raporlarini toparladin",
    "ekonomi panelinde vardiya yaptin",
    "bot komutlarini test ettin"
]


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError:
        return None


def format_money(amount):
    return f"{amount:,} kredi".replace(",", ".")


def empty_account():
    return {
        "wallet": 0,
        "bank": 0,
        "daily_at": None,
        "work_at": None
    }


def guild_data(data, guild_id):
    guild_key = str(guild_id)
    data.setdefault(guild_key, {})
    return data[guild_key]


def account_data(data, guild_id, user_id):
    guild = guild_data(data, guild_id)
    user_key = str(user_id)
    guild.setdefault(user_key, empty_account())
    account = guild[user_key]
    account.setdefault("wallet", 0)
    account.setdefault("bank", 0)
    account.setdefault("daily_at", None)
    account.setdefault("work_at", None)
    return account


def get_account(guild_id, user_id):
    data = load_economy()
    return account_data(data, guild_id, user_id).copy()


def get_rank(guild_id, user_id):
    rows = get_leaderboard(guild_id)
    for index, row in enumerate(rows, start=1):
        if row["user_id"] == int(user_id):
            return index
    return None


def claim_daily(guild_id, user_id):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    last_claim = parse_time(account.get("daily_at"))
    current_time = now_utc()

    if last_claim and current_time - last_claim < DAILY_COOLDOWN:
        return False, DAILY_COOLDOWN - (current_time - last_claim), account.copy()

    account["wallet"] += DAILY_REWARD
    account["daily_at"] = current_time.isoformat()
    save_economy(data)
    return True, DAILY_REWARD, account.copy()


def work(guild_id, user_id):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    last_work = parse_time(account.get("work_at"))
    current_time = now_utc()

    if last_work and current_time - last_work < WORK_COOLDOWN:
        return False, WORK_COOLDOWN - (current_time - last_work), account.copy(), None

    reward = random.randint(WORK_MIN_REWARD, WORK_MAX_REWARD)
    account["wallet"] += reward
    account["work_at"] = current_time.isoformat()
    save_economy(data)
    return True, reward, account.copy(), random.choice(JOBS)


def deposit(guild_id, user_id, amount):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    if amount > account["wallet"]:
        return False, account.copy()

    account["wallet"] -= amount
    account["bank"] += amount
    save_economy(data)
    return True, account.copy()


def withdraw(guild_id, user_id, amount):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    if amount > account["bank"]:
        return False, account.copy()

    account["bank"] -= amount
    account["wallet"] += amount
    save_economy(data)
    return True, account.copy()


def transfer(guild_id, sender_id, receiver_id, amount):
    data = load_economy()
    sender = account_data(data, guild_id, sender_id)
    receiver = account_data(data, guild_id, receiver_id)

    if amount > sender["wallet"]:
        return False, sender.copy(), receiver.copy()

    sender["wallet"] -= amount
    receiver["wallet"] += amount
    save_economy(data)
    return True, sender.copy(), receiver.copy()


def add_money(guild_id, user_id, amount, target="wallet"):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    account[target] += amount
    save_economy(data)
    return account.copy()


def remove_money(guild_id, user_id, amount, target="wallet"):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    removed = min(amount, account[target])
    account[target] -= removed
    save_economy(data)
    return removed, account.copy()


def set_money(guild_id, user_id, wallet=None, bank=None):
    data = load_economy()
    account = account_data(data, guild_id, user_id)
    if wallet is not None:
        account["wallet"] = max(0, wallet)
    if bank is not None:
        account["bank"] = max(0, bank)
    save_economy(data)
    return account.copy()


def reset_account(guild_id, user_id):
    data = load_economy()
    guild = guild_data(data, guild_id)
    guild[str(user_id)] = empty_account()
    save_economy(data)
    return guild[str(user_id)].copy()


def get_leaderboard(guild_id, limit=10):
    data = load_economy()
    guild = guild_data(data, guild_id)
    rows = []

    for user_id, account in guild.items():
        wallet = int(account.get("wallet", 0))
        bank = int(account.get("bank", 0))
        rows.append({
            "user_id": int(user_id),
            "wallet": wallet,
            "bank": bank,
            "total": wallet + bank
        })

    rows.sort(key=lambda row: row["total"], reverse=True)
    return rows[:limit]


def remaining_text(delta):
    total_seconds = max(0, int(delta.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}s {minutes}d"
    if minutes:
        return f"{minutes}d {seconds}sn"
    return f"{seconds}sn"
