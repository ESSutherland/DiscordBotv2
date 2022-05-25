import discord

async def create_error_embed(error):
    embed = discord.Embed(
        title='Error!',
        color=discord.Color.red(),
        description=str(error)
    )
    return embed

async def create_success_embed(message, color):
    embed = discord.Embed(
        title='Success!',
        color=color,
        description=str(message)
    )
    return embed

async def create_color_success_embed(color_hex, color, user):
    color_hex = color_hex.upper()

    embed = discord.Embed(
        color=color
    )

    embed.add_field(
        name='Success!',
        value=f'Color set to `{color_hex}` for {user.mention}',
        inline=True
    )

    embed.set_thumbnail(url='attachment://last_color.png')
    return embed

async def create_level_embed(user, level, color):

    if int(level) == 1000:
        embed = discord.Embed(
            title='Level Up!',
            color=color,
            description=f'Congratulations, {user.mention} for reaching level {level}! What is wrong with you???'
        )
    elif int(level) == 69:
        embed = discord.Embed(
            title='Level Up!',
            color=color,
            description=f'Congratulations, {user.mention} for reaching level {level}! Nice.'
        )
    else:
        embed = discord.Embed(
            title='Level Up!',
            color=color,
            description=f'Congratulations, {user.mention} for reaching level {level}!'
        )
    return embed

async def add_blank_field(embed, inline):
    embed.add_field(
        name='\u200b',
        value='\u200b',
        inline=inline
    )