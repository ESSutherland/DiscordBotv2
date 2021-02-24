import sqlite3
import discord
import helpers.embed_helper

from discord.ext import commands

description = 'Allows users to run a command to get information about a specified Animal Crossing New Horizons Villager.'

class AnimalCrossing(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Animal Crossing Module Loaded.')

    @commands.command(name='villager')
    async def villager(self, ctx, villager_name):
        if await is_villager(villager_name):
            villager = await get_villager_data(villager_name)
            embed = discord.Embed(
                color=self.client.guilds[0].get_member(self.client.user.id).color
            )
            embed.set_author(name=villager[2], icon_url=f'http://acnhapi.com/v1/icons/villagers/{villager[0]}')
            embed.set_image(url=f'http://acnhapi.com/v1/images/villagers/{villager[0]}')
            embed.add_field(
                name='Personality :smiley:',
                value=villager[3],
                inline=True
            )
            await helpers.embed_helper.add_blank_field(embed, True)
            embed.add_field(
                name='Birthday :birthday:',
                value=villager[4],
                inline=True
            )
            embed.add_field(
                name='Species :dna:',
                value=villager[5],
                inline=True
            )
            await helpers.embed_helper.add_blank_field(embed, True)
            embed.add_field(
                name='Gender :couple:',
                value=villager[6],
                inline=True
            )
            embed.add_field(
                name='Catchphrase :speech_balloon:',
                value=villager[7],
                inline=True
            )

            await ctx.send(
                embed=embed
            )

        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'Villager `{villager_name}` not Found! This command only supports villagers from Animal Crossing: New Horizons.'
                )
            )

async def is_villager(villager_name):
    connection = sqlite3.connect('./db/villagers.db')
    db = connection.cursor()

    db.execute('SELECT * FROM villagers WHERE LOWER(name) LIKE ?', (villager_name.lower(),))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_villager_data(villager_name):
    connection = sqlite3.connect('./db/villagers.db')
    db = connection.cursor()

    db.execute('SELECT * FROM villagers WHERE LOWER(name) LIKE ?', (villager_name.lower(),))
    row = db.fetchone()

    return row

def setup(client):
    client.add_cog(AnimalCrossing(client))
