import discord
from discord.ext import commands
from database import guild_manager
from logger.logger_setup import get_logger
import asyncio

logger = get_logger(__name__, level=20)

class Forwarding(commands.Cog):
    """
    Cog for handling message forwarding based on guild-specific rules.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listen for messages and forward them if they match any rules.
        """
        if message.author.bot or not message.guild:
            return

        try:
            guild_settings = await guild_manager.get_guild_settings(str(message.guild.id))

            if not guild_settings.get("features", {}).get("forwarding_enabled", False):
                return

            rules = guild_settings.get("rules", [])
            if not rules:
                return

            for rule in rules:
                if not rule.get("is_active") or str(rule.get("source_channel_id")) != str(message.channel.id):
                    continue

                # Check daily message limit
                daily_limit = guild_settings.get("limits", {}).get("daily_messages", 100)
                daily_count = await guild_manager.get_daily_message_count(str(message.guild.id))
                if daily_count >= daily_limit:
                    if guild_settings.get("features", {}).get("notify_on_error", True):
                        await message.channel.send(f"Daily message forwarding limit of {daily_limit} reached.", delete_after=60)
                    continue # Stop processing this rule

                if await self.process_rule(rule, message, guild_settings):
                    # Log forwarded message
                    log_data = {
                        "guild_id": str(message.guild.id),
                        "rule_id": rule.get("rule_id"),
                        "source_channel_id": str(message.channel.id),
                        "destination_channel_id": str(rule.get("destination_channel_id")),
                        "original_message_id": str(message.id),
                        "success": True
                    }
                    await guild_manager.log_forwarded_message(log_data)


        except Exception as e:
            logger.error(f"Error in on_message for guild {message.guild.id}: {e}", exc_info=True)

    async def process_rule(self, rule: dict, message: discord.Message, guild_settings: dict) -> bool:
        """
        Process a single rule against a message.
        Returns True if forwarded, False otherwise.
        """
        settings = rule.get("settings", {})
        if not self.check_message_type(settings.get("message_types", {}), message):
            return False

        if not self.check_filters(settings.get("filters", {}), message, settings.get("advanced_options", {})):
            return False

        destination_channel_id = rule.get("destination_channel_id")
        destination_channel = self.bot.get_channel(int(destination_channel_id))

        if not destination_channel:
            logger.warning(f"Destination channel {destination_channel_id} not found for rule {rule.get('rule_id')}")
            return False

        await self.forward_message(settings.get("formatting", {}), message, destination_channel)
        return True

    def check_message_type(self, message_types: dict, message: discord.Message) -> bool:
        """Check if the message type is allowed by the rule."""
        if message.content and message_types.get("text", False):
            return True
        if message.attachments and message_types.get("media", False): # Simplified: media covers general attachments
            return True
        if message.attachments and message_types.get("files", False):
            return True
        if message.embeds and message_types.get("embeds", False):
            return True
        if message.stickers and message_types.get("stickers", False):
            return True
        if "http" in message.content and message_types.get("links", False): # simple link check
            return True
        # If message content is empty, but there is something else, we should not block it if text is not required.
        if not message.content:
            return True

        return False


    def check_filters(self, filters: dict, message: discord.Message, advanced: dict) -> bool:
        """Check keyword and length filters."""
        content = message.content
        case_sensitive = advanced.get("case_sensitive", False)
        whole_word = advanced.get("whole_word_only", False)

        if not case_sensitive:
            content = content.lower()

        # Length filters
        min_len = filters.get("min_length", 0)
        max_len = filters.get("max_length", 2000)
        if not (min_len <= len(message.content) <= max_len):
            return False

        # Keyword filters
        require_keywords = filters.get("require_keywords", [])
        block_keywords = filters.get("block_keywords", [])

        if not case_sensitive:
            require_keywords = [k.lower() for k in require_keywords]
            block_keywords = [k.lower() for k in block_keywords]

        if whole_word:
            words = content.split()
            if block_keywords and any(word in block_keywords for word in words):
                return False
            if require_keywords and not any(word in require_keywords for word in words):
                return False
        else:
            if block_keywords and any(keyword in content for keyword in block_keywords):
                return False
            if require_keywords and not any(keyword in content for keyword in require_keywords):
                return False

        return True

    async def forward_message(self, formatting: dict, message: discord.Message, destination: discord.TextChannel):
        """Construct and send the forwarded message."""
        content_parts = []
        embeds_to_send = []
        files_to_send = []

        # Prefix
        if prefix := formatting.get("add_prefix"):
            content_parts.append(prefix)

        # Author
        if formatting.get("include_author", True):
            content_parts.append(f"**From {message.author.mention}:**")

        # Message content
        if message.content:
            content_parts.append(message.content)

        # Suffix
        if suffix := formatting.get("add_suffix"):
            content_parts.append(suffix)

        final_content = "\n".join(content_parts)

        # Embeds
        if formatting.get("forward_embeds", True) and message.embeds:
            embeds_to_send.extend(message.embeds)

        # Attachments
        if formatting.get("forward_attachments", True) and message.attachments:
            for attachment in message.attachments:
                try:
                    # This can fail if the attachment is too large or bot is rate limited
                    f = await attachment.to_file()
                    files_to_send.append(f)
                except discord.HTTPException as e:
                    logger.warning(f"Failed to forward attachment {attachment.filename}: {e}")
                    final_content += f"\n(Attachment failed to forward: {attachment.filename})"


        # Send the message
        try:
            await destination.send(content=final_content if final_content else None, embeds=embeds_to_send, files=files_to_send, reference=message)
        except discord.HTTPException as e:
            logger.error(f"Failed to send forwarded message to {destination.id}: {e}")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(Forwarding(bot))
    logger.info("Forwarding cog loaded.")
