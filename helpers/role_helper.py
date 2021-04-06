import sqlite3

from discord.ext import commands

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

async def is_role_defined(role):
    db.execute('SELECT role_id FROM roles WHERE role_name=?', (role,))
    row = db.fetchone()
    if row is not None:
        return True
    else:
        return False

async def get_role_id(role):
    db.execute('SELECT role_id FROM roles WHERE role_name=?', (role,))
    row = db.fetchone()
    return row[0]

async def get_role_index(guild, role):

    return guild.roles.index(role)

async def has_role(guild, user_id,  role_name):
    role_id = await get_role_id(role_name)
    role = guild.get_role(int(role_id))
    member = guild.get_member(user_id)

    if member is None:
        return False

    for r in member.roles:
        if r == role:
            return True
    return False

def is_booster(admin=True):
    async def predicate(ctx):
        if await is_role_defined('booster'):
            if (await has_role(ctx.guild, ctx.author.id, 'booster') or
                    (ctx.author.guild_permissions.administrator and admin)):
                return True
            else:
                return False
        else:
            return False
    return commands.check(predicate)

def is_mod(admin=True):
    async def predicate(ctx):
        if await is_role_defined('mod'):
            if (await has_role(ctx.guild, ctx.author.id, 'mod') or
                    (ctx.author.guild_permissions.administrator and admin)):
                return True
            else:
                return False
        else:
            return False
    return commands.check(predicate)

def is_sub(admin=True):
    async def predicate(ctx):
        if await is_role_defined('sub'):
            if (await has_role(ctx.guild, ctx.author.id, 'sub') or
                    (ctx.author.guild_permissions.administrator and admin)):
                return True
            else:
                return False
        else:
            return False
    return commands.check(predicate)
