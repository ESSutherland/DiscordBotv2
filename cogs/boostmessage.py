import discord
import helpers.channel_helper

from discord.ext import commands
from configparser import ConfigParser

cfg = ConfigParser()
cfg.read('config.ini')

boost_message = cfg.get('Bot', 'boost_message')

description = 'Have the bot send a thank you message in the general channel when someone boosts the server.'

class BoostMessage(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.type == discord.MessageType.premium_guild_subscription or
                message.type == discord.MessageType.premium_guild_tier_1 or
                message.type == discord.MessageType.premium_guild_tier_2 or
                message.type == discord.MessageType.premium_guild_tier_3 or
                (message.content == 'test_boost' and message.author.guild_permissions.administrator)
        ):
            if await helpers.channel_helper.is_channel_defined('general'):
                global boost_message
                if '{user}' in boost_message:
                    print(True)
                    boost_message = boost_message.replace('{user}', message.author.mention)
                await message.guild.get_channel(await helpers.channel_helper.get_channel_id('general')).send(
                    boost_message
                )

    @commands.command(name='boostmessage')
    @commands.has_permissions(administrator=True)
    async def boost_message(self, ctx, *, message):
        cfg_file = open('config.ini', 'w')
        cfg.set('Bot', 'boost_message', message)
        cfg.write(cfg_file)
        cfg_file.close()


def setup(client):
    client.add_cog(BoostMessage(client))
