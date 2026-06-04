from bot_commands import (
    ban,
    clear,
    clear_warnings,
    embed,
    help,
    kick,
    kurulum,
    lock,
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
    warnings
)


COMMAND_MODULES = [
    help,
    ping,
    server,
    user,
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
