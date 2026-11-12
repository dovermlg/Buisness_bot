# Private channel bot

A small `discord.py` bot with `/create` and `/category` slash commands.

Only members with a role named **Manager** or **Owner** can run it. Server administrators can also run it. Each channel is private by default; the creator, the optional user, the optional role, and the bot can view history, send messages, and attach files. Channels remain until a server member with permission deletes them.

## Run with Portainer

1. Put this folder in a GitHub repository.
2. In Portainer, create a Stack from that repository and select `compose.yaml`.
3. Add stack environment variables `DISCORD_TOKEN` and `DISCORD_GUILD_ID` before deploying. `DISCORD_GUILD_ID` makes the slash commands appear quickly in that server.
4. Deploy the stack. The named `bot-data` volume keeps the selected category when the container is recreated.
5. In Discord, run `/category category:<your category>` once. Then use `/create name:<channel name> [user] [role]`.

## Run locally

1. Create a Discord application and bot in the Discord Developer Portal. Enable the `bot` and `applications.commands` scopes when inviting it. Grant it **Manage Channels**; put its role above any roles you want it to grant channel access to.
2. Install Python 3.10 or newer.
3. In this folder, install dependencies with `python -m pip install -r requirements.txt`.
4. Set the bot token and server ID as environment variables in the shell or hosting service, then run `python bot.py`.

For quick local use in PowerShell:

```powershell
$env:DISCORD_TOKEN = "your bot token"
$env:DISCORD_GUILD_ID = "your server ID"
python bot.py
```

The bot must stay running for `/create` to work. Keep the token private and reset it in the Developer Portal if it is exposed. Names are checked case-insensitively; use the exact role names `Manager` and `Owner`.

## Command

`/category category:<category>` selects the category for future channels. Only members with the Manager or Owner role (or server administrators) can use it. The setting is saved in `/data/config.json`.

`/create name:<channel-name> [user:<member>] [role:<role>]`

The optional user and role receive permission to view the channel and its history, send messages, and attach files. The creator is always included. The bot does not provide separate commands to change access after creation; authorized server staff can manage the channel in Discord.
