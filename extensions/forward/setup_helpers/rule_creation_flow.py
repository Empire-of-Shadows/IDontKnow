"""
Interactive rule creation flow for setup wizard.
"""
from typing import Dict, Any, Optional, Tuple
import discord

from .state_manager import state_manager
from .channel_select import channel_selector
from .rule_setup import rule_setup_helper
from .button_manager import button_manager


class RuleCreationFlow:
    """Handles the interactive rule creation process."""

    async def start_rule_creation(self, interaction: discord.Interaction, session):
        """Start the rule creation process."""
        # Initialize current rule if not exists
        if not session.current_rule:
            session.current_rule = {
                "step": "source_channel",
                "source_channel_id": None,
                "destination_channel_id": None,
                "rule_name": None
            }

        # Show the appropriate step based on current progress
        current_step = session.current_rule.get("step", "source_channel")

        if current_step == "source_channel":
            await self.show_source_channel_step(interaction, session)
        elif current_step == "destination_channel":
            await self.show_destination_channel_step(interaction, session)
        elif current_step == "rule_name":
            await self.show_rule_name_step(interaction, session)
        elif current_step == "rule_preview":
            await self.show_rule_preview_step(interaction, session)

    async def show_source_channel_step(self, interaction: discord.Interaction, session):
        """Show source channel selection step."""
        embed = await channel_selector.create_channel_embed(interaction.guild, "source_channel")

        embed.title = "🔄 Step 1: Select Source Channel"
        embed.add_field(
            name="📝 What's a source channel?",
            value="This is the channel I'll watch for messages to forward.",
            inline=False
        )

        # Create channel selection menu
        view = await channel_selector.create_channel_select_menu(
            interaction.guild,
            "text",
            "rule_source_select"
        )

        # Update buttons for rule flow
        view = await self._modify_view_for_rule_flow(view, session, "source_channel")

        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

        # Update session
        await state_manager.update_session(interaction.guild_id, {
            "current_rule": session.current_rule
        })

    async def show_destination_channel_step(self, interaction: discord.Interaction, session):
        """Show destination channel selection step."""
        embed = await channel_selector.create_channel_embed(interaction.guild, "destination_channel")

        embed.title = "🔄 Step 2: Select Destination Channel"

        # Show selected source channel
        source_channel = interaction.guild.get_channel(session.current_rule["source_channel_id"])
        if source_channel:
            embed.add_field(
                name="✅ Source Channel",
                value=source_channel.mention,
                inline=True
            )

        embed.add_field(
            name="📝 What's a destination channel?",
            value="This is where I'll forward messages from the source channel.",
            inline=False
        )

        # Create channel selection menu
        view = await channel_selector.create_channel_select_menu(
            interaction.guild,
            "text",
            "rule_dest_select"
        )

        # Update buttons for rule flow
        view = await self._modify_view_for_rule_flow(view, session, "destination_channel")

        await interaction.response.edit_message(embed=embed, view=view)

        # Update session
        await state_manager.update_session(interaction.guild_id, {
            "current_rule": session.current_rule
        })

    async def show_rule_name_step(self, interaction: discord.Interaction, session):
        """Show rule naming step."""
        source_channel = interaction.guild.get_channel(session.current_rule["source_channel_id"])
        dest_channel = interaction.guild.get_channel(session.current_rule["destination_channel_id"])

        embed = discord.Embed(
            title="🔄 Step 3: Name Your Rule",
            color=discord.Color.blue()
        )

        embed.description = (
            "Give your forwarding rule a descriptive name so you can easily identify it later.\n\n"
            "**Examples:**\n"
            "• 'Announcements to Archive'\n"
            "• 'General to Crosspost'\n"
            "• 'Support Questions to Staff'\n"
        )

        # Show channel selections
        embed.add_field(
            name="🔍 Source",
            value=source_channel.mention if source_channel else "Unknown",
            inline=True
        )

        embed.add_field(
            name="📤 Destination",
            value=dest_channel.mention if dest_channel else "Unknown",
            inline=True
        )

        # Create view with modal trigger button
        view = discord.ui.View(timeout=1800)

        # Button to open name input modal
        name_button = discord.ui.Button(
            label="Enter Rule Name",
            style=discord.ButtonStyle.primary,
            custom_id="rule_name_input",
            emoji="📝"
        )
        name_button.callback = self._create_name_modal_callback()
        view.add_item(name_button)

        # Navigation buttons
        view.add_item(discord.ui.Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="rule_name_back",
            emoji="⬅️"
        ))

        view.add_item(discord.ui.Button(
            label="Use Auto-Name",
            style=discord.ButtonStyle.secondary,
            custom_id="rule_auto_name",
            emoji="🤖"
        ))

        view.add_item(discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.danger,
            custom_id="rule_name_cancel",
            emoji="✖️"
        ))

        await interaction.response.edit_message(embed=embed, view=view)

        # Update session
        await state_manager.update_session(interaction.guild_id, {
            "current_rule": session.current_rule
        })

    async def show_rule_preview_step(self, interaction: discord.Interaction, session):
        """Show rule preview and confirmation step."""
        # Create the full rule configuration
        rule = await rule_setup_helper.create_initial_rule(
            session.current_rule["source_channel_id"],
            session.current_rule["destination_channel_id"],
            session.current_rule["rule_name"]
        )

        # Validate the rule
        is_valid, errors = await rule_setup_helper.validate_rule_configuration(rule, interaction.guild)

        # Create preview embed
        embed = await rule_setup_helper.create_rule_preview_embed(rule, interaction.guild)
        embed.title = "🔄 Step 4: Review Your Rule"

        if not is_valid:
            embed.color = discord.Color.red()
            embed.add_field(
                name="❌ Validation Errors",
                value="\n".join(f"• {error}" for error in errors),
                inline=False
            )

        # Add action instructions
        if is_valid:
            embed.add_field(
                name="✅ Ready to Create!",
                value="Click 'Create Rule' to save this forwarding rule.",
                inline=False
            )
        else:
            embed.add_field(
                name="🛠️ Needs Fixing",
                value="Please go back and fix the issues above.",
                inline=False
            )

        # Create action buttons
        view = discord.ui.View(timeout=1800)

        if is_valid:
            view.add_item(discord.ui.Button(
                label="Create Rule",
                style=discord.ButtonStyle.success,
                custom_id="rule_final_create",
                emoji="✅"
            ))

        view.add_item(discord.ui.Button(
            label="Edit Rule",
            style=discord.ButtonStyle.primary,
            custom_id="rule_edit_settings",
            emoji="⚙️"
        ))

        view.add_item(discord.ui.Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="rule_preview_back",
            emoji="⬅️"
        ))

        view.add_item(discord.ui.Button(
            label="Start Over",
            style=discord.ButtonStyle.secondary,
            custom_id="rule_start_over",
            emoji="🔄"
        ))

        await interaction.response.edit_message(embed=embed, view=view)

        # Update session with full rule
        session.current_rule = rule
        session.current_rule["step"] = "rule_preview"
        await state_manager.update_session(interaction.guild_id, {
            "current_rule": session.current_rule
        })

    async def _modify_view_for_rule_flow(self, original_view: discord.ui.View, session,
                                         current_step: str) -> discord.ui.View:
        """Modify a channel selection view for rule creation flow."""
        # Remove existing navigation buttons and add rule-specific ones
        new_view = discord.ui.View(timeout=1800)

        # Keep the select menu
        for item in original_view.children:
            if isinstance(item, discord.ui.Select):
                new_view.add_item(item)
                break

        # Add rule-specific navigation
        if current_step == "source_channel":
            # Only continue if source channel is selected
            has_source = session.current_rule.get("source_channel_id") is not None

            continue_button = discord.ui.Button(
                label="Continue",
                style=discord.ButtonStyle.success,
                custom_id="rule_source_continue",
                emoji="➡️",
                disabled=not has_source
            )
            new_view.add_item(continue_button)

        elif current_step == "destination_channel":
            # Only continue if destination channel is selected
            has_dest = session.current_rule.get("destination_channel_id") is not None

            continue_button = discord.ui.Button(
                label="Continue",
                style=discord.ButtonStyle.success,
                custom_id="rule_dest_continue",
                emoji="➡️",
                disabled=not has_dest
            )
            new_view.add_item(continue_button)

        # Add back button
        back_button = discord.ui.Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id=f"rule_{current_step}_back",
            emoji="⬅️"
        )
        new_view.add_item(back_button)

        # Add cancel button
        cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.danger,
            custom_id=f"rule_{current_step}_cancel",
            emoji="✖️"
        )
        new_view.add_item(cancel_button)

        return new_view

    def _create_name_modal_callback(self):
        """Create callback for rule name modal."""

        async def modal_callback(interaction: discord.Interaction):
            # This will be handled by the modal submission
            await interaction.response.defer()

        return modal_callback

    async def handle_channel_selection(self, interaction: discord.Interaction, session, channel_type: str,
                                       channel_id: int):
        """Handle channel selection during rule creation."""
        # Validate channel access
        is_valid, message = await channel_selector.validate_channel_access(interaction.guild, channel_id)

        if not is_valid:
            await interaction.response.send_message(
                f"❌ {message}",
                ephemeral=True
            )
            return

        # Update session with selected channel
        session.current_rule[f"{channel_type}_channel_id"] = channel_id

        # Show confirmation
        channel = interaction.guild.get_channel(channel_id)
        await interaction.response.send_message(
            f"✅ Selected {channel.mention} as {channel_type.replace('_', ' ')}.",
            ephemeral=True
        )

        # Refresh the current step to update button states
        current_step = session.current_rule.get("step")
        if current_step == "source_channel":
            await self.show_source_channel_step(interaction, session)
        elif current_step == "destination_channel":
            await self.show_destination_channel_step(interaction, session)

    async def handle_auto_name(self, interaction: discord.Interaction, session):
        """Generate an automatic rule name."""
        source_channel = interaction.guild.get_channel(session.current_rule["source_channel_id"])
        dest_channel = interaction.guild.get_channel(session.current_rule["destination_channel_id"])

        if source_channel and dest_channel:
            auto_name = f"Forward from #{source_channel.name} to #{dest_channel.name}"
            session.current_rule["rule_name"] = auto_name
            session.current_rule["step"] = "rule_preview"

            await interaction.response.send_message(
                f"✅ Using automatic name: `{auto_name}`",
                ephemeral=True
            )

            await self.show_rule_preview_step(interaction, session)
        else:
            await interaction.response.send_message(
                "❌ Could not generate automatic name. Please select channels first.",
                ephemeral=True
            )

    async def create_final_rule(self, interaction: discord.Interaction, session) -> Tuple[bool, str]:
        """Create the final rule in the database."""
        try:
            # Todo: Save rule to database
            # This will use the database manager to create the forwarding rule

            rule_data = session.current_rule

            # For now, just return success
            # await database.create_forwarding_rule(rule_data)

            # Add to session's rules list
            session.forwarding_rules.append(rule_data)

            return True, "Rule created successfully!"

        except Exception as e:
            return False, f"Error creating rule: {str(e)}"


# Global rule creation flow instance
rule_creation_flow = RuleCreationFlow()