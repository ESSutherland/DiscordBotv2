import pokebase as pb
import discord
import asyncio
import requests
import helpers.embed_helper

from discord.ext import commands
from pokebase import cache

description = 'Allow users to get information on a specified pokemon'

messages = []
img_url = 'https://essutherland.github.io/bot-site/images/'

class PokemonModule(commands.Cog):

    def __init__(self, client):
        self.client = client
        cache.set_cache('./images/pokemon')

    @commands.Cog.listener()
    async def on_ready(self):
        print('Pokemon Module Loaded.')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message = await self.client.guilds[0].get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message in messages:
            if payload.emoji.name == '✨' and not payload.member.bot:
                embed = message.embeds[0]
                url_list = embed.image.url.split('/')
                file_name = url_list[len(url_list)-1]
                file_list = file_name.split('_')
                footer = f'{embed.footer.text if embed.footer.text != discord.Embed.Empty else ""} (Shiny)'
                if len(file_list) < 6:
                    file_name = f'{file_name[:-4]}_s.png'
                    embed.set_image(url=f'{img_url}{file_name}')
                    embed.set_footer(text=footer)
                    await message.edit(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message = await self.client.guilds[0].get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message in messages:
            if payload.emoji.name == '✨':
                embed = message.embeds[0]
                url_list = embed.image.url.split('/')
                file_name = url_list[len(url_list) - 1]
                file_list = file_name.split('_')
                footer = embed.footer.text.replace('(Shiny)', ' ')
                if len(file_list) > 5:
                    file_name = f'{file_name[:-6]}.png'
                    embed.set_image(url=f'{img_url}{file_name}')
                    embed.set_footer(text=footer)
                    await message.edit(embed=embed)

    @commands.command(name='pokemon')
    async def pokemon(self, ctx, poke_name_or_id, page=1):
        print(f'{ctx.author}({ctx.author.id}) executed Pokemon command.')

        message = await ctx.send(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        try:
            poke_search = int(poke_name_or_id)
        except:
            poke_search = poke_name_or_id.lower()

        try:
            poke_species = pb.pokemon_species(poke_search)
            if page < 1:
                pass
            else:

                poke = pb.pokemon(poke_species.id)

                blocked_forms = ['-rock-star', '-belle', '-pop-star', '-phd', '-libre', '-cosplay', '-totem', '-unknown']
                accepted_forms = []

                for f in poke_species.varieties:
                    a = True
                    for x in blocked_forms:
                        if x in f.pokemon.name:
                            a = False
                    if a:
                        poke_form = f.pokemon.forms[0]
                        b = True
                        for y in accepted_forms:
                            if poke_form.name == y.name:
                                b = False
                        if b:
                            accepted_forms.append(poke_form)

                for f2 in poke.forms:
                    a2 = True
                    for x in blocked_forms:
                        if x in f2.name:
                            a2 = False
                    if a2:
                        b2 = True
                        for y in accepted_forms:
                            if f2.name == y.name:
                                b2 = False
                        if b2:
                            accepted_forms.append(f2)

                form = pb.pokemon_form(accepted_forms[page-1].name)
                poke = pb.pokemon(form.pokemon.name)

                file_name = ''
                image_file = None
                gender_options = ['mf', 'md', 'fd', 'mo', 'fo', 'uk']

                for i in range(0, len(gender_options)):
                    file_name = f'{poke_species.id}_{page - 1 if len(accepted_forms) > 1 else 0}_{gender_options[i]}_{"g" if "gmax" in poke.name else "n"}_0.png'
                    image_string = f'{img_url}{file_name}'

                    req = requests.get(image_string)
                    if req.status_code == 200:
                        break
                    else:
                        file_name = ''

                if len(file_name) == 0:
                    for x in range(0, len(gender_options)):
                        file_name = f'{poke_species.id}_0_{gender_options[x]}_{"g" if "gmax" in poke.name else "n"}_0.png'
                        image_string = f'{img_url}{file_name}'
                        req2 = requests.get(image_string)
                        if req2.status_code == 200:
                            break
                        else:
                            continue

                poke_name = get_english(poke_species.names)

                type_names = []
                type_string = ''

                for poke_type in form.types:
                    types = pb.type_(poke_type.type.name)
                    type_name = get_english(types.names)
                    type_names.append(type_name)
                    if form.types.index(poke_type) == 0:
                        type_string += f'{type_name}'
                    else:
                        type_string += f', {type_name}'

                ability_names = []
                ability_string = ''

                for ability in poke.abilities:
                    ability_data = pb.ability(ability.ability.name)
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
                embed.set_image(url=f'{img_url}{file_name}')
                embed.add_field(name='Type(s)', value=type_string, inline=True)
                embed.add_field(name='Abilities', value=ability_string, inline=True)
                embed.add_field(name='Height/Weight', value=f'{"{:.1f}".format(poke.height*0.1)} m/{"{:.1f}".format(poke.weight*0.1)} kg')

                for stat in poke.stats:
                    stat_data = pb.stat(stat.stat.name)
                    embed.add_field(name=get_english(stat_data.names), value=stat.base_stat, inline=True)

                if len(accepted_forms) > 1:
                    embed.set_footer(text=f'Forms [{page}/{len(accepted_forms)}]')

                msg = await ctx.send(embed=embed)
                await msg.add_reaction("✨")
                messages.append(msg)

        except:
            await ctx.send(embed=await helpers.embed_helper.create_error_embed(f'Unable to get info on `{poke_name_or_id}`. Please make sure you used the correct name or number.'))

        await message.delete()

def get_english(names):
    for x in names:
        if x.language.name == 'en':
            return x.name

def get_genus(genera):
    for x in genera:
        if x.language.name == 'en':
            return x.genus

def setup(client):
    client.add_cog(PokemonModule(client))
