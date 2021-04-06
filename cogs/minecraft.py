import sqlite3
import helpers.embed_helper
import helpers.role_helper

from discord.ext import commands
from mojang_api import Player, get_status
from mcrcon import MCRcon

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

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
                    await whitelist_remove_user(user[0])

        print('Minecraft Module Loaded.')

    # COMMANDS #
    @commands.command(name="whitelist")
    @helpers.role_helper.is_sub()
    @commands.guild_only()
    async def whitelist(self, ctx, username):

        print(f'{ctx.author}({ctx.author.id}) executed Whitelist command.')

        status_response: dict = get_status()
        auth_server = status_response.get('data')[3]
        auth_server_status = auth_server['authserver.mojang.com']

        if auth_server_status == 'green':
            if await is_rcon_enabled():
                if await helpers.role_helper.is_role_defined('sub'):
                    try:
                        player = Player(username=username)
                        await whitelist_add_user(ctx.author.id, username)
                        await ctx.send(
                            embed=await helpers.embed_helper.create_success_embed(
                                f'Set whitelist for {ctx.author.mention}: `{player.username}`',
                                self.client.guilds[0].get_member(self.client.user.id).color
                            )
                        )
                    except:
                        await ctx.send(
                            embed=await helpers.embed_helper.create_error_embed(
                                f'`{username}` is not a valid Minecraft account.'
                            )
                        )
                else:
                    await ctx.send(
                        embed=await helpers.embed_helper.create_error_embed(
                            'Sub role has not been set. Please have an administrator use `!setrole sub @<role>`.'
                        )
                    )
            else:
                await ctx.send(
                    embed=await helpers.embed_helper.create_error_embed(
                        'RCON has not been set up yet, please ask an admin to set it up.'
                    )
                )
        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    'Mojang auth server is offline.'
                )
            )

    @commands.command(name='setrcon')
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def set_rcon(self, ctx, rcon_ip, rcon_port, rcon_password):

        print(f'{ctx.author}({ctx.author.id}) executed SetRCON command.')

        await set_rcon(rcon_ip, rcon_port, rcon_password)
        await ctx.send(
            embed=await helpers.embed_helper.create_success_embed(
                'RCON Info Set.',
                self.client.guilds[0].get_member(self.client.user.id).color
            )
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
    rcon: tuple = await get_rcon()
    mcr = MCRcon(host=rcon[0], port=int(rcon[1]), password=rcon[2])
    mcr.connect()

    if await has_whitelist(user_id):
        rcon_response = mcr.command(f'whitelist remove {await get_mc_username(user_id)}')
        print(rcon_response)
        db.execute('UPDATE minecraft_users SET mc_username=? WHERE user_id=?', (username, user_id))
    else:
        db.execute('INSERT INTO minecraft_users VALUES(?,?)', (user_id, username))
    connection.commit()

    rcon_response = mcr.command(f'whitelist add {username}')
    print(rcon_response)
    mcr.disconnect()

async def whitelist_remove_user(user_id):
    rcon: tuple = await get_rcon()
    mcr = MCRcon(host=rcon[0], port=int(rcon[1]), password=rcon[2])

    mcr.connect()
    rcon_response = mcr.command(f'whitelist remove {await get_mc_username(user_id)}')
    print(rcon_response)
    mcr.disconnect()

    db.execute('DELETE FROM minecraft_users WHERE user_id=?', (user_id,))
    connection.commit()

async def set_rcon(rcon_ip, rcon_port, rcon_password):
    db.execute('SELECT * FROM minecraft_rcon')
    row = db.fetchone()

    if row is not None:
        db.execute('UPDATE minecraft_rcon SET server_ip=?, port=?, password=? WHERE server_ip=?', (rcon_ip, rcon_port, rcon_password, row[0]))
    else:
        db.execute('INSERT INTO minecraft_rcon VALUES(?,?,?)', (rcon_ip, rcon_port, rcon_password))
    connection.commit()

async def get_rcon():
    db.execute('SELECT * FROM minecraft_rcon')
    row = db.fetchone()

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

def setup(client):
    client.add_cog(Minecraft(client))
