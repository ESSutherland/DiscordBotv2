import sqlite3
import discord
import helpers.role_helper
import helpers.channel_helper
import helpers.embed_helper
import helpers.config
import requests
import emoji
import unicodedata
import math
import time

from discord.ext import commands
from configparser import ConfigParser
from PIL import Image, ImageDraw, ImageColor, ImageFont, ImageOps, ImageFilter
from colorsys import rgb_to_hls, hls_to_rgb
from discord import app_commands
from discord.ui import Button, View

# CONFIG INFO #
cfg = ConfigParser()
cfg.read('config.ini')

bot_prefix = cfg.get('Bot', 'command_prefix')
level_exp = int(cfg.get('Bot', 'level_exp'))
image = cfg.get('Bot', 'image_url')

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

server_id = helpers.config.server_id

description = 'Allows users to gain experience and levels for being active in the server.'


class LevelsView(View):
    prev_button = Button(label='Previous', style=discord.ButtonStyle.green, custom_id=f'prev_cmd{time.time()}')
    next_button = Button(label='Next', style=discord.ButtonStyle.green, custom_id=f'next_cmd{time.time()}')

    def __init__(self, embeds, max_pages):
        super().__init__()
        self.page = 1
        self.embeds = embeds
        self.max_pages = max_pages
        self.next_button.callback = self.button_callback
        self.prev_button.callback = self.button_callback
        self.add_item(self.prev_button)
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


class Levels(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        db.execute(
            'CREATE TABLE IF NOT EXISTS levels (user_id text unique, level integer default 1, exp real default 0.0)')
        connection.commit()
        print('Levels Module Loaded.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.DMChannel):
            msg_exp = 1
            author_id = message.author.id
            if not message.author.bot:
                multiplier = await get_multiplier(message.author, message.guild)

                if not await has_level(message.author.id):
                    db.execute('INSERT INTO levels(user_id) VALUES(?)', (author_id,))
                    connection.commit()

                user_exp = await get_exp(author_id)
                user_level = await get_level(author_id)

                if (user_exp + (msg_exp * multiplier)) >= level_exp:
                    await set_level(author_id, (user_level + 1))
                    await set_exp(author_id, (user_exp + (msg_exp * multiplier)) - level_exp)

                    if await helpers.channel_helper.is_channel_defined('bot'):
                        await message.guild.get_channel(await helpers.channel_helper.get_channel_id('bot')).send(
                            embed=await helpers.embed_helper.create_level_embed(
                                message.author,
                                await get_level(author_id),
                                self.client.guilds[0].get_member(self.client.user.id).color
                            )
                        )
                else:
                    await set_exp(author_id, user_exp + (msg_exp * multiplier))

    @app_commands.command(name='level', description='Displays the current level of the mentioned user.')
    async def level(self, interaction: discord.Interaction):

        print(f'{interaction.user}({interaction.user.id}) executed Level command.')

        user = interaction.user
        embed = discord.Embed(
            title=f'Rank: #{await get_rank(user.id) if await get_rank(user.id) > 0 else "N/A"}',
            description=f'Multiplier **{await get_multiplier(interaction.user, interaction.guild)}**',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        )
        embed.set_author(name=user.name, icon_url=user.display_avatar)

        embed.add_field(
            name='Level',
            value=f'{await get_level(user.id)}',
            inline=True
        )

        await helpers.embed_helper.add_blank_field(embed, True)

        embed.add_field(
            name=f'Exp to level {await get_level(user.id) + 1}',
            value=f'{float(await get_exp(user.id))}/{level_exp}',
            inline=True
        )

        embed.set_thumbnail(url=image)
        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(name='leaderboard', description='Displays leaderboard of player levels in the server.')
    async def leaderboard(self, interaction: discord.Interaction):

        print(f'{interaction.user}({interaction.user.id}) executed Leaderboard command.')
        embeds = []

        entry_per_page = 8

        first = ':first_place:'
        second = ':second_place:'
        third = ':third_place:'
        count = 1

        levels = await get_top_ranks()
        top = []

        for u in levels:
            if interaction.guild.get_member(int(u[0])):
                top.append(u)

        total_pages = math.ceil(len(top) / entry_per_page)

        for i in range(1, total_pages + 1):
            embed = discord.Embed(
                title=f'Leaderboard for levels in {interaction.guild.name}',
                color=self.client.guilds[0].get_member(self.client.user.id).color
            )
            number = min((entry_per_page * i), len(top))
            for j in range(entry_per_page * (i - 1), number):
                if count == 1:
                    user_rank = first
                elif count == 2:
                    user_rank = second
                elif count == 3:
                    user_rank = third
                else:
                    user_rank = f'-{count}-'

                embed.add_field(
                    name='\u200b',
                    value=f'**{user_rank} {interaction.guild.get_member(int(top[j][0])).name} **',
                    # value=f'**{user_rank} {top[j][0]} **',
                    inline=True
                )

                embed.add_field(
                    name='\u200b',
                    value=f'`Level: {top[j][1]}`',
                    inline=True
                )

                embed.add_field(
                    name='\u200b',
                    value=f'Exp: {top[j][2]}/{level_exp}',
                    inline=True
                )
                count += 1
            embeds.append(embed)
        view = LevelsView(embeds, total_pages)
        await interaction.response.send_message(
            embed=embeds[0],
            view=view
        )

    @app_commands.command(name='setexp', description='Set the amount of experience that each level takes.')
    async def set_exp(self, interaction: discord.Interaction, exp: int):
        if interaction.user.guild_permissions.administrator:
            print(f'{interaction.user}({interaction.user.id}) executed SetExp command.')

            if exp > 0:
                cfg_file = open('config.ini', 'w')
                cfg.set('Bot', 'level_exp', str(exp))
                cfg.write(cfg_file)
                cfg_file.close()
                await interaction.response.send_message(
                    embed=await helpers.embed_helper.create_success_embed(f'Set experience per level to `{exp}`', interaction.guild.get_member(self.client.user.id).color)
                )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

    @app_commands.command(name='user', description='Get a graphical layout of user info.')
    async def user(self, interaction: discord.Interaction):
        author = interaction.user

        print(f'{author}({author.id}) executed User command.')

        name = ''
        emojis = []
        for letter in author.name:
            if letter in emoji.UNICODE_EMOJI.get('en'):
                name += '%'
                if 'MODIFIER' not in unicodedata.name(letter):
                    emojis.append(letter)
            else:
                name += letter

        user_desc = f'{name} #{author.discriminator}'

        font_size = 1
        font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', font_size)
        while font.getsize(user_desc)[0] < 420 and font.getsize(user_desc)[1] < 60:
            font_size += 1
            font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', font_size)

        role_font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', 20)
        label_font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', 42)

        user_desc_size = font.getsize(user_desc)
        guild_name_size = label_font.getsize(interaction.guild.name)

        try:
            bg_image = Image.open(fp=f'./images/levels/{interaction.guild.id}.png')
        except FileNotFoundError:
            bg_image = Image.open(fp=f'./images/levels/BG.png')

        bg_image = bg_image.resize((840, 500))

        image_x, image_y = bg_image.size

        image_draw = ImageDraw.Draw(im=bg_image)

        avatar = Image.open(requests.get(author.display_avatar.url, stream=True).raw).convert('RGBA')
        avatar = avatar.resize((200, 200))
        mask = Image.open('./images/levels/mask.png').convert('L')
        output = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)

        rect = Image.new('RGBA', (image_x - 50, image_y - 50), color=(0, 0, 0, 120))

        user_exp = await get_exp(author.id)
        exp_bar = Image.new('RGBA', (450, 20), color=ImageColor.getrgb('#616161'))
        exp_bar_size = exp_bar.size
        user_exp_bar = Image.new('RGBA', (int(exp_bar_size[0] * (user_exp / level_exp)), 20),
                                 color=ImageColor.getrgb(
                                     str(self.client.guilds[0].get_member(self.client.user.id).color)))
        exp_bar.paste(user_exp_bar, (0, 0), user_exp_bar)

        user_joined = author.joined_at

        bg_image.paste(rect, (25, 25), rect)
        bg_image.paste(output, (40, 40), output)
        bg_image.paste(exp_bar, (240, 415), exp_bar)

        count = 0
        name_xy = (int((image_x / 2) - (user_desc_size[0] / 2)), 100)
        emoji_xy = [0, name_xy[1] + 5]

        emoji_font = ImageFont.truetype('./images/fonts/seguiemj.ttf', font_size)

        for section in user_desc.split('%'):
            if len(emojis) > 0 and count < len(emojis):
                emoji_xy[0] += (name_xy[0] + font.getsize(section)[0] + 5)
                image_draw.text(xy=tuple(emoji_xy), text=emojis[count], font=emoji_font, embedded_color=True)
                count += 1

        image_draw.text(xy=name_xy, text=user_desc.strip().replace('%', '  '), fill='white', font=font)
        image_draw.text(xy=(40, 190), text='Roles: ', font=label_font, fill='white')
        image_draw.text(xy=(40, 400), text=f'Level {await get_level(author.id)}', font=label_font, fill='white')
        image_draw.text(xy=(40, 320), text=f'Joined: {user_joined.strftime("%a, %b %d, %Y")}', font=label_font,
                        fill='white')
        image_draw.text(xy=(int((image_x / 2) - (guild_name_size[0] / 2)), 30), text=f'{interaction.guild.name}',
                        font=label_font, fill='white')
        image_draw.text(xy=(700, 415),
                        text=f'{user_exp if not user_exp.is_integer() else int(user_exp)}/{level_exp}',
                        font=role_font, fill='white')

        last_role = None
        start_roles = (150, 200)
        role_x, role_y = start_roles
        role_list = author.roles
        role_list.reverse()

        for role in role_list:
            role_size = role_font.getsize(role.name)
            if role.name != '@everyone':

                color_str = str(role.color) if (str(role.color) != '#000000') else '#b3b3b3'
                role_color = ImageColor.getrgb(color_str)

                darken = False
                for n in role_color:
                    if n > 230:
                        darken = True

                color_scale = 0.5
                additional = 0
                for n in role_color:
                    if n < 20:
                        color_scale = 5
                        additional = 10
                    else:
                        color_scale = 0.5
                        break

                text_color = lighten_color(role_color[0] + additional, role_color[1] + additional,
                                           role_color[2] + additional, color_scale) if not darken else darken_color(
                    role_color[0], role_color[1], role_color[2], color_scale)

                role_box = Image.new('RGBA', ((role_size[0] + 20), 40), color=role_color)
                role_box_size = role_box.size
                role_draw = ImageDraw.Draw(im=role_box)

                if last_role is not None:
                    role_x += (last_role[0] + 10)

                if role_x + role_box_size[0] > image_x - 50:
                    role_x = start_roles[0]
                    role_y += (role_box_size[1] + 10)

                text_x, text_y = ((role_box_size[0] / 2 - role_size[0] / 2), (role_box_size[1] / 2 - 30 / 3))

                role_draw.text(xy=(text_x, text_y), text=role.name, font=role_font, fill=tuple(text_color))
                role_box = add_corners(role_box, 20)
                bg_image.paste(role_box, (role_x, role_y), role_box)

                last_role = role_box_size

        bg_image.save('./images/levels/last_user.png')

        await interaction.response.send_message(file=discord.File(fp='./images/levels/last_user.png'))


async def has_level(user_id):
    db.execute('SELECT * FROM levels WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False


async def get_exp(user_id):
    db.execute('SELECT exp FROM levels WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return float(row[0])
    else:
        return 0.0


async def get_level(user_id):
    db.execute('SELECT level FROM levels WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return int(row[0])
    else:
        return 0


async def set_exp(user_id, exp):
    db.execute('UPDATE levels SET exp=? WHERE user_id=?', (exp, user_id))
    connection.commit()


async def set_level(user_id, level):
    db.execute('UPDATE levels SET level=? WHERE user_id=?', (level, user_id))
    connection.commit()


async def get_rank(user_id):
    db.execute('SELECT * FROM levels ORDER BY level DESC, exp DESC')
    results = db.fetchall()
    rank = 0

    if await get_level(user_id) > 0:
        for user in results:
            rank += 1
            if user[0] == str(user_id):
                return rank
    return rank


async def get_top_ranks():
    db.execute('SELECT * FROM levels ORDER BY level DESC, exp DESC')
    results = db.fetchall()

    return results


async def get_multiplier(user, guild):
    author_id = user.id
    multiplier = 1
    if await helpers.role_helper.is_role_defined('sub'):
        if await helpers.role_helper.has_role(guild, author_id, 'sub'):
            multiplier = 1.5

    if await helpers.role_helper.is_role_defined('booster'):
        if await helpers.role_helper.has_role(guild, author_id, 'booster'):
            multiplier = 2

    return multiplier


async def setup(client):
    await client.add_cog(Levels(client), guild=discord.Object(id=server_id))


# FUNCTIONS FOUND ONLINE #

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im


def adjust_color_lightness(r, g, b, factor):
    h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def lighten_color(r, g, b, factor=0.1):
    return adjust_color_lightness(r, g, b, 1 + factor)


def darken_color(r, g, b, factor=0.1):
    return adjust_color_lightness(r, g, b, 1 - factor)
