import discord

from mal import Anime, Manga, config, AnimeSearch, MangaSearch
from discord.ext import commands

description = 'Allows users to search and display data on Anime and Manga via MyAnimeList.'

class AnimeModule(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Anime Module Loaded')

    @commands.command(name='anime')
    async def anime(self, ctx, *, params):
        await ctx.send(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        search = AnimeSearch(params)
        anime_data = search.results[0]

        message_id = ctx.channel.last_message_id

        anime_data_2 = Anime(anime_data.mal_id)

        message = await ctx.channel.fetch_message(message_id)
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

        await ctx.send(embed=embed)

    @commands.command(name='manga')
    async def manga(self, ctx, *, params):
        await ctx.send(embed=discord.Embed(
            title='Fetching Data...Please Wait.',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        ))

        search = MangaSearch(params)
        manga_data = search.results[0]

        message_id = ctx.channel.last_message_id

        manga_data_2 = Manga(manga_data.mal_id)

        message = await ctx.channel.fetch_message(message_id)
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

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(AnimeModule(client))
