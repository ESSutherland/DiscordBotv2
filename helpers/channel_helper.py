import sqlite3

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

async def is_channel_defined(channel):
    db.execute('SELECT channel_id FROM channels WHERE channel_name=?', (channel,))
    row = db.fetchone()
    if row is not None:
        return True
    else:
        return False

async def get_channel_id(channel):
    db.execute('SELECT channel_id FROM channels WHERE channel_name=?', (channel,))
    row = db.fetchone()
    return row[0]
