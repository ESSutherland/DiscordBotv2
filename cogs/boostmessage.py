import discord
import helpers.channel_helper
import helpers.embed_helper
import helpers.config

from discord.ext import commands
from configparser import ConfigParser
from discord import app_commands

cfg = ConfigParser()
cfg.read('config.ini')

boost_message = cfg.get('Bot', 'boost_message')
server_id = helpers.config.server_id

description = 'Have the bot send a thank you message in the general channel when someone boosts the server.'

class BoostMessage(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Boost Message Module Loaded.')

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
                    user_message = boost_message.replace('{user}', message.author.mention)
                    await message.guild.get_channel(await helpers.channel_helper.get_channel_id('general')).send(
                        user_message
                    )
                else:
                    await message.guild.get_channel(await helpers.channel_helper.get_channel_id('general')).send(
                        boost_message
                    )

    @app_commands.command(name='boostmessage', description='Set the message that is sent in the defined general channel when a user boosts the server.')
    async def boost_message(self, interaction: discord.Interaction, message: str):
        if interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed BoostMessage command.')
            cfg_file = open('config.ini', 'w')
            cfg.set('Bot', 'boost_message', message)
            cfg.write(cfg_file)
            cfg_file.close()

            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_success_embed('Boost Message Updated.',
                                                                      self.client.guilds[0].get_member(
                                                                          self.client.user.id).color)
            )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )


async def setup(client):
    await client.add_cog(BoostMessage(client), guild=discord.Object(id=server_id))
