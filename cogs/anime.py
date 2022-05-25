import discord

from mal import Anime, Manga, AnimeSearch, MangaSearch
from discord.ext import commands
from discord.ui import Button, View

description = 'Allows users to search and display data on Anime and Manga via MyAnimeList.'

class AnimeModule(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Anime Module Loaded')

    @commands.command(name='anime')
    @commands.guild_only()
    async def anime(self, ctx, *, params):
        print(f'{ctx.author}({ctx.author.id}) executed Anime command.')
        message = await ctx.send(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        search = AnimeSearch(params)
        anime_data = search.results[0]

        anime_data_2 = Anime(anime_data.mal_id)

        await message.delete()

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

        await ctx.send(embed=embed, view=view)

    @commands.command(name='manga')
    @commands.guild_only()
    async def manga(self, ctx, *, params):
        print(f'{ctx.author}({ctx.author.id}) executed Manga command.')
        message = await ctx.send(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        search = MangaSearch(params)
        manga_data = search.results[0]

        manga_data_2 = Manga(manga_data.mal_id)

        await message.delete()

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

        await ctx.send(embed=embed, view=view)

async def setup(client):
    await client.add_cog(AnimeModule(client))
