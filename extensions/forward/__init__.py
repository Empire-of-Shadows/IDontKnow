"""
Message Forwarding extension for Discord bot.
"""
from .setup import SetupCog

async def setup(bot):
    """Setup function for the forward extension."""
    await bot.add_cog(SetupCog(bot))