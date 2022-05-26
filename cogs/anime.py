import discord
import helpers.config
import helpers.embed_helper

from mal import Anime, Manga, AnimeSearch, MangaSearch
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

description = 'Allows users to search and display data on Anime and Manga via MyAnimeList.'

server_id = helpers.config.server_id

class AnimeModule(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Anime Module Loaded')

    @app_commands.command(name='anime', description='Display info about a specified anime (via MyAnimeList).')
    async def anime(self, interaction: discord.Interaction, params: str):
        print(f'{interaction.user}({interaction.user.id}) executed Anime command.')

        await interaction.response.send_message(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        search = AnimeSearch(params)

        if len(search.results) > 0:
            anime_data = search.results[0]

            anime_data_2 = Anime(anime_data.mal_id)

            print(anime_data_2.title)

            embed = discord.Embed(
                title=anime_data.title,
                description=anime_data_2.title_japanese,
                color=self.client.guilds[0].get_member(self.client.user.id).color,
                url=anime_data.url
            )
            embed.set_image(url=anime_data.image_url)
            embed.add_field(
                name='Synopsis',
                value=anime_data.synopsis,
                inline=False
            )
            embed.add_field(
                name='Episodes',
                value=str(anime_data_2.episodes),
                inline=True
            )
            embed.add_field(
                name='Status',
                value=str(anime_data_2.status),
                inline=True
            )
            embed.add_field(
                name='Score',
                value=str(anime_data.score),
                inline=True
            )

            embed.set_footer(text=f'Aired: {anime_data_2.aired}')

            button = Button(label='View on site', style=discord.ButtonStyle.url, url=anime_data_2.url)
            view = View()
            view.add_item(button)

            await interaction.edit_original_message(embed=embed, view=view)
        else:
            await interaction.edit_original_message(embed=await helpers.embed_helper.create_error_embed(f'Could not find any anime similar to {params}'))

    @app_commands.command(name='manga', description='Display info about a specified manga (via MyAnimeList).')
    async def manga(self, interaction: discord.Interaction, params: str):
        print(f'{interaction.user}({interaction.user.id}) executed Manga command.')
        await interaction.response.send_message(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        search = MangaSearch(params)

        if len(search.results) > 0:
            manga_data = search.results[0]

            manga_data_2 = Manga(manga_data.mal_id)

            embed = discord.Embed(
                title=manga_data.title,
                description=manga_data_2.title_japanese,
                color=self.client.guilds[0].get_member(self.client.user.id).color,
                url=manga_data.url
            )
            embed.set_image(url=manga_data.image_url)
            embed.add_field(
                name='Synopsis',
                value=manga_data.synopsis,
                inline=False
            )
            embed.add_field(
                name='Volumes',
                value=str(manga_data_2.volumes),
                inline=True
            )
            embed.add_field(
                name='Status',
                value=str(manga_data_2.status),
                inline=True
            )
            embed.add_field(
                name='Score',
                value=str(manga_data.score),
                inline=True
            )

            embed.set_footer(text=f'Published: {manga_data_2.published}')

            button = Button(label='View on site', style=discord.ButtonStyle.url, url=manga_data_2.url)
            view = View()
            view.add_item(button)

            await interaction.edit_original_message(embed=embed, view=view)
        else:
            await interaction.edit_original_message(embed=await helpers.embed_helper.create_error_embed(f'Could not find any manga similar to {params}'))

async def setup(client):
    await client.add_cog(AnimeModule(client), guild=discord.Object(id=server_id))
