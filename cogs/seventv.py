import io

import helpers.config
import helpers.embed_helper
import requests
import discord

from PIL import Image

from discord.ext import commands
from discord import app_commands

description = 'Add 7tv Emotes to discord server'
server_id = helpers.config.server_id

url = 'https://7tv.io/v3'

requests.packages.urllib3.disable_warnings()

class SevenTV(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('7TV Module Loaded.')

    @app_commands.command(name='7tv', description='add a 7tv emote to the server')
    async def emote(self, interaction: discord.Interaction, emote_id: str):
        if interaction.user.guild_permissions.manage_emojis:
            try:
                r = requests.get(url=f'{url}/emotes/{emote_id}', verify=False)
                r_json = r.json()
                emote_url = f'https:{r_json.get("host").get("url")}/4x.webp'
                image = Image.open(requests.get(emote_url, stream=True, verify=False).raw)
                buf = io.BytesIO()
                if r_json.get('animated'):
                    image.save(buf, 'gif', save_all=True, disposal=2, loop=0)
                else:
                    image.save(buf, 'png')
                await interaction.guild.create_custom_emoji(name=r_json.get("name"), image=buf.getvalue())
                await interaction.response.send_message(embed=await helpers.embed_helper.create_success_embed(
                    message=f'Emote `{r_json.get("name")}` has been added to the server!',
                    color=interaction.guild.get_member(self.client.user.id).color))
            except AttributeError as e:
                print(e.__traceback__)
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed(f'`{emote_id}` is not a valid emote id.'))

            except Exception as e:
                print(e.__context__)
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_error_embed(f'Discord does not support this emote.'))
        else:
            await interaction.response.send_message(embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command'))


async def setup(client):
    await client.add_cog(SevenTV(client), guild=discord.Object(id=server_id))
