import sqlite3

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

async def has_role(guild, user_id,  role_name):
    role_id = await get_role_id(role_name)
    role = guild.get_role(int(role_id))
    member = guild.get_member(user_id)

    for r in member.roles:
        if r == role:
            return True
    return False
