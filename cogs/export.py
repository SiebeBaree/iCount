import discord
from discord.ext import commands
import settings
import mysql.connector
import json
import os
from core._errors import Error


class CogsExport(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["dump"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def export(self, ctx):
        if ctx.author.id == ctx.guild.owner_id:
            db = mysql.connector.connect(host=settings.host, database=settings.database,
                                         user=settings.user, passwd=settings.passwd)
            cursor = db.cursor()

            cursor.execute("SELECT * FROM guildSettings WHERE guild = %s", (ctx.guild.id,))
            guild_settings = cursor.fetchone()

            if guild_settings is None:
                print(f"[ERROR] guild_settings not found onCount.py (Guild: {ctx.guild.id}, ID: {ctx.guild.id})")
                db.close()
                return

            cursor.execute("SELECT * FROM guildData WHERE guild = %s", (ctx.guild.id,))
            guild_data = cursor.fetchone()

            if guild_data is None:
                guild_data = (ctx.guild.id, 0, 0)

            cursor.execute("SELECT * FROM guildModules WHERE guild = %s", (ctx.guild.id,))
            guild_modules = cursor.fetchone()

            if guild_modules is None:
                guild_modules = (ctx.guild.id, 0, 0, 0, 0, 0)

            cursor.execute("SELECT * FROM guildAutomation WHERE guild = %s", (ctx.guild.id,))
            guild_automation = cursor.fetchall()

            if guild_automation is None:
                guild_automation = ()

            cursor.execute("SELECT * FROM userData WHERE guild = %s", (ctx.guild.id,))
            user_data = cursor.fetchall()

            if user_data is None:
                user_data = ()

            cursor.execute("SELECT * FROM userNotify WHERE guild = %s", (ctx.guild.id,))
            user_notify = cursor.fetchall()

            if user_notify is None:
                user_notify = ()

            db.close()

            user_data_dict = {}
            for user in user_data:
                user_data_dict[f"{user[2]}"] = user[3]

            notifications_data = {}
            for notification in user_notify:
                notifications_data[f"{notification[0]}"] = {
                    "user": notification[2],
                    "mode": notification[4],
                    "number": notification[3]
                }

            automation_data = {}
            for automation in guild_automation:
                automation_data[f"{automation[0]}"] = {
                    "trigger": automation[2],
                    "action": automation[3],
                    "number": automation[4],
                    "actionId": automation[5],
                    "message": automation[6]
                }

            # try:
            #     os.remove(f"data/exportdata/{ctx.guild.id}.json")
            # except Exception:
            #     pass

            export_data = {
                "guild-id": ctx.guild.id,
                "prefix": guild_settings[1],
                "channel-id": guild_settings[2],
                "maxcount": guild_settings[3],
                "timeoutrole": guild_settings[4],
                "language": guild_settings[6],
                "count": guild_data[1],
                "lastuser": guild_data[2],
                "modules": {
                    "allow-spam": guild_modules[1],
                    "restart-error": guild_modules[2],
                    "emote-react": guild_modules[3],
                    "post-embed": guild_modules[4]
                },
                "userdata": user_data_dict,
                "notifications": notifications_data,
                "automation": automation_data
            }

            with open(f"data/exportdata/{ctx.guild.id}.json", "w") as export_file:
                json.dump(export_data, export_file, indent=4)

            try:
                await ctx.author.send(f"Database Export data for guild {ctx.guild} ({ctx.guild.id})", file=discord.File(f"data/exportdata/{ctx.guild.id}.json"))
                await ctx.send(":white_check_mark: Export Data send into you DMs.")
            except discord.errors.Forbidden:
                await ctx.send(":x: I cannot send a message to you. Please enable private messaging in the privacy settings of this server.")
                ctx.command.reset_cooldown(ctx)

            # try:
            #     os.remove(f"data/exportdata/{ctx.guild.id}.json")
            # except Exception:
            #     pass
        else:
            ctx.command.reset_cooldown(ctx)
            raise commands.MissingPermissions([])

    @export.error
    async def export_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Sorry, this feature is not working yet.")
        else:
            error_class = Error(ctx, error, self.client)
            await error_class.error_check()


def setup(client):
    client.add_cog(CogsExport(client))
