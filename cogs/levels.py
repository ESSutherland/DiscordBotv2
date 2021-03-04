import sqlite3
import discord
import helpers.role_helper
import helpers.channel_helper
import helpers.embed_helper
import requests

from discord.ext import commands
from configparser import ConfigParser
from cogs.customcommands import is_command
from PIL import Image, ImageDraw, ImageColor, ImageFont, ImageOps, ImageFilter
from colorsys import rgb_to_hls, hls_to_rgb

# CONFIG INFO #
cfg = ConfigParser()
cfg.read('config.ini')

bot_prefix = cfg.get('Bot', 'command_prefix')
level_exp = int(cfg.get('Bot', 'level_exp'))
image = cfg.get('Bot', 'image_url')

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

description = 'Allows users to gain experience and levels for being active in the server.'

class Levels(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS levels (user_id text unique, level integer default 1, exp real default 0.0)')
        connection.commit()
        print('Levels Module Loaded.')

    @commands.Cog.listener()
    async def on_message(self, message):
        msg_exp = 1
        author_id = message.author.id
        if not message.author.bot:
            if not message.content.startswith(bot_prefix) and not await is_command(message.content):
                multiplier = await get_multiplier(message)

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

    @commands.command(name='level')
    async def level(self, ctx):

        print(f'{ctx.author}({ctx.author.id}) executed Level command.')

        user = ctx.author
        embed = discord.Embed(
            title=f'Rank: #{await get_rank(user.id) if await get_rank(user.id) > 0 else "N/A"}',
            description=f'Multiplier **{await get_multiplier(ctx)}**',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        )
        embed.set_author(name=user.name, icon_url=user.avatar_url)

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
        await ctx.send(
            embed=embed
        )

    @commands.command(name='leveltop')
    async def level_top(self, ctx):

        print(f'{ctx.author}({ctx.author.id}) executed LevelTop command.')

        first = ':first_place:'
        second = ':second_place:'
        third = ':third_place:'
        count = 1

        embed = discord.Embed(
            title=f'Top 5 levels in {ctx.guild.name}',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        )

        top5 = await get_top_ranks()
        for users in top5:
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
                value=f'**{user_rank} {ctx.guild.get_member(int(users[0])).mention} **',
                inline=True
            )

            embed.add_field(
                name='\u200b',
                value=f'`Level: {users[1]}`',
                inline=True
            )

            embed.add_field(
                name='\u200b',
                value=f'Exp: {users[2]}/{level_exp}',
                inline=True
            )
            count += 1

        await ctx.send(
            embed=embed
        )

    @commands.command(name='setexp')
    @commands.has_permissions(administrator=True)
    async def set_exp(self, ctx, exp):

        print(f'{ctx.author}({ctx.author.id}) executed SetExp command.')

        if int(exp) > 0:
            cfg_file = open('config.ini', 'w')
            cfg.set('Bot', 'level_exp', exp)
            cfg.write(cfg_file)
            cfg_file.close()

    @commands.command(name='user')
    async def user(self, ctx, user=None):

        print(f'{ctx.author}({ctx.author.id}) executed User command.')

        author = ctx.author
        if user is not None:
            if len(ctx.message.mentions) > 0:
                author = ctx.message.mentions[0]

        name = author.name
        user_desc = f'{name}#{author.discriminator}'

        font_size = 1
        font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', font_size)
        while font.getsize(user_desc)[0] < 420 and font.getsize(user_desc)[1] < 60:
            font_size += 1
            font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', font_size)

        role_font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', 20)
        label_font = ImageFont.truetype('./images/fonts/Oleg Stepanov - SimpleStamp.otf', 42)

        user_desc_size = font.getsize(user_desc)

        bg_image = Image.open(fp='./images/levels/BG.png')
        image_x, image_y = bg_image.size
        image_draw = ImageDraw.Draw(im=bg_image)

        avatar = Image.open(requests.get(author.avatar_url, stream=True).raw).convert('RGBA')
        avatar = avatar.resize((200, 200))
        mask = Image.open('./images/levels/mask.png').convert('L')
        output = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)

        rect = Image.new('RGBA', (image_x - 50, image_y - 50), color=(0, 0, 0, 70))

        user_exp = await get_exp(author.id)
        exp_bar = Image.new('RGBA', (450, 20), color=ImageColor.getrgb('#616161'))
        exp_bar_size = exp_bar.size
        user_exp_bar = Image.new('RGBA', (int(exp_bar_size[0]*(user_exp/level_exp)), 20),
                                 color=ImageColor.getrgb(str(self.client.guilds[0].get_member(self.client.user.id).color)))
        exp_bar.paste(user_exp_bar, (0, 0), user_exp_bar)

        user_joined = author.joined_at

        bg_image.paste(rect, (25, 25), rect)
        bg_image.paste(output, (40, 40), output)
        bg_image.paste(exp_bar, (240, 415), exp_bar)

        image_draw.text(xy=(int((image_x/2)-(user_desc_size[0]/2)), 80), text=user_desc, fill='white', font=font)
        image_draw.text(xy=(40, 190), text='Roles: ', font=label_font, fill='white')
        image_draw.text(xy=(40, 400), text=f'Level {await get_level(author.id)}', font=label_font, fill='white')
        image_draw.text(xy=(40, 320), text=f'Joined: {user_joined.strftime("%a, %b %d, %Y")}', font=label_font, fill='white')
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

                print(role_color)

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

                text_color = lighten_color(role_color[0] + additional, role_color[1] + additional, role_color[2] + additional, color_scale) if not darken else darken_color(role_color[0], role_color[1], role_color[2], color_scale)

                role_box = Image.new('RGBA', ((role_size[0] + 20), 40), color=role_color)
                role_box_size = role_box.size
                role_draw = ImageDraw.Draw(im=role_box)

                if last_role is not None:
                    role_x += (last_role[0] + 10)

                if role_x + role_box_size[0] > image_x-50:
                    role_x = start_roles[0]
                    role_y += (role_box_size[1] + 10)

                text_x, text_y = ((role_box_size[0]/2 - role_size[0]/2), (role_box_size[1]/2 - 30/3))

                role_draw.text(xy=(text_x, text_y), text=role.name, font=role_font, fill=tuple(text_color))
                role_box = add_corners(role_box, 20)
                bg_image.paste(role_box, (role_x, role_y), role_box)

                last_role = role_box_size

        bg_image.save('./images/levels/last_user.png')

        await ctx.send(file=discord.File(fp='./images/levels/last_user.png'))

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
    db.execute('SELECT * FROM levels ORDER BY level DESC, exp DESC LIMIT 5')
    results = db.fetchall()

    return results

async def get_multiplier(message):
    author_id = message.author.id
    multiplier = 1
    if await helpers.role_helper.is_role_defined('sub'):
        if await helpers.role_helper.has_role(message.guild, author_id, 'sub'):
            multiplier = 1.5

    if await helpers.role_helper.is_role_defined('booster'):
        if await helpers.role_helper.has_role(message.guild, author_id, 'booster'):
            multiplier = 2

    return multiplier

def setup(client):
    client.add_cog(Levels(client))

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
