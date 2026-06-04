import json
from pathlib import Path


DATA_DIR = Path("data")
WARNINGS_FILE = DATA_DIR / "warnings.json"


def load_warnings():
    if not WARNINGS_FILE.exists():
        return {}
    with WARNINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_warnings(data):
    DATA_DIR.mkdir(exist_ok=True)
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
