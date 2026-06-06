import json
import shutil
import datetime
from pathlib import Path

from core.config import NEXOS_DATA_DIR


LEGACY_DATA_DIR = Path("data")
DATA_DIR = NEXOS_DATA_DIR
WARNINGS_FILE = DATA_DIR / "warnings.json"
ECONOMY_FILE = DATA_DIR / "economy.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOGS_FILE = DATA_DIR / "logs.jsonl"
TICKETS_FILE = DATA_DIR / "tickets.json"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
LEGACY_WARNINGS_FILE = LEGACY_DATA_DIR / "warnings.json"


def migrate_legacy_warnings():
    if WARNINGS_FILE.exists() or not LEGACY_WARNINGS_FILE.exists():
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LEGACY_WARNINGS_FILE, WARNINGS_FILE)


def load_warnings():
    migrate_legacy_warnings()
    if not WARNINGS_FILE.exists():
        return {}
    with WARNINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_warnings(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with WARNINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def add_warning(guild_id, user_id, warning):
    data = load_warnings()
    guild_key = str(guild_id)
    user_key = str(user_id)
    data.setdefault(guild_key, {})
    data[guild_key].setdefault(user_key, [])
    data[guild_key][user_key].append(warning)
    save_warnings(data)
    return data[guild_key][user_key]


def get_warnings(guild_id, user_id):
    data = load_warnings()
    return data.get(str(guild_id), {}).get(str(user_id), [])


def clear_user_warnings(guild_id, user_id):
    data = load_warnings()
    guild_key = str(guild_id)
    user_key = str(user_id)
    if guild_key in data and user_key in data[guild_key]:
        data[guild_key][user_key] = []
        save_warnings(data)


def load_economy():
    if not ECONOMY_FILE.exists():
        return {}
    with ECONOMY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_economy(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with ECONOMY_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_settings():
    if not SETTINGS_FILE.exists():
        return {}
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_settings(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_guild_setting(guild_id, key, default=None):
    data = load_settings()
    return data.get(str(guild_id), {}).get(key, default)


def set_guild_setting(guild_id, key, value):
    data = load_settings()
    guild_key = str(guild_id)
    data.setdefault(guild_key, {})
    data[guild_key][key] = value
    save_settings(data)


def append_log(event):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOGS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_tickets():
    if not TICKETS_FILE.exists():
        return {}
    with TICKETS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_tickets(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with TICKETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def guild_tickets(data, guild_id):
    guild_key = str(guild_id)
    data.setdefault(guild_key, {})
    return data[guild_key]


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def create_ticket_record(guild_id, channel_id, owner_id, subject, details="", priority="normal"):
    data = load_tickets()
    tickets = guild_tickets(data, guild_id)
    tickets[str(channel_id)] = {
        "owner_id": int(owner_id),
        "subject": subject,
        "details": details,
        "priority": priority,
        "status": "open",
        "claimed_by": None,
        "added_users": [],
        "created_at": now_iso(),
        "closed_at": None,
        "close_reason": None
    }
    save_tickets(data)
    return tickets[str(channel_id)]


def get_ticket_record(guild_id, channel_id):
    data = load_tickets()
    return data.get(str(guild_id), {}).get(str(channel_id))


def update_ticket_record(guild_id, channel_id, **updates):
    data = load_tickets()
    ticket = data.get(str(guild_id), {}).get(str(channel_id))
    if not ticket:
        return None

    ticket.update(updates)
    save_tickets(data)
    return ticket


def close_ticket_record(guild_id, channel_id, reason="Sebep belirtilmedi"):
    data = load_tickets()
    ticket = data.get(str(guild_id), {}).get(str(channel_id))
    if ticket:
        ticket["status"] = "closed"
        ticket["closed_at"] = now_iso()
        ticket["close_reason"] = reason
        save_tickets(data)
    return ticket


def find_open_ticket_for_user(guild_id, owner_id):
    data = load_tickets()
    tickets = data.get(str(guild_id), {})
    for channel_id, ticket in tickets.items():
        if ticket.get("owner_id") == int(owner_id) and ticket.get("status") == "open":
            return int(channel_id), ticket
    return None, None


def add_ticket_user(guild_id, channel_id, user_id):
    ticket = get_ticket_record(guild_id, channel_id)
    if not ticket:
        return None
    users = ticket.setdefault("added_users", [])
    if int(user_id) not in users:
        users.append(int(user_id))
    return update_ticket_record(guild_id, channel_id, added_users=users)


def remove_ticket_user(guild_id, channel_id, user_id):
    ticket = get_ticket_record(guild_id, channel_id)
    if not ticket:
        return None
    users = [item for item in ticket.get("added_users", []) if int(item) != int(user_id)]
    return update_ticket_record(guild_id, channel_id, added_users=users)


def transcript_path(guild_id, channel_id):
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    return TRANSCRIPTS_DIR / f"{guild_id}-{channel_id}-{now_iso().replace(':', '-')}.txt"
