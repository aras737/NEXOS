from bot_commands import (
    ban,
    balance,
    clear,
    clear_warnings,
    daily,
    deposit,
    embed,
    help,
    invite,
    kick,
    kurulum,
    leaderboard,
    lock,
    pay,
    ping,
    role_add,
    role_remove,
    say,
    server,
    slowmode,
    timeout,
    unban,
    unlock,
    untimeout,
    user,
    warn,
    warnings,
    withdraw,
    work
)


COMMAND_MODULES = [
    help,
    invite,
    ping,
    server,
    user,
    balance,
    daily,
    work,
    deposit,
    withdraw,
    pay,
    leaderboard,
    clear,
    kick,
    ban,
    unban,
    timeout,
    untimeout,
    warn,
    warnings,
    clear_warnings,
    role_add,
    role_remove,
    lock,
    unlock,
    slowmode,
    say,
    embed,
    kurulum
]


def register_all_commands(bot):
    for module in COMMAND_MODULES:
        module.register(bot)
