import discord
import sqlite3
import helpers.role_helper
import helpers.config
import helpers.embed_helper

from discord.ext import commands
from discord import app_commands

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

description = 'Allows users to obtain roles that will help them get notified of community events.'
server_id = helpers.config.server_id

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
        if is_message_set('movie') and await helpers.role_helper.is_role_defined('movie'):
            if payload.emoji.name == "🎥" and not payload.member.bot:
                if str(message.id) == get_message('movie'):
                    role = self.client.guilds[0].get_role(await helpers.role_helper.get_role_id('movie'))
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
        if is_message_set('movie') and await helpers.role_helper.is_role_defined('movie'):
            if payload.emoji.name == "🎥" and not member.bot:
                if str(message.id) == get_message('movie'):
                    role = self.client.guilds[0].get_role(await helpers.role_helper.get_role_id('movie'))
                    await member.remove_roles(role)

    @app_commands.command(name='game', description='create a game role message')
    async def game(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('✅')
            if await helpers.role_helper.is_role_defined('game'):
                role = interaction.guild.get_role(await helpers.role_helper.get_role_id('game'))
                embed = discord.Embed(
                    title='Community Games!',
                    description=f'React to this message with 🎮 to receive the {role.mention} role and be notified about Community Gaming related messages! Remove your reaction at any time to remove the role from yourself.',
                    color=self.client.guilds[0].get_member(self.client.user.id).color
                )
                message = await interaction.channel.send(embed=embed)
                await interaction.delete_original_response()
                set_message('game', message.id)
                await message.add_reaction("🎮")
        else:
            await interaction.response.send_message(embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command'))

    @app_commands.command(name='movie', description='create a watch party role message')
    async def movie(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('✅')
            if await helpers.role_helper.is_role_defined('movie'):
                role = interaction.guild.get_role(await helpers.role_helper.get_role_id('movie'))
                embed = discord.Embed(
                    title='Community Watch Parties!',
                    description=f'React to this message with 🎥 to receive the {role.mention} role and be notified about Community Watch Party related messages! Remove your reaction at any time to remove the role from yourself.',
                    color=interaction.guild.get_member(self.client.user.id).color
                )
                message = await interaction.channel.send(embed=embed)
                await interaction.delete_original_response()
                set_message('movie', message.id)
                await message.add_reaction("🎥")
        else:
            await interaction.response.send(embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command'))

    @app_commands.command(name='live', description='create a live notice role message')
    async def live(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('✅')
            if await helpers.role_helper.is_role_defined('live'):
                role = interaction.guild.get_role(await helpers.role_helper.get_role_id('live'))
                embed = discord.Embed(
                    title='Live Notifications!',
                    description=f'React to this message with 🔴 to receive the {role.mention} role and be notified when there is a stream! Remove your reaction at any time to remove the role from yourself.',
                    color=self.client.guilds[0].get_member(self.client.user.id).color
                )
                message = await interaction.channel.send(embed=embed)
                await interaction.delete_original_response()
                set_message('movie', message.id)
                await message.add_reaction("🔴")
        else:
            await interaction.response.send(embed=await helpers.embed_helper.create_error_embed(
                'You do not have permission to use this command'))

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

async def setup(client):
    await client.add_cog(CommunityRoles(client), guild=discord.Object(id=server_id))
