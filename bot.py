from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
import discord
import random
import aiosqlite
import time

client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)

footer="Better than discord's own bot"
gold=0xffd700
red=0xff0000
green=0x6aff00

@client.event
async def on_ready():
    print(f"logged into {client.user}")
    await tables()

async def check(guild, user):
    async with aiosqlite.connect("data.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (guild.id, user.id))
        row = await cursor.fetchone()
        return row == None

async def new_user(guild, user):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("INSERT INTO users VALUES (?, ?, 0, 0, 0, 0, 0, 0)", (guild.id, user.id))
        await db.commit()

async def tables():
    async with aiosqlite.connect("data.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users(guild_id integer, user_id integer, balls integer, hits integer, misses integer, taken integer, last_throw integer, last_pickup integer)''')
        await db.commit()

@slash.slash(guild_ids = [554362814794563586],
    name="collect",
    description="Get snowballs to throw at people!"
)
async def collect(ctx):
    if ctx.channel.id == 554362815285166121 or ctx.channel.id == 722099463040139274:
        if await check(ctx.guild, ctx.author):
            await new_user(ctx.guild, ctx.author)
        async with aiosqlite.connect("data.db") as db:
            await ctx.defer(hidden=True)
            cursor = await db.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id))
            row = await cursor.fetchone()
            if int(time.time()) - row[7] >= 30:
                if int(time.time()) - row[6] >= (60*3):

                    await db.execute("UPDATE users SET balls = balls + 1 WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id))
                    await db.execute("UPDATE users SET last_pickup = ? WHERE guild_id = ? AND user_id = ?", (int(time.time()), ctx.guild.id, ctx.author.id))
                    await db.commit()

                    embed = discord.Embed(title="", color=green)
                    embed.add_field(name="You collected another snowball", value=f"You now have {row[2]+1} snowball(s)!", inline=False)
                    embed.set_footer(text=footer)
                    await ctx.send(embed=embed, hidden=True)
                else:
                    embed = discord.Embed(title="**No can do**", color=red)
                    embed.add_field(name="You got hit and now you can't pick up snow", value="Try and wait 3 minutes for your arms to rest", inline=False)
                    embed.set_footer(text=footer)
                    await ctx.send(embed=embed, hidden=True)
            else:
                embed = discord.Embed(title="**No can do**", color=red)
                embed.add_field(name="There is no more snow", value="Try and wait 30 seconds for the snow to fall", inline=False)
                embed.set_footer(text=footer)
                await ctx.send(embed=embed, hidden=True)
    else:
        await ctx.send("Please don't do that here!", hidden=True)

@slash.slash(guild_ids = [554362814794563586],
    name="throw",
    description="Get snowballs to throw at people!",
    options=[
        create_option(
            name="target",
            description="Who do you want to hit?",
            option_type=6,
            required=True,
        )
    ]
)
async def throw(ctx, target: discord.member):
    if ctx.channel.id == 554362815285166121 or ctx.channel.id == 722099463040139274:
        if await check(ctx.guild, ctx.author):
            await new_user(ctx.guild, ctx.author)
        if await check(ctx.guild, target):
            await new_user(ctx.guild, target)

        async with aiosqlite.connect("data.db") as db:
            cursor = await db.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id))
            attacker = await cursor.fetchone()

            if attacker[2] > 0:
                if int(time.time()) - attacker[6] >= (120*3):
                    await ctx.defer()
                    x = random.randint(0, 4)

                    if x == 0:
                        await db.execute("UPDATE users SET misses = misses + 1 WHERE user_id = ? AND guild_id = ?", (ctx.author.id, ctx.guild.id))
                        await db.execute("UPDATE users SET balls = balls - 1 WHERE user_id = ? AND guild_id = ?", (ctx.author.id, ctx.guild.id))
                        await db.commit()

                        embed = discord.Embed(title="**Close one!**", color=red)
                        embed.add_field(name=f"You missed {target}!", value="You need to work on your aim", inline=False)
                        embed.set_footer(text=footer)
                        await ctx.send(embed=embed)

                    else:
                        await db.execute("UPDATE users SET balls = balls - 1 WHERE user_id = ? AND guild_id = ?", (ctx.author.id, ctx.guild.id))
                        await db.execute("UPDATE users SET hits = hits + 1 WHERE user_id = ? AND guild_id = ?", (ctx.author.id, ctx.guild.id))

                        await db.execute("UPDATE users SET taken = taken + 1 WHERE user_id = ? AND guild_id = ?", (target.id, ctx.guild.id))
                        await db.execute("UPDATE users SET last_throw = ? WHERE user_id = ? AND guild_id = ?", (time.time(), target.id, ctx.guild.id))
                        await db.commit()

                        embed = discord.Embed(title="**Nice Shot!**", color=green)
                        embed.add_field(name=f"Smack! you hit {target} right in the face!", value="Target eliminated!", inline=False)
                        embed.set_footer(text=footer)
                        await ctx.send(embed=embed)

                else:
                    embed = discord.Embed(title="**No can do**", color=red)
                    embed.add_field(name="You are on cooldown", value="You got hit and are currently a bit hurt, wait for your arm to rest", inline=False)
                    embed.set_footer(text=footer)
                    await ctx.send(embed=embed, hidden=True)
            else:
                embed = discord.Embed(title="**No can do**", color=red)
                embed.add_field(name="You are out of snowballs", value="You can't throw air lol", inline=False)
                embed.set_footer(text=footer)
                await ctx.send(embed=embed, hidden=True)
    else:
        await ctx.send("Please don't do that here!", hidden=True)

@slash.slash(guild_ids = [554362814794563586],
    name="stats",
    description="Who has the best stats",
    options=[
        create_option(
            name="user",
            description="Who's stats do you want to see? (optional)",
            option_type=6,
            required=False,
        )
    ]
)
async def stats(ctx, user: discord.Member = None):
    if ctx.channel.id == 554362815285166121 or ctx.channel.id == 722099463040139274:
        if user is None:
            user = ctx.author
        if await check(ctx.guild, user):
            await new_user(ctx.guild, user)
        async with aiosqlite.connect("data.db") as db:
            cursor = await db.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, user.id))
            row = await cursor.fetchone()


            embed = discord.Embed(title="**Stats**", color=green)
            embed.add_field(name=f"{user}", value="Check out their stats!", inline=False)
            embed.add_field(name=f"Snowballs: {row[2]}", value=f"Snowballs collected: {row[2] + row[3] + row[4]}", inline=False)
            embed.add_field(name=f"Hits: {row[3]}", value=f"Misses: {row[4]}", inline=False)
            embed.add_field(name=f"Hits taken: {row[5]}", value="Get better tbh", inline=False)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)
    else:
        await ctx.send("Please don't do that here!", hidden=True)

@slash.slash(guild_ids = [554362814794563586],
    name="leaderboard",
    description="Who are on the top?",
)
async def leaderboard(ctx):
    if ctx.channel.id == 554362815285166121 or ctx.channel.id == 722099463040139274:
        async with aiosqlite.connect("data.db") as db:
            cursor = await db.execute(
                "SELECT user_id, hits, misses, taken FROM users WHERE guild_id = ? ORDER BY hits/(taken + 0.0001) DESC LIMIT 10", (ctx.guild.id,))
            rows = await cursor.fetchall()

            embed = discord.Embed(title="**Leaderboard**", description="Only the best ones are here!", color=gold)
            top10 = False
            for i, row in enumerate(rows):
                print(row[0], row[1], row[2], row[3])
                print(i)
                if row[0] == ctx.author.id:
                    top10 = True
                if i == 0:
                    embed.add_field(name=f"<:MedalGold:882630754436272198> {await client.fetch_user(int(row[0]))}", value=f"Hits: {row[1]}\nMisses: {row[2]}\nHits taken: {row[3]}", inline=False)
                if i == 1:
                    embed.add_field(name=f"<:MedalSilver:882630754427891742> {await client.fetch_user(int(row[0]))}", value=f"Hits: {row[1]}\nMisses: {row[2]}\nHits taken: {row[3]}", inline=False)
                if i == 2:
                    embed.add_field(name=f"<:MedalBronze:882630754536919100> {await client.fetch_user(int(row[0]))}", value=f"Hits: {row[1]}\nMisses: {row[2]}\nHits taken: {row[3]}", inline=False)
                if i >= 3:
                    embed.add_field(name=f"{str(i + 1)}. {await client.fetch_user(int(row[0]))}", value=f"Hits: {row[1]}\nMisses: {row[2]}\nHits taken: {row[3]}", inline=False)

            embed.set_footer(text=footer)
            if top10:
                await ctx.send(embed=embed)
            else:
                cursor = await db.execute(
                    "SELECT RowNum, user_id, hits, misses, taken FROM (SELECT ROW_NUMBER() OVER (ORDER BY hits/(taken + 0.0001) DESC) RowNum, guild_id, user_id, hits, misses, taken FROM users WHERE guild_id = ?) AS t WHERE user_id = ?}",
                    (guild_id, user_id,))
                row = await cursor.fetchone()
                embed.add_field(name=f"{str(row[0])}. {await client.fetch_user(int(row[1]))}", value=f"Hits: {row[2]}\nMisses: {row[3]}\nHits taken: {row[4]}", inline=False)
                await ctx.send(embed=embed)
    else:
        await ctx.send("Please don't do that here!", hidden=True)

if __name__ == '__main__':
    client.run("")