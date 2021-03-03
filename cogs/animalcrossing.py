import sqlite3
import discord
import requests
import helpers.embed_helper

from discord.ext import commands
from PIL import Image, ImageDraw, ImageColor, ImageFont

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

description = 'Allows users to run a command to get information about a specified Animal Crossing New Horizons Villager.'

class AnimalCrossing(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS villagers ('
                   'id text, file_name text, name text, personality text, birthday text, species text,'
                   'gender text, icon text, image text, bubble_color text, text_color text, '
                   'catchphrase text, hobby text)')
        connection.commit()
        print('Animal Crossing Module Loaded.')

    @commands.command(name='villager')
    async def villager(self, ctx, villager_name):
        print(f'{ctx.author}({ctx.author.id}) executed Villager command.')
        if await is_villager(villager_name):
            villager = await get_villager_data(villager_name)
            box_color = '#ded9c6'
            text_color = '#7c7056'

            month, day = villager.get('birthday').split(' ')

            font = ImageFont.truetype('./images/fonts/FOT-RodinHimawariPro-UB.otf', 32)
            font2 = ImageFont.truetype('./images/fonts/FOT-RodinHimawariPro-UB.otf', 24)

            text_size = font.getsize(villager.get('name'))
            catch_size = font2.getsize(f'"{villager.get("catchphrase")}"')
            birth_size = font2.getsize(f'{villager.get("birthday")}')
            personality_size = font2.getsize(f'Personality: {villager.get("personality")}')
            species_size = font2.getsize(f'Species: {villager.get("species")}')
            gender_size = font2.getsize(f'Gender: {villager.get("gender")}')
            hobby_size = font2.getsize(f'Hobby: {villager.get("hobby")}')

            color_image = create_rounded_rectangle_mask((text_size[0] + 60, 56), 20, villager.get('bubble_color'))
            catch_image = create_rounded_rectangle_mask((catch_size[0]+30, catch_size[1]+10), 10, box_color)
            birth_image = create_rounded_rectangle_mask((birth_size[0], birth_size[1]+10), 10)
            personality_image = create_rounded_rectangle_mask((personality_size[0]+30, personality_size[1]+10), 10)
            species_image = create_rounded_rectangle_mask((species_size[0]+30, species_size[1]+10), 10)
            gender_image = create_rounded_rectangle_mask((gender_size[0]+30, gender_size[1]+10), 10)
            hobby_image = create_rounded_rectangle_mask((hobby_size[0]+30, hobby_size[1]+10), 10)

            color_draw = ImageDraw.Draw(color_image)
            catch_draw = ImageDraw.Draw(catch_image)
            birth_draw = ImageDraw.Draw(birth_image)
            personality_draw = ImageDraw.Draw(personality_image)
            species_draw = ImageDraw.Draw(species_image)
            gender_draw = ImageDraw.Draw(gender_image)
            hobby_draw = ImageDraw.Draw(hobby_image)

            color_w, color_h = color_image.size
            catch_w, catch_h = catch_image.size
            birth_w, birth_h = birth_image.size
            personality_w, personality_h = personality_image.size
            species_w, species_h = species_image.size
            gender_w, gender_h = gender_image.size
            hobby_w, hobby_h = hobby_image.size

            color_draw.text((int(((color_w/2)-(text_size[0]/2))), int((color_h/2)-(56/3))), villager.get('name'), font=font, fill=villager.get('text_color'))
            catch_draw.text((int((catch_w/2)-(catch_size[0]/2)), int((catch_h/2)-(catch_size[1]/2))), f'"{villager.get("catchphrase")}"', font=font2, fill=text_color)
            birth_draw.text((int((birth_w/2)-(birth_size[0]/2)), int((birth_h/2)-(birth_size[1]/2))), f'{villager.get("birthday")}', font=font2, fill=text_color)
            personality_draw.text((int((personality_w/2)-(personality_size[0]/2)), int((personality_h/2)-(personality_size[1]/2))), f'Personality: {villager.get("personality")}', font=font2, fill=text_color)
            species_draw.text((int((species_w/2)-(species_size[0]/2)), int((species_h/2)-(species_size[1]/2))), f'Species: {villager.get("species")}', font=font2, fill=text_color)
            gender_draw.text((int((gender_w/2)-(gender_size[0]/2)), int((gender_h/2)-(gender_size[1]/2))), f'Gender: {villager.get("gender")}', font=font2, fill=text_color)
            hobby_draw.text((int((hobby_w/2)-(hobby_size[0]/2)), int((hobby_h/2)-(hobby_size[1]/2))), f'Hobby: {villager.get("hobby")}', font=font2, fill=text_color)

            template = Image.open(fp='./images/animalcrossing/villager_box.png')
            image = Image.open(requests.get(villager.get('image'), stream=True).raw)
            icon = Image.open(requests.get(villager.get('icon'), stream=True).raw)
            sign = Image.open(fp=f'./images/animalcrossing/{get_sign(month, day)}.png').convert("RGBA")
            sign = sign.resize((40, 40))
            cake = Image.open(fp=f'./images/animalcrossing/birthday.png').convert("RGBA")
            cake = cake.resize((30, 30))
            image = image.resize((256, 256))
            image = add_corners(image, 50)
            icon = icon.resize((64, 64))
            icon_w, icon_h = icon.size

            cake_w, cake_h = cake.size

            alpha = cake.getchannel('A')
            bday = Image.new('RGBA', cake.size, color=text_color)
            bday.putalpha(alpha)

            template.paste(color_image, (50, 20), color_image)
            template.paste(catch_image, (400 + icon_w, 90), catch_image)
            template.paste(birth_image, (int(77+(256/2)-(birth_w/2)), 400), birth_image)
            template.paste(sign, (int(int(77+(256/2)+(birth_w/2)+10)), 395), sign)
            template.paste(bday, (int(int(77 + (256 / 2) - (birth_w / 2) - (cake_w + 10))), 400), bday)
            template.paste(personality_image, (400, 160), personality_image)
            template.paste(species_image, (400, 225), species_image)
            template.paste(gender_image, (400, 290), gender_image)
            template.paste(hobby_image, (400, 355), hobby_image)
            template.paste(image, (77, 120), image)
            template.paste(icon, (400, int(90-(icon_h/4))), icon)

            template.save('./images/animalcrossing/last_villager.png')

            await ctx.send(
                file=discord.File(fp='./images/animalcrossing/last_villager.png')
            )

        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'Villager `{villager_name}` not Found! This command only supports villagers from Animal Crossing: New Horizons.'
                )
            )

    @commands.command(name='updatevillagers')
    async def update_villagers(self, ctx):
        await update_villager_db()

        await ctx.send(embed=await helpers.embed_helper.create_success_embed('Villager data updated!', self.client.guilds[0].get_member(self.client.user.id).color))

async def is_villager(villager_name):
    db.execute('SELECT * FROM villagers WHERE LOWER(name) LIKE ?', (villager_name.lower(),))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_villager_data(villager_name):
    db.execute('SELECT * FROM villagers WHERE LOWER(name) LIKE ?', (villager_name.lower(),))
    row = db.fetchone()

    villager_dict = {
        'id': row[0],
        'file_name': row[1],
        'name': row[2],
        'personality': row[3],
        'birthday': row[4],
        'species': row[5],
        'gender': row[6],
        'icon': row[7],
        'image': row[8],
        'bubble_color': row[9],
        'text_color': row[10],
        'catchphrase': row[11],
        'hobby': row[12]
    }

    return villager_dict

async def update_villager_db():
    db.execute('DELETE FROM villagers')
    connection.commit()

    response = requests.get('https://acnhapi.com/v1/villagers/')

    for villager in response.json():
        villager_data = response.json().get(villager)

        db.execute('INSERT INTO villagers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (villager_data.get('id'), villager_data.get('file-name'), villager_data['name'].get('name-USen'),
                    villager_data.get('personality'), villager_data.get('birthday-string'), villager_data.get('species'),
                    villager_data.get('gender'), villager_data.get('icon_uri'), villager_data.get('image_uri'),
                    villager_data.get('bubble-color'), villager_data.get('text-color'),
                    villager_data['catch-translations'].get('catch-USen'), villager_data.get('hobby')))
        connection.commit()

def setup(client):
    client.add_cog(AnimalCrossing(client))

# FUNCTIONS FOUND ONLINE #

def create_rounded_rectangle_mask(size, radius, color=(255, 255, 255, 0)):
    factor = 5  # Factor to increase the image size that I can later antialiaze the corners
    radius = radius * factor
    image = Image.new('RGBA', (size[0] * factor, size[1] * factor), (0, 0, 0, 0))

    # create corner
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    # added the fill = .. you only drew a line, no fill
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=color)

    # max_x, max_y
    mx, my = (size[0] * factor, size[1] * factor)

    # paste corner rotated as needed
    # use corners alpha channel as mask
    image.paste(corner, (0, 0), corner)
    image.paste(corner.rotate(90), (0, my - radius), corner.rotate(90))
    image.paste(corner.rotate(180), (mx - radius, my - radius), corner.rotate(180))
    image.paste(corner.rotate(270), (mx - radius, 0), corner.rotate(270))

    # draw both inner rects
    draw = ImageDraw.Draw(image)
    draw.rectangle([(radius, 0), (mx - radius, my)], fill=color)
    draw.rectangle([(0, radius), (mx, my - radius)], fill=color)
    image = image.resize(size, Image.ANTIALIAS)  # Smooth the corners

    return image

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

def get_sign(month, day):
    month = month.lower()
    day = int(day[:-2])
    astro_sign = ''

    if month == 'december':
        astro_sign = 'sagittarius' if (day < 22) else 'capricorn'
    elif month == 'january':
        astro_sign = 'capricorn' if (day < 20) else 'aquarius'
    elif month == 'february':
        astro_sign = 'aquarius' if (day < 19) else 'pisces'
    elif month == 'march':
        astro_sign = 'pisces' if (day < 21) else 'aries'
    elif month == 'april':
        astro_sign = 'aries' if (day < 20) else 'taurus'
    elif month == 'may':
        astro_sign = 'taurus' if (day < 21) else 'gemini'
    elif month == 'june':
        astro_sign = 'gemini' if (day < 21) else 'cancer'
    elif month == 'july':
        astro_sign = 'cancer' if (day < 23) else 'leo'
    elif month == 'august':
        astro_sign = 'leo' if (day < 23) else 'virgo'
    elif month == 'september':
        astro_sign = 'virgo' if (day < 23) else 'libra'
    elif month == 'october':
        astro_sign = 'libra' if (day < 23) else 'scorpio'
    elif month == 'november':
        astro_sign = 'scorpio' if (day < 22) else 'sagittarius'

    return astro_sign
