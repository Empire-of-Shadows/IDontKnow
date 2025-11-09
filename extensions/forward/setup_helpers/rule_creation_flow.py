"""
Manages the interactive flow for creating a new forwarding rule.
"""
import discord
from typing import Optional, Tuple

from ..models.setup_state import SetupState
from .channel_select import channel_selector
from .state_manager import state_manager


class RuleCreationFlow:
    """Handles the step-by-step process of creating a forwarding rule."""

    def __init__(self, bot):
        self.bot = bot

    async def start_rule_creation(self, interaction: discord.Interaction, session: SetupState):
        """Start the rule creation flow."""
        # Initialize a new rule in the session
        session.current_rule = {
            "step": "source_channel"
        }
        await state_manager.update_session(interaction.guild_id, {
            "current_rule": session.current_rule
        })
        await self.show_source_channel_step(interaction, session)

    async def show_source_channel_step(self, interaction: discord.Interaction, session: SetupState):
        """Show the source channel selection step."""
        embed = await channel_selector.create_channel_embed(interaction.guild, "source_channel")
        view = await channel_selector.create_channel_select_menu(
            interaction.guild, "text", "rule_source_select"
        )

        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if "already been acknowledged" in str(e).lower():
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except discord.HTTPException:
                    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                raise e

    async def show_destination_channel_step(self, interaction: discord.Interaction, session: SetupState):
        """Show the destination channel selection step."""
        embed = await channel_selector.create_channel_embed(interaction.guild, "destination_channel")
        view = await channel_selector.create_channel_select_menu(
            interaction.guild, "text", "rule_dest_select"
        )

        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if "already been acknowledged" in str(e).lower():
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except discord.HTTPException:
                    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                raise e

    async def handle_channel_selection(self, interaction: discord.Interaction, session: SetupState, channel_type: str,
                                       channel_id: int):
        """Handle channel selection for source or destination."""
        is_valid, message = await channel_selector.validate_channel_access(interaction.guild, channel_id)

        if not is_valid:
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(f"❌ {message}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {message}", ephemeral=True)
            except discord.HTTPException as e:
                if "already been acknowledged" in str(e).lower():
                    await interaction.followup.send(f"❌ {message}", ephemeral=True)
                else:
                    raise e
            return

        if channel_type == "source":
            session.current_rule["source_channel_id"] = channel_id
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(
                        f"✅ Source channel set to {interaction.guild.get_channel(channel_id).mention}", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"✅ Source channel set to {interaction.guild.get_channel(channel_id).mention}", ephemeral=True)
            except discord.HTTPException as e:
                if "already been acknowledged" in str(e).lower():
                    await interaction.followup.send(
                        f"✅ Source channel set to {interaction.guild.get_channel(channel_id).mention}", ephemeral=True)
                else:
                    raise e
            await self.show_destination_channel_step(interaction, session)
        elif channel_type == "destination":
            session.current_rule["destination_channel_id"] = channel_id
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(
                        f"✅ Destination channel set to {interaction.guild.get_channel(channel_id).mention}",
                        ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"✅ Destination channel set to {interaction.guild.get_channel(channel_id).mention}",
                        ephemeral=True)
            except discord.HTTPException as e:
                if "already been acknowledged" in str(e).lower():
                    await interaction.followup.send(
                        f"✅ Destination channel set to {interaction.guild.get_channel(channel_id).mention}",
                        ephemeral=True)
                else:
                    raise e
            await self.show_rule_name_step(interaction, session)

    async def show_rule_name_modal(self, interaction: discord.Interaction, session: SetupState, callback):
        """Show the rule name modal."""
        await callback(interaction, session)

    async def show_rule_name_step(self, interaction: discord.Interaction, session: SetupState):
        """Show the rule name input step."""
        embed = discord.Embed(
            title="📝 Rule Name",
            description="Please provide a name for this rule.",
            color=discord.Color.blue()
        )
        from ..setup_helpers.button_manager import button_manager
        view = button_manager.create_button_row([
            {
                "label": "Enter Name",
                "style": discord.ButtonStyle.primary,
                "custom_id": "rule_name_input"
            },
            {
                "label": "Use Auto-generated Name",
                "style": discord.ButtonStyle.secondary,
                "custom_id": "rule_auto_name"
            }
        ])

        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if "already been acknowledged" in str(e).lower():
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except discord.HTTPException:
                    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                raise e

    async def handle_auto_name(self, interaction: discord.Interaction, session: SetupState):
        """Handle auto-naming the rule."""
        source_channel = interaction.guild.get_channel(session.current_rule["source_channel_id"])
        dest_channel = interaction.guild.get_channel(session.current_rule["destination_channel_id"])
        rule_name = f"Forward from #{source_channel.name} to #{dest_channel.name}"
        session.current_rule["rule_name"] = rule_name
        await self.show_rule_preview_step(interaction, session)

    async def show_rule_preview_step(self, interaction: discord.Interaction, session: SetupState):
        """Show a preview of the rule before creation."""
        from .rule_setup import rule_setup_helper
        rule = await rule_setup_helper.create_initial_rule(
            source_channel_id=session.current_rule["source_channel_id"],
            destination_channel_id=session.current_rule["destination_channel_id"],
            rule_name=session.current_rule["rule_name"]
        )
        embed = await rule_setup_helper.create_rule_preview_embed(rule, interaction.guild)
        from ..setup_helpers.button_manager import button_manager
        view = button_manager.create_button_row([
            {
                "label": "Create Rule",
                "style": discord.ButtonStyle.success,
                "custom_id": "rule_final_create"
            },
            {
                "label": "Edit Settings",
                "style": discord.ButtonStyle.secondary,
                "custom_id": "rule_edit_settings"
            },
            {
                "label": "Start Over",
                "style": discord.ButtonStyle.danger,
                "custom_id": "rule_start_over"
            }
        ])

        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if "already been acknowledged" in str(e).lower():
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except discord.HTTPException:
                    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                raise e

    async def create_final_rule(self, interaction: discord.Interaction, session: SetupState) -> Tuple[bool, str]:
        """Create the final rule and add it to the session."""
        from .rule_setup import rule_setup_helper
        rule = await rule_setup_helper.create_initial_rule(
            source_channel_id=session.current_rule["source_channel_id"],
            destination_channel_id=session.current_rule["destination_channel_id"],
            rule_name=session.current_rule["rule_name"]
        )
        is_valid, errors = await rule_setup_helper.validate_rule_configuration(rule, interaction.guild)
        if not is_valid:
            return False, " ".join(errors)

        session.forwarding_rules.append(rule)
        await state_manager.update_session(interaction.guild_id, {
            "forwarding_rules": session.forwarding_rules
        })
        return True, "Rule created successfully."

    async def handle_rule_back(self, interaction: discord.Interaction, session: SetupState, step: str):
        """Handle back navigation within rule creation."""
        if step == "source":
            # Go back to the first rule step
            from ..setup import SetupCog
            setup_cog = SetupCog(self.bot)
            await setup_cog.show_first_rule_step(interaction, session)
        elif step == "destination":
            await self.show_source_channel_step(interaction, session)
        elif step == "name":
            await self.show_destination_channel_step(interaction, session)
        elif step == "preview":
            await self.show_rule_name_step(interaction, session)
        else:
            # Default back to source channel
            await self.show_source_channel_step(interaction, session)

rule_creation_flow = RuleCreationFlow(None)