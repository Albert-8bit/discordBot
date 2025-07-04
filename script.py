import discord
from discord.ext import commands
import random
import json
import os
import asyncio


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "casino_data.json"
EMOJIS = ["🍒", "🍀", "💎", "7️⃣"]


pending_duels = {}  # {opponent_id: (challenger_id, amount)}

# Start a duel
@bot.command()
async def duel(ctx, opponent: discord.Member, amount: int):
    if opponent.bot or opponent.id == ctx.author.id or amount <= 0:
        await ctx.send("Invalid duel command.")
        return

    author_bal = get_balance(ctx.author.id)
    opponent_bal = get_balance(opponent.id)

    if author_bal < amount:
        await ctx.send("🚫 You don't have enough SHITCOINI.")
        return
    if opponent_bal < amount:
        await ctx.send(f"🚫 {opponent.mention} doesn't have enough SHITCOINI.")
        return

    pending_duels[opponent.id] = (ctx.author.id, amount)
    await ctx.send(f"⚔️ {ctx.author.mention} challenged {opponent.mention} to a duel for {amount} SHITCOINI! {opponent.mention}, type `!accept` to fight.")

    await asyncio.sleep(30)
    if opponent.id in pending_duels:
        del pending_duels[opponent.id]
        await ctx.send("⌛ Duel request expired.")

@bot.command()
async def accept(ctx):
    if ctx.author.id not in pending_duels:
        await ctx.send("❌ No duel found.")
        return

    challenger_id, amount = pending_duels.pop(ctx.author.id)
    challenger = await bot.fetch_user(challenger_id)

    if get_balance(challenger_id) < amount or get_balance(ctx.author.id) < amount:
        await ctx.send("💸 Someone doesn't have enough SHITCOINI anymore.")
        return

    await ctx.send(f"🪨📄✂️ Rock Paper Scissors begins between {challenger.mention} and {ctx.author.mention}! Check your DMs and reply with `1`, `2`, or `3`.")

    # Mapping: 1-Rock, 2-Paper, 3-Scissors
    choices = {1: 'rock', 2: 'paper', 3: 'scissors'}
    emoji_map = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}

    def check_number(msg, player):
        return msg.author.id == player.id and msg.content.isdigit() and int(msg.content) in [1, 2, 3]

    try:
        await challenger.send("🎮 Reply with 1 2 or 3:\n1 - Rock 🪨\n2 - Paper 📄\n3 - Scissors ✂️")
        await ctx.author.send("🎮 Reply with 1 2 or 3:\n1 - Rock 🪨\n2 - Paper 📄\n3 - Scissors ✂️")

        c_msg = await bot.wait_for('message', timeout=30.0, check=lambda m: check_number(m, challenger))
        o_msg = await bot.wait_for('message', timeout=30.0, check=lambda m: check_number(m, ctx.author))

        c_choice = choices[int(c_msg.content)]
        o_choice = choices[int(o_msg.content)]

    except asyncio.TimeoutError:
        await ctx.send("⏰ Duel canceled due to no response.")
        return
    except Exception as e:
        await ctx.send("❌ Duel failed. Error occurred.")
        return

    # Game logic
    outcomes = {
        'rock':     {'rock': 'tie', 'paper': 'lose', 'scissors': 'win'},
        'paper':    {'rock': 'win', 'paper': 'tie', 'scissors': 'lose'},
        'scissors': {'rock': 'lose', 'paper': 'win', 'scissors': 'tie'},
    }

    result = outcomes[c_choice][o_choice]

    if result == "tie":
        await ctx.send(f"🤝 It's a tie! Both chose {emoji_map[c_choice]}")
        return
    elif result == "win":
        winner, loser = challenger, ctx.author
        win_choice, lose_choice = c_choice, o_choice
    else:
        winner, loser = ctx.author, challenger
        win_choice, lose_choice = o_choice, c_choice

    add_balance(winner.id, amount)
    add_balance(loser.id, -amount)

    await ctx.send(
        f"🎯 {winner.mention} **wins** the duel! "
        f"{emoji_map[win_choice]} beats {emoji_map[lose_choice]} "
        f"and takes {amount} SHITCOINI from {loser.mention} 💸"
    )




@bot.command()
async def hug(ctx, user1: discord.Member, user2: discord.Member):
    art = f"""
⠀ {user1.mention}
         ⣴⣾⣿⣿⣶⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ 
⠀⠀⢸⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠈⢿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠈⣉⣩⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢀⣼⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣾⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀{user2.mention}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ 
⢠⣾⣿⣿⠉⣿⣿⣿⣿⣿⡄⠀⢀⣠⣤⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠙⣿⣿⣧⣿⣿⣿⣿⣿⡇⢠⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣷⠸⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠘⠿⢿⣿⣿⣿⣿⡄⠙⠻⠿⠿⠛⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⡟⣩⣝⢿⠀⠀⣠⣶⣶⣦⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣷⡝⣿⣦⣠⣾⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣿⣿⣮⢻⣿⠟⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⡇⠀⠀⠻⠿⠻⣿⣿⣿⣿⣦⡀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⠇⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⡆⠀⠀
⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⠇⠀⠀
⠀⠀⠀⠀⠀⠀⢸⣿⣿⡿⠀⠀⠀⢀⣴⣿⣿⣿⣿⣟⣋⣁⣀⣀⠀
⠀⠀⠀⠀⠀⠀⠹⣿⣿⠇⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇
"""
    await ctx.send(art)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Error: casino_data.json is corrupted.")
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_balance(user_id):
    return load_data().get(str(user_id), 0)

def set_balance(user_id, amount):
    data = load_data()
    data[str(user_id)] = amount
    save_data(data)

def add_balance(user_id, amount):
    set_balance(user_id, get_balance(user_id) + amount)

@bot.event
async def on_ready():
    print(f"🎰 SHITCOIN Casino is online as {bot.user}")

@bot.command()
async def balance(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, balansi: {bal} SHITCOINI.")

@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.user)  # once per hour
async def daily(ctx):
    bal = get_balance(ctx.author.id)
    bonus = 100 + bal // 10  # 100 + 10% of balance
    add_balance(ctx.author.id, bonus)
    await ctx.send(f"{ctx.author.mention}, miige {bonus} SHITCOINI saatobrivi bonusi(100 + balanci/10).")

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining = int(error.retry_after)
        minutes = str(remaining // 60).zfill(2)
        seconds = str(remaining % 60).zfill(2)
        await ctx.send(f"{ctx.author.mention}, macadee  {minutes}:{seconds} vax! ")


@bot.command()
async def bet(ctx, amount: int):
    if amount <= 0:
        await ctx.send(" Sike zango you thought?")
        return

    bal = get_balance(ctx.author.id)
    if amount > bal:
        await ctx.send(" Gakotrdi zango?")
        return

    spin_msg = await ctx.send("🎰 ▫️▫️▫️")
    for _ in range(6):  # reduced steps
        spin_frame = ''.join(random.choices(EMOJIS, k=3))
        await spin_msg.edit(content=spin_frame)
        await asyncio.sleep(0.07)  # faster animation

    result = [random.choice(EMOJIS) for _ in range(3)]
    result_str = ''.join(result)
    await spin_msg.edit(content=result_str)

    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            winnings = amount * 10
            add_balance(ctx.author.id, winnings)
            await ctx.send(f"{ctx.author.mention} JACKPOT!  +{winnings} SHITCOINI! 🎉")
        else:
            winnings = amount * 2
            add_balance(ctx.author.id, winnings)
            await ctx.send(f"{ctx.author.mention} GG EZ +{winnings} SHITCOINI 🎊")
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        winnings = int(amount * 1.5)
        add_balance(ctx.author.id, winnings)
        await ctx.send(f"{ctx.author.mention} Maladec +{winnings} SHITCOINI 👏")
    else:
        add_balance(ctx.author.id, -amount)
        await ctx.send(f"{ctx.author.mention} Gaasxi {amount} SHITCOINI lol 💀")


@bet.error
async def bet_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("sheiyvane ricxvi mag: !bet 50")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("sheiyvane ricxvi mag: !bet 50")

@bot.command()
async def leaderboard(ctx):
    data = load_data()
    if not data:
        await ctx.send("maca")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "**Top 10 SHITCOIN Holders:**\n"
    for i, (uid, bal) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(uid))
            msg += f"{i}. {user.name} — {bal} 💸\n"
        except:
            msg += f"{i}. [Unknown User] — {bal} 💸\n"
    await ctx.send(msg)

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(" Sike you though zango")
        return
    if amount > get_balance(ctx.author.id):
        await ctx.send(" Gakotrdi Zango?")
        return
    add_balance(ctx.author.id, -amount)
    add_balance(member.id, amount)
    await ctx.send(f"{ctx.author.mention} gadauricxa {amount} SHITCOINI → {member.mention}.(kargi qna da qvaze dado)")


bot.run(os.environ["DISCORD_TOKEN"])
