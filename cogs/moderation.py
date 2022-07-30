import discord
import sqlite3
import time
import helpers.role_helper
import helpers.config
import helpers.embed_helper
import helpers.channel_helper
import math
import calendar
import uuid
import asyncio

from discord.ext import commands
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from discord.ui import Button, View
from discord import app_commands

connection = sqlite3.connect("./db/logs.db")
db = connection.cursor()

connection2 = sqlite3.connect("./db/config.db")
db2 = connection2.cursor()

server_id = helpers.config.server_id

description = 'Tools and commands to be used by moderators of the server.'


class ModView(View):
    prev_button = Button(label='Previous', style=discord.ButtonStyle.green, custom_id=f'prev_cmd{time.time()}')
    next_button = Button(label='Next', style=discord.ButtonStyle.green, custom_id=f'next_cmd{time.time()}')

    def __init__(self, embeds, max_pages):
        super().__init__()
        self.page = 1
        self.embeds = embeds
        self.max_pages = max_pages
        self.next_button.callback = self.button_callback
        self.prev_button.callback = self.button_callback
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.disable_buttons()

    async def button_callback(self, interaction: discord.Interaction):
        button_id = interaction.data['custom_id']

        if button_id == self.next_button.custom_id:
            self.page += 1
        elif button_id == self.prev_button.custom_id:
            self.page -= 1

        self.disable_buttons()

        embed = self.embeds[self.page - 1]
        await interaction.response.edit_message(embed=embed, view=self)

    def disable_buttons(self):
        if self.page <= 1:
            self.prev_button.disabled = True
        else:
            self.prev_button.disabled = False
        if self.page == self.max_pages:
            self.next_button.disabled = True
        else:
            self.next_button.disabled = False

class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        table_string = 'CREATE TABLE IF NOT EXISTS messages (msg_id text unique, user_id text, message text, channel_name text, channel_id text, time_sent text, is_deleted int)'
        db.execute(table_string)

        table_string = 'CREATE TABLE IF NOT EXISTS punishments (uuid text unique, user_id text, type text, time_sent text, reason text, given_by text)'
        db.execute(table_string)

        db2.execute('CREATE TABLE IF NOT EXISTS banned_names(username text unique)')

        connection.commit()
        connection2.commit()

        print('Moderation Module Loaded.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot and (message.type == discord.MessageType.default or message.type == discord.MessageType.reply):
            user_id = message.author.id
            message_content = message.content
            if len(message.attachments) > 0:
                if len(message_content) == 0:
                    message_content = '(NONE)'
                message_content += ' | attachments: '
                for a in message.attachments:
                    message_content += f'( {a.url} )'

            await add_msg(user_id, message.id, message_content, message.channel.name, message.channel.id,
                          message.created_at, 0)
            await delete_old_messages()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message):
        await set_deleted(message.message_id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        punish_id = str(uuid.uuid4())
        ban_list = [entry async for entry in guild.bans(limit=2000)]

        reason = ''

        for _ban in ban_list:
            if _ban.user.id == user.id:
                if _ban.reason is not None:
                    reason = _ban.reason

        if await helpers.channel_helper.is_channel_defined('mod'):
            channel = guild.get_channel(await helpers.channel_helper.get_channel_id('mod'))
            ban_giver = ''

            await asyncio.sleep(2)

            async for log in guild.audit_logs(
                    limit=1,
                    action=discord.AuditLogAction.ban,
                    after=(datetime.now() - relativedelta(seconds=5))
            ):
                ban_giver = log.user
            if not ban_giver.bot:
                await add_punishment(punish_id, user.id, 'ban', datetime.now(timezone.utc), reason, ban_giver.id)
                await channel.send(embed=await ban_embed(punish_id, user, ban_giver, reason, guild.get_member(self.client.user.id).color))

    @app_commands.command(name='logs', description='Get message logs of a specified user via Discord ID')
    async def logs(self, interaction: discord.Interaction, user_id: str):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Logs command.')
            embeds = []

            messages = await get_messages(user_id)

            if len(messages) > 0:
                messages_per_page = 6
                total_pages = math.ceil(len(messages) / messages_per_page)

                for i in range(1, total_pages + 1):
                    user = interaction.guild.get_member(int(user_id))

                    if user is None:
                        user = await self.client.fetch_user(int(user_id))

                    embed = discord.Embed(
                        title=f'Messages From {user}',
                        color=interaction.guild.get_member(self.client.user.id).color
                    )
                    number = min((messages_per_page * i), len(messages))
                    for j in range((messages_per_page * (i - 1)), number):

                        t = datetime.fromisoformat(messages[j][5]).utctimetuple()
                        ep = calendar.timegm(t)

                        channel = interaction.guild.get_channel(int(messages[j][4]))
                        if channel is None:
                            channel = f'#{messages[j][3]}'
                        else:
                            channel = channel.mention

                        if messages[j][6] == 0:
                            deleted = '✅'
                        else:
                            deleted = '❌'

                        if j == messages_per_page * (i - 1):
                            msg_string: str = messages[j][2]
                            embed.add_field(name='Message', value=(msg_string[0:100]+'...' if (len(msg_string) > 200) else msg_string), inline=True)
                            embed.add_field(name='Time', value=f'<t:{ep}>', inline=True)
                            embed.add_field(name='Message Status/Channel', value=f'{deleted}   -   {channel}', inline=True)
                        else:
                            embed.add_field(name='\u200b', value=messages[j][2], inline=True)
                            embed.add_field(name='\u200b', value=f'<t:{ep}>', inline=True)
                            embed.add_field(name='\u200b', value=f'{deleted}   -   {channel}', inline=True)
                    if total_pages > 1:
                        embed.add_field(name='\u200b', value=f'Page [{i}/{total_pages}]', inline=True)
                    embeds.append(embed)

                view = ModView(embeds, total_pages)

                await interaction.response.send_message(
                    embed=embeds[0],
                    view=(view if total_pages > 1 else View())
                )
            else:
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed('This user has no message history.')
                )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='warn', description='Give user a warning')
    async def warn(self, interaction: discord.Interaction, user: discord.User, reason: str = ''):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Warn command.')
            punish_id = str(uuid.uuid4())
            await add_punishment(punish_id, user.id, 'warn', datetime.now(timezone.utc), reason, interaction.user.id)

            embed = discord.Embed(
                title='User Warned!',
                color=interaction.guild.get_member(self.client.user.id).color,
                description=f'{interaction.user.mention} gave a warning to {user.mention}'
            )
            if len(reason) > 0:
                embed.add_field(name='Reason', value=reason, inline=False)

            embed.set_footer(text=f'UUID: {punish_id}')

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='ban', description='Ban a user from the server using their discord ID.')
    async def ban(self, interaction: discord.Interaction, user_id: str, reason: str = ''):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Ban command.')
            user = None
            try:
                user = await self.client.fetch_user(int(user_id))
            except:
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed(
                        'Not a valid discord ID.')
                )

            if user:
                punish_id = str(uuid.uuid4())
                ban_reason = f'{interaction.user.name}: {reason}'
                await interaction.guild.ban(user=user, delete_message_days=1, reason=ban_reason)
                await add_punishment(punish_id, user.id, 'ban', datetime.now(timezone.utc), reason, interaction.user.id)
                color = interaction.guild.get_member(self.client.user.id).color
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_success_embed('User Banned!', color))
                if await helpers.channel_helper.is_channel_defined('mod'):
                    channel = interaction.guild.get_channel(await helpers.channel_helper.get_channel_id('mod'))
                    await channel.send(embed=await ban_embed(punish_id, user, interaction.user, reason, color))
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='standing', description='returns a list of punishments on a user and their warning points.')
    async def standing(self, interaction: discord.Interaction, user: discord.User):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Standing command.')
            embed = discord.Embed(
                title=f'Standing for {user}',
                color=interaction.guild.get_member(self.client.user.id).color,
                description=f'Current Warning Points: {await get_warn_points(user.id)}'
            )
            punishments = await get_punishments(user.id)
            embeds = []
            if len(punishments) > 0:
                messages_per_page = 6
                total_pages = math.ceil(len(punishments) / messages_per_page)

                for i in range(1, total_pages + 1):

                    number = min((messages_per_page * i), len(punishments))
                    for j in range((messages_per_page * (i - 1)), number):

                        t = datetime.fromisoformat(punishments[j][3]).utctimetuple()
                        ep = calendar.timegm(t)

                        if j == messages_per_page * (i - 1):
                            embed.add_field(name='Type / Giver', value=f'{get_type_string(punishments[j][2])}  -  {interaction.guild.get_member(int(punishments[j][5])).mention}', inline=True)
                            embed.add_field(name='Time', value=f'<t:{ep}>', inline=True)
                            embed.add_field(name='UUID', value=punishments[j][0], inline=True)
                        else:
                            embed.add_field(name='\u200b', value=f'{get_type_string(punishments[j][2])}  -  {interaction.guild.get_member(int(punishments[j][5])).mention}', inline=True)
                            embed.add_field(name='\u200b', value=f'<t:{ep}>', inline=True)
                            embed.add_field(name='\u200b', value=punishments[j][0], inline=True)
                    if total_pages > 1:
                        embed.add_field(name='\u200b', value=f'Page [{i}/{total_pages}]', inline=True)
                    embeds.append(embed)

                view = ModView(embeds, total_pages)

                await interaction.response.send_message(
                    embed=embeds[0],
                    view=(view if len(embeds) > 1 else View())
                )
            else:
                embed.add_field(name='Punishments:', value='N/A', inline=False)
                await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='punishment', description='Get information on a punishment via UUID')
    async def punishment(self, interaction: discord.Interaction, punishment_uuid: str):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Punishment command.')
            punish_data = await get_punishment(punishment_uuid)
            if punish_data is not None:
                user = await self.client.fetch_user(int(punish_data[1]))
                embed = discord.Embed(
                    title='Info On Punishment',
                    color=interaction.guild.get_member(self.client.user.id).color,
                    description=f'{get_type_string(punish_data[2])} on {user.mention}({user})'
                )
                embed.add_field(name='Given By', value=interaction.guild.get_member(int(punish_data[5])).mention, inline=True)
                t = datetime.fromisoformat(punish_data[3]).utctimetuple()
                ep = calendar.timegm(t)
                embed.add_field(name='Given At', value=f'<t:{ep}>', inline=True)
                embed.add_field(name='Reason', value=(punish_data[4] if len(punish_data[4]) > 0 else 'N/A'), inline=True)

                embed.set_footer(text=f'UUID: {punish_data[0]}')

                await interaction.response.send_message(
                    embed=embed
                )

            else:
                await interaction.response.send_message(
                    embed=helpers.embed_helper.create_error_embed('Not a valid punishment UUID')
                )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='remove', description='Remove a punishment from a user via UUID')
    async def remove(self, interaction: discord.Interaction, punishment_uuid: str):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Remove command.')
            if await get_punishment(punishment_uuid):
                await remove_punishment(punishment_uuid)
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_success_embed('Punishment removed!', interaction.guild.get_member(self.client.user.id).color)
                )
            else:
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed('Not a valid punishment UUID')
                )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='lookup', description='Lookup a discord user via user ID.')
    async def lookup(self, interaction: discord.Interaction, user_id: str):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Lookup command.')
            try:
                user = await self.client.fetch_user(int(user_id))
                embed = discord.Embed(
                    color=interaction.guild.get_member(self.client.user.id).color,
                    description=user.mention
                )
                embed.set_author(name=str(user), icon_url=user.display_avatar)
                embed.set_thumbnail(url=user.display_avatar)
                created_at = user.created_at

                embed.add_field(
                    name='Registered',
                    value=created_at.strftime('%a, %b %d, %Y %I:%M %p'),
                    inline=True
                )

                await interaction.response.send_message(
                    embed=embed
                )
            except:
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed(f'`{user_id}` is not a valid Discord user ID.'))
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='massban', description='Ban multiple users from the server using a username.')
    async def massban(self, interaction: discord.Interaction, username: str, reason: str = ''):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id,
                                              'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Mass Ban command.')
            members = await interaction.guild.query_members(query=f'{username}')
            ban_reason = f'{interaction.user.name}: {reason}'

            for m in members:
                user = self.client.get_user(m.id)
                await interaction.guild.ban(user=user, delete_message_days=1, reason=ban_reason)
                embed = discord.Embed(
                    title='User Banned!',
                    color=interaction.guild.get_member(self.client.user.id).color,
                    description=f'{interaction.user.mention} banned {user}.'
                )
                embed.set_author(name=str(user), icon_url=user.display_avatar)
                if len(reason) > 0:
                    embed.add_field(name='Reason', value=reason, inline=False)
                embed.set_footer(text=f'Discord ID: {user.id}')
                if await helpers.channel_helper.is_channel_defined('mod'):
                    channel = interaction.guild.get_channel(await helpers.channel_helper.get_channel_id('mod'))
                    await channel.send(embed=embed)
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='autoban', description='Add a username to a list that will be auto banned upon joining the server.')
    async def autoban(self, interaction: discord.Interaction, username: str):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Auto Ban command.')
            db2.execute('INSERT INTO banned_names VALUES (?)', (username,))
            connection2.commit()
            embed = await helpers.embed_helper.create_success_embed(
                f'`{username}` Added To Auto-Ban List.',
                interaction.guild.get_member(self.client.user.id).color
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='unautoban', description='Remove a username form the auto ban list.')
    async def unautoban(self, interaction: discord.Interaction, username: str):
        if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed Un-Auto Ban Name command.')
            db2.execute('DELETE FROM banned_names WHERE username=?', (username,))
            connection2.commit()
            embed = await helpers.embed_helper.create_success_embed(
                f'`{username}` Removed From Auto-Ban List.',
                interaction.guild.get_member(self.client.user.id).color
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

async def add_msg(user_id, msg_id, message, channel_name, channel_id, time_sent, is_deleted):
    query_string = 'INSERT INTO messages VALUES (?,?,?,?,?,?,?)'
    db.execute(query_string, (msg_id, user_id, message, channel_name, channel_id, time_sent, is_deleted))
    connection.commit()

async def get_messages(user_id):
    query_string = 'SELECT * FROM messages WHERE user_id=? ORDER BY time_sent DESC'
    db.execute(query_string, (user_id,))
    results = db.fetchall()
    return results

async def set_deleted(message_id):
    query_string = 'UPDATE messages SET is_deleted=1 WHERE msg_id=?'
    db.execute(query_string, (message_id,))
    connection.commit()

async def delete_old_messages():
    query_string = 'SELECT msg_id, time_sent FROM messages'
    db.execute(query_string)
    results = db.fetchall()

    for m in results:
        if datetime.fromisoformat(m[1]) + relativedelta(days=30) < datetime.now(timezone.utc):
            db.execute('DELETE FROM messages WHERE msg_id=?', (m[0],))
            connection.commit()

async def add_punishment(punish_id, user_id, punish_type, time_sent, reason, giver_id):
    query_string = 'INSERT INTO punishments VALUES (?,?,?,?,?,?)'
    db.execute(query_string, (punish_id, user_id, punish_type, time_sent, reason, giver_id))
    connection.commit()

async def get_punishment(punish_id):
    query_string = 'SELECT * FROM punishments WHERE uuid=?'
    db.execute(query_string, (punish_id,))
    result = db.fetchone()
    return result

async def get_punishments(user_id):
    query_string = 'SELECT * FROM punishments WHERE user_id=?'
    db.execute(query_string, (user_id,))
    results = db.fetchall()
    return results

async def remove_punishment(punish_id):
    query_string = 'DELETE FROM punishments WHERE uuid=?'
    db.execute(query_string, (punish_id,))
    connection.commit()

async def ban_embed(punish_id, user, ban_giver, reason, color):
    embed = discord.Embed(
        title='User Banned!',
        color=color,
        description=f'{ban_giver.mention} banned {user}.'
    )
    embed.set_author(name=f'{str(user)} ({user.id})', icon_url=user.display_avatar)

    if len(reason) > 0:
        embed.add_field(name='Reason', value=reason, inline=False)

    embed.set_footer(text=f'UUID: {punish_id}')

    return embed

async def get_warn_points(user_id):
    query_string = 'SELECT * FROM punishments WHERE user_id=? AND type=?'
    db.execute(query_string, (user_id, 'warn'))
    results = db.fetchall()
    return len(results)

def get_type_string(_type):
    if _type == 'warn':
        return 'Warning'
    elif _type == 'ban':
        return 'Ban'
    elif _type == 'kick':
        return 'Kick'

async def setup(client):
    await client.add_cog(Moderation(client), guild=discord.Object(id=server_id))
