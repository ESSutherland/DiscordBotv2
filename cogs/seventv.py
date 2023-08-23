import io

import helpers.config
import helpers.embed_helper
import requests
import discord
import pillow_avif

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
            print(f'{interaction.user.name}({interaction.user.id}) executed 7TV command.')
            try:
                r = requests.get(url=f'{url}/emotes/{emote_id}', verify=False)
                r_json = r.json()

                file_list = r_json.get('host').get('files')

                await interaction.response.send_message(embed=discord.Embed(
                    title='Fetching Data...Please Wait.',
                    color=self.client.guilds[0].get_member(self.client.user.id).color
                ))

                for i in reversed(range(0, len(file_list))):
                    if 'avif' in file_list[i].get('name'):
                        try:
                            file_name = file_list[i].get('name')
                            print(file_name)
                            emote = await interaction.guild.create_custom_emoji(name=r_json.get("name"), image=await get_emote(r_json, file_name))
                            await interaction.edit_original_response(embed=await helpers.embed_helper.create_success_embed(
                                message=f'Emote `{r_json.get("name")}` has been added to the server!',
                                color=interaction.guild.get_member(self.client.user.id).color,
                                image=emote.url))
                            break
                        except:
                            if i > 0:
                                continue
                            else:
                                await interaction.edit_original_response(
                                    embed=await helpers.embed_helper.create_error_embed(
                                        f'`{r_json.get("name")}` is too large for Discord.'))

            except AttributeError as e:
                await interaction.edit_original_response(
                    embed=await helpers.embed_helper.create_error_embed(f'`{emote_id}` is not a valid emote id.'))
            except Exception as e:
                await interaction.edit_original_response(
                    embed=await helpers.embed_helper.create_error_embed(f'An Error occurred: {e.__traceback__}')
                )
        else:
            await interaction.edit_original_response(embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command'))


async def get_emote(data, file):
    emote_url = f'https:{data.get("host").get("url")}/{file}'
    image = Image.open(requests.get(emote_url, stream=True, verify=False).raw)
    buf = io.BytesIO()
    if data.get('animated'):
        image.save(buf, 'gif', save_all=True, disposal=2, loop=0, background=None, interlace=False)
    else:
        image.save(buf, 'png')

    return buf.getvalue()

async def setup(client):
    await client.add_cog(SevenTV(client), guild=discord.Object(id=server_id))
