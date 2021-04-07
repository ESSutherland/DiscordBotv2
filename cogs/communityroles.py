import discord
import sqlite3
import helpers.role_helper

from discord.ext import commands

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

description = 'Allows users to obtain roles that will help them get notified of community events.'

class CommunityRoles(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS role_messages (message_name text unique, message_id text)')
        connection.commit()
        print('Community Roles Module Loaded')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message = await self.client.guilds[0].get_channel(payload.channel_id).fetch_message(payload.message_id)
        if is_message_set('game') and await helpers.role_helper.is_role_defined('game'):
            if payload.emoji.name == "🎮" and not payload.member.bot:
                if str(message.id) == get_message('game'):
                    role = self.client.guilds[0].get_role(await helpers.role_helper.get_role_id('game'))
                    await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message = await self.client.guilds[0].get_channel(payload.channel_id).fetch_message(payload.message_id)
        member = self.client.guilds[0].get_member(payload.user_id)
        if is_message_set('game') and await helpers.role_helper.is_role_defined('game'):
            if payload.emoji.name == "🎮" and not member.bot:
                if str(message.id) == get_message('game'):
                    role = self.client.guilds[0].get_role(await helpers.role_helper.get_role_id('game'))
                    await member.remove_roles(role)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def game(self, ctx):
        if await helpers.role_helper.is_role_defined('game'):
            message = await ctx.send('GAME MESSAGE')
            set_message('game', message.id)
            await message.add_reaction("🎮")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def movie(self, ctx):
        if await helpers.role_helper.is_role_defined('movie'):
            message = await ctx.send('MOVIE MESSAGE')
            set_message('movie', message.id)
            await message.add_reaction("🎥")

def set_message(name, message_id):
    if is_message_set(name):
        db.execute('UPDATE role_messages SET message_id=? WHERE message_name=?', (message_id, name))
    else:
        db.execute('INSERT INTO role_messages VALUES (?,?)', (name, message_id))

    connection.commit()

def get_message(name):
    db.execute('SELECT message_id FROM role_messages WHERE message_name=?', (name,))
    row = db.fetchone()

    if row is not None:
        return row[0]
    else:
        return ""

def is_message_set(name):
    db.execute('SELECT * FROM role_messages WHERE message_name=?', (name,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

def setup(client):
    client.add_cog(CommunityRoles(client))
