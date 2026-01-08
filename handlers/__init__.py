from .start import register_handlers
from .group_commands import register_group_commands

def register_all_handlers(app):
    register_handlers(app)
    register_group_commands(app)
    print("✅ Group commands registered!")
