import pokepy
import discord
import requests
import helpers.embed_helper
import helpers.config
import time

from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

description = 'Allow users to get information on a specified pokemon'

server_id = helpers.config.server_id

img_url = 'https://essutherland.github.io/bot-site/images/'

p_client = pokepy.V2Client()

class PokemonView(View):
    prev_button = Button(label='Previous Form', style=discord.ButtonStyle.green, custom_id=f'prev_poke{time.time()}')
    shiny_button = Button(label='Toggle Shiny', style=discord.ButtonStyle.blurple, custom_id=f'shiny_poke{time.time()}', emoji='✨')
    next_button = Button(label='Next Form', style=discord.ButtonStyle.green, custom_id=f'next_poke{time.time()}')

    def __init__(self, embeds, max_pages, pokemon_ids):
        super().__init__()
        self.page = 1
        self.shiny = False
        self.embeds = embeds
        self.max_pages = max_pages
        self.pokemon_ids = pokemon_ids
        self.next_button.callback = self.button_callback
        self.prev_button.callback = self.button_callback
        self.shiny_button.callback = self.shiny_callback
        self.add_item(self.prev_button)
        self.add_item(self.shiny_button)
        self.add_item(self.next_button)
        self.disable_buttons()

    async def button_callback(self, interaction: discord.Interaction):
        button_id = interaction.data['custom_id']
        if button_id == self.next_button.custom_id:
            self.page += 1
        elif button_id == self.prev_button.custom_id:
            self.page -= 1

        self.disable_buttons()

        embed = self.embeds[self.page - 1]
        self.shiny = False
        self.update_image(embed)
        await interaction.response.edit_message(embed=embed, view=self)

    async def shiny_callback(self, interaction: discord.Interaction):
        button_id = interaction.data['custom_id']
        embed: discord.Embed = self.embeds[self.page - 1]
        if button_id == self.shiny_button.custom_id:
            self.shiny = not self.shiny
            self.update_image(embed)

        await interaction.response.edit_message(embed=embed, view=self)

    def disable_buttons(self):
        if self.page <= 1:
            self.prev_button.disabled = True
        else:
            self.prev_button.disabled = False
        if self.page == self.max_pages:
            self.next_button.disabled = True
        else:
            self.next_button.disabled = False

    def update_image(self, embed):
        # url_list = embed.image.url.split('/')
        # file_name = url_list[len(url_list) - 1]
        # file_list = file_name.split('_')
        if self.shiny:
            # if len(file_list) < 6:
            #     file_name = f'{file_name[:-4]}_s.png'
            #     embed.set_image(url=f'{img_url}{file_name}')
            embed.set_image(url=get_image(self.pokemon_ids[self.page-1], True))
            embed.set_footer(text=f'Forms [{self.page}/{self.max_pages}] ✨')
        else:
            # if len(file_list) > 5:
            #     file_name = f'{file_name[:-6]}.png'
            #     embed.set_image(url=f'{img_url}{file_name}')
            embed.set_image(url=get_image(self.pokemon_ids[self.page-1], False))
            embed.set_footer(text=f'Forms [{self.page}/{self.max_pages}]')

class PokemonModule(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Pokemon Module Loaded.')

    @app_commands.command(name='pokemon', description='Get information about the specified Pokemon.')
    async def _pokemon(self, interaction: discord.Interaction, name_or_id: str):
        print(f'{interaction.user.name}({interaction.user.id}) executed Pokemon command.')

        name_or_id = name_or_id.lower()
        if ('.' in name_or_id) and (' ' in name_or_id):
            name_or_id = name_or_id.replace('.', '',)
            name_or_id = name_or_id.replace(' ', '-')
        elif '.' in name_or_id:
            name_or_id = name_or_id.replace('.', '-')
        elif ' ' in name_or_id:
            name_or_id = name_or_id.replace(' ', '-')

        embeds = []
        pokemon_ids = []

        await interaction.response.send_message(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        try:
            poke_search = int(name_or_id)
        except:
            poke_search = name_or_id.lower()

        try:
            poke_species = p_client.get_pokemon_species(poke_search)[0]

            poke = p_client.get_pokemon(poke_species.id)[0]

            blocked_forms = ['-rock-star', '-belle', '-pop-star', '-phd', '-libre', '-cosplay', '-totem', '-unknown']
            accepted_forms = []

            for f in poke_species.varieties:
                f_mon = p_client.get_pokemon(f.pokemon.name)[0]
                a = True
                for x in blocked_forms:
                    if x in f_mon.name:
                        a = False
                if a:
                    poke_form = f_mon.forms[0]
                    b = True
                    for y in accepted_forms:
                        if poke_form.name == y.name:
                            b = False
                    if b:
                        accepted_forms.append(poke_form)

            # for f2 in poke.forms:
            #     a2 = True
            #     for x in blocked_forms:
            #         if x in f2.name:
            #             a2 = False
            #     if a2:
            #         b2 = True
            #         for y in accepted_forms:
            #             if f2.name == y.name:
            #                 b2 = False
            #         if b2:
            #             accepted_forms.append(f2)

            print(accepted_forms)

            for j in range(1, len(accepted_forms)+1):
                form = p_client.get_pokemon_form(accepted_forms[j-1].name)[0]
                poke = p_client.get_pokemon(form.pokemon.name)[0]

                file_name = ''
                # image_file = None
                # gender_options = ['mf', 'md', 'fd', 'mo', 'fo', 'uk']
                #
                # for i in range(0, len(gender_options)):
                #     file_name = f'{poke_species.id}_{j - 1 if len(accepted_forms) > 1 else 0}_{gender_options[i]}_{"g" if "gmax" in poke.name else "n"}_0.png'
                #     image_string = f'{img_url}{file_name}'
                #
                #     req = requests.get(image_string)
                #     if req.status_code == 200:
                #         break
                #     else:
                #         file_name = ''
                #
                # if len(file_name) == 0:
                #     for x in range(0, len(gender_options)):
                #         file_name = f'{poke_species.id}_0_{gender_options[x]}_{"g" if "gmax" in poke.name else "n"}_0.png'
                #         image_string = f'{img_url}{file_name}'
                #         req2 = requests.get(image_string)
                #         if req2.status_code == 200:
                #             break
                #         else:
                #             continue

                poke_name = get_english(poke_species.names)
                try:
                    poke_form = p_client.get_pokemon(form.name)[0]
                except:
                    poke_form = p_client.get_pokemon(form.id)[0]

                type_names = []
                type_string = ''

                for poke_type in poke_form.types:
                    types = p_client.get_type(poke_type.type.name)[0]
                    type_name = get_english(types.names)
                    type_names.append(type_name)
                    if poke_form.types.index(poke_type) == 0:
                        type_string += f'{type_name}'
                    else:
                        type_string += f', {type_name}'

                ability_names = []
                ability_string = ''

                for ability in poke.abilities:
                    ability_data = p_client.get_ability(ability.ability.name)[0]
                    ability_name = get_english(ability_data.names)
                    ability_names.append(ability_name)
                    if poke.abilities.index(ability) == 0:
                        ability_string += f'{ability_name}'
                    else:
                        if ability.is_hidden:
                            ability_string += f', **{ability_name}**'
                        else:
                            ability_string += f', {ability_name}'

                embed = discord.Embed(
                    title=f'{poke_name} - #{poke_species.id} {f"({get_english(form.names)})" if len(form.names) > 0 else ""}',
                    color=self.client.guilds[0].get_member(self.client.user.id).color,
                    description=get_genus(poke_species.genera)
                )
                embed.set_image(url=f'{get_image(poke.id, False)}')
                embed.add_field(name='Type(s)', value=type_string, inline=True)
                embed.add_field(name='Abilities', value=ability_string, inline=True)
                embed.add_field(name='Height/Weight', value=f'{"{:.1f}".format(poke.height*0.1)} m/{"{:.1f}".format(poke.weight*0.1)} kg')

                for stat in poke.stats:
                    stat_data = p_client.get_stat(stat.stat.name)[0]
                    embed.add_field(name=get_english(stat_data.names), value=stat.base_stat, inline=True)

                embed.set_footer(text=f'Forms [{j}/{len(accepted_forms)}]')

                embeds.append(embed)
                pokemon_ids.append(poke.id)

            view = PokemonView(embeds=embeds, max_pages=len(accepted_forms), pokemon_ids=pokemon_ids)
            await interaction.edit_original_response(embed=embeds[0], view=view)

        except Exception:
            await interaction.edit_original_response(embed=await helpers.embed_helper.create_error_embed(f'Unable to find data on `{poke_search}`.'))
            raise

def get_english(names):
    for x in names:
        if x.language.name == 'en':
            return x.name

def get_genus(genera):
    for x in genera:
        if x.language.name == 'en':
            return x.genus

def get_image(id, shiny):
    url = ''
    if shiny:
        url = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/'
    else:
        url = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/'

    return f'{url}{id}.png'

async def setup(client):
    await client.add_cog(PokemonModule(client), guild=discord.Object(id=server_id))
