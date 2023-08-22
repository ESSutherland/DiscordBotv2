import sqlite3

import discord

import helpers.embed_helper
import helpers.role_helper
import helpers.config

from discord.ext import commands
from mojang_api import Player, get_status
from mcrcon import MCRcon
from discord import app_commands

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

server_id = helpers.config.server_id

description = 'Allows twitch subscribers to whitelist themselves on the connected Minecraft server.'

class Minecraft(commands.Cog):

    def __init__(self, client):
        self.client = client

    # EVENTS #
    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS minecraft_users (user_id text unique, mc_username text)')
        db.execute('CREATE TABLE IF NOT EXISTS minecraft_rcon (server_ip text, port text, password text)')
        connection.commit()

        for user in await get_all_whitelists():
            if await helpers.role_helper.is_role_defined('sub'):
                if not await helpers.role_helper.has_role(
                    self.client.guilds[0],
                    int(user[0]),
                    'sub'
                ):
                    try:
                        await whitelist_remove_user(user[0])
                    except:
                        print('MINECRAFT SERVER OFFLINE')

        print('Minecraft Module Loaded.')

    # COMMANDS #
    @app_commands.command(name='whitelist', description='Allows subscribers to whitelist themselves on the linked Minecraft server.')
    async def whitelist(self, interaction: discord.Interaction, username: str):
        author = interaction.user
        if await helpers.role_helper.has_role(interaction.guild, author.id, 'sub') or await helpers.role_helper.has_role(interaction.guild, author.id, 'mod'):
            print(f'{author.name}({author.id}) executed Whitelist command.')

            if await is_rcon_enabled():
                if await helpers.role_helper.is_role_defined('sub'):
                    player = None
                    try:
                        player = Player(username=username)
                    except:
                        await interaction.response.send_message(
                            embed=await helpers.embed_helper.create_error_embed(
                                f'`{username}` is not a valid Minecraft account.'
                            )
                        )
                    else:
                        await whitelist_add_user(author.id, username)
                        await interaction.response.send_message(
                            embed=await helpers.embed_helper.create_success_embed(
                                f'Set whitelist for {author.mention}: `{player.username}`',
                                self.client.guilds[0].get_member(self.client.user.id).color
                            )
                        )
                else:
                    await interaction.response.send_message(
                        embed=await helpers.embed_helper.create_error_embed(
                            'Sub role has not been set.'
                        )
                    )
            else:
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed(
                        'RCON has not been set up yet, please ask an admin to set it up.'
                    )
                )

    @app_commands.command(name='addrcon', description='Used to set up RCON information of a Minecraft server.')
    async def add_rcon(self, interaction: discord.Interaction, rcon_ip: str, rcon_port: str, rcon_password: str):
        if interaction.user.guild_permissions.administrator:
            print(f'{interaction.user.name}({interaction.user.id}) executed AddRCON command.')

            await add_rcon(rcon_ip, rcon_port, rcon_password)
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_success_embed(
                    'RCON Info Set.',
                    interaction.guild.get_member(self.client.user.id).color
                )
            )

    @app_commands.command(name='delrcon', description='Used to remove RCON information of a Minecraft server.')
    async def del_rcon(self, interaction: discord.Interaction, rcon_ip: str):
        if interaction.user.guild_permissions.administrator and await is_rcon(rcon_ip):
            print(f'{interaction.user.name}({interaction.user.id}) executed DelRCON command.')

            await remove_rcon(rcon_ip)
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_success_embed(
                    'RCON Info Removed.',
                    interaction.guild.get_member(self.client.user.id).color
                )
            )

    @app_commands.command(name='listrcon', description='Used to get the RCON information of the Minecraft servers.')
    async def list_rcon(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            print(f'{interaction.user.name}({interaction.user.id}) executed ListRCON command.')
            embed = discord.Embed(
                title='RCON Connections',
                color=interaction.guild.get_member(self.client.user.id).color
            )
            rcon_list = await get_rcon()

            for rcon in rcon_list:
                embed.add_field(
                    name='\u200b',
                    value=f'{rcon[0]}',
                    inline=True
                )

                embed.add_field(
                    name='\u200b',
                    value=f'{rcon[1]}',
                    inline=True
                )

                embed.add_field(
                    name='\u200b',
                    value=f'{rcon[2]}',
                    inline=True
                )

            await interaction.response.send_message(
                embed=embed
            )

    @whitelist.error
    async def whitelist_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.__cause__, ConnectionRefusedError):
                print("SERVER OFFLINE")
                await ctx.send(
                    embed=await helpers.embed_helper.create_error_embed(
                        'Minecraft server is offline.'
                    )
                )
            else:
                print(error)

async def has_whitelist(user_id):
    db.execute('SELECT mc_username FROM minecraft_users WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_mc_username(user_id):
    db.execute('SELECT mc_username FROM minecraft_users WHERE user_id=?', (user_id,))
    row = db.fetchone()

    return row[0]

async def whitelist_add_user(user_id, username):
    for rcon in await get_rcon():
        mcr = MCRcon(host=rcon[0], port=int(rcon[1]), password=rcon[2])
        mcr.connect()

        if await has_whitelist(user_id):
            rcon_response = mcr.command(f'whitelist remove {await get_mc_username(user_id)}')
            print(rcon_response)

        rcon_response = mcr.command(f'whitelist add {username}')
        print(rcon_response)
        mcr.disconnect()

    if await has_whitelist(user_id):
        db.execute('UPDATE minecraft_users SET mc_username=? WHERE user_id=?', (username, user_id))
    else:
        db.execute('INSERT INTO minecraft_users VALUES(?,?)', (user_id, username))
    connection.commit()

async def whitelist_remove_user(user_id):
    for rcon in await get_rcon():
        mcr = MCRcon(host=rcon[0], port=int(rcon[1]), password=rcon[2])

        mcr.connect()
        rcon_response = mcr.command(f'whitelist remove {await get_mc_username(user_id)}')
        print(rcon_response)
        mcr.disconnect()

    db.execute('DELETE FROM minecraft_users WHERE user_id=?', (user_id,))
    connection.commit()

async def add_rcon(rcon_ip, rcon_port, rcon_password):
    db.execute('INSERT INTO minecraft_rcon VALUES(?,?,?)', (rcon_ip, rcon_port, rcon_password))
    connection.commit()

async def remove_rcon(rcon_ip):
    db.execute('DELETE FROM minecraft_rcon WHERE server_ip=?', (rcon_ip,))
    connection.commit()

async def is_rcon(rcon_ip):
    db.execute('SELECT * FROM minecraft_rcon WHERE server_ip=?', (rcon_ip,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_rcon():
    db.execute('SELECT * FROM minecraft_rcon')
    row = db.fetchall()

    return row

async def is_rcon_enabled():
    db.execute('SELECT * FROM minecraft_rcon')
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_all_whitelists():
    db.execute('SELECT * FROM minecraft_users')
    results = db.fetchall()

    return results

async def setup(client):
    await client.add_cog(Minecraft(client), guild=discord.Object(id=server_id))
