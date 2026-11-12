import json
import os
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


TOKEN = os.environ.get("DISCORD_TOKEN")
GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
COMMAND_ROLE_NAMES = {"manager", "owner"}
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
CONFIG_PATH = DATA_DIR / "config.json"

if not TOKEN:
    raise RuntimeError("Set the DISCORD_TOKEN environment variable.")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def can_create(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(
        role.name.casefold() in COMMAND_ROLE_NAMES for role in member.roles
    )


def load_config() -> dict[str, str]:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


@bot.tree.command(name="create", description="Create a private channel")
@app_commands.describe(
    name="Channel name",
    user="Optional person to give access",
    role="Optional role to give access",
)
async def create_channel(
    interaction: discord.Interaction,
    name: app_commands.Range[str, 1, 90],
    user: discord.Member | None = None,
    role: discord.Role | None = None,
) -> None:
    if not isinstance(interaction.user, discord.Member) or not can_create(interaction.user):
        await interaction.response.send_message(
            "Only members with the Manager or Owner role can use /create.",
            ephemeral=True,
        )
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return

    channel_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-_").lower()
    if not channel_name:
        await interaction.response.send_message("Choose a name with letters or numbers.", ephemeral=True)
        return

    bot_member = guild.me
    if bot_member is None or not bot_member.guild_permissions.manage_channels:
        await interaction.response.send_message(
            "I need the Manage Channels permission to create private channels.", ephemeral=True
        )
        return

    saved_category_id = load_config().get(str(guild.id))
    category = guild.get_channel(int(saved_category_id)) if saved_category_id else None
    if saved_category_id and not isinstance(category, discord.CategoryChannel):
        await interaction.response.send_message(
            "The saved category is no longer available. Set it again with /category.", ephemeral=True
        )
        return

    overwrites: dict[discord.Role | discord.Member, discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        bot_member: discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
            manage_channels=True,
            manage_permissions=True,
        ),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
        ),
    }
    if user:
        overwrites[user] = discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
        )
    if role:
        overwrites[role] = discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
        )

    try:
        channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Private channel created by {interaction.user} using /create",
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I couldn't create the channel. Check my role position and channel permissions.",
            ephemeral=True,
        )
        return
    except discord.HTTPException:
        await interaction.response.send_message("Discord couldn't create that channel. Try another name.", ephemeral=True)
        return

    await interaction.response.send_message(f"Created private channel {channel.mention}.", ephemeral=True)


@bot.tree.command(name="category", description="Choose where /create puts new channels")
@app_commands.describe(category="The category to put new private channels in")
async def set_category(
    interaction: discord.Interaction,
    category: discord.CategoryChannel,
) -> None:
    if not isinstance(interaction.user, discord.Member) or not can_create(interaction.user):
        await interaction.response.send_message(
            "Only members with the Manager or Owner role can use /category.", ephemeral=True
        )
        return
    if interaction.guild is None or category.guild.id != interaction.guild.id:
        await interaction.response.send_message("Choose a category from this server.", ephemeral=True)
        return

    config = load_config()
    config[str(interaction.guild.id)] = str(category.id)
    try:
        save_config(config)
    except OSError:
        await interaction.response.send_message(
            "I couldn't save the category. Check that the /data storage is writable.", ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"New private channels will be created in {category.mention}.", ephemeral=True
    )


@bot.event
async def on_ready() -> None:
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()
    print(f"Ready as {bot.user}")


bot.run(TOKEN)
