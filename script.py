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

# -------------------
# Data helpers
# -------------------

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

def get_user_data(user_id):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": 0,
            "wins": 0,
            "losses": 0,
            "total_win_amount": 0,
            "total_loss_amount": 0
        }
        save_data(data)
    return data[uid]

def save_user_data(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

def get_balance(user_id):
    return get_user_data(user_id).get("balance", 0)

def set_balance(user_id, amount):
    user_data = get_user_data(user_id)
    user_data["balance"] = amount
    save_user_data(user_id, user_data)

def add_balance(user_id, amount):
    user_data = get_user_data(user_id)
    user_data["balance"] = user_data.get("balance", 0) + amount
    save_user_data(user_id, user_data)

def add_game_result(user_id, result, amount):
    user_data = get_user_data(user_id)
    if result == "win":
        user_data["wins"] = user_data.get("wins", 0) + 1
        user_data["total_win_amount"] = user_data.get("total_win_amount", 0) + amount
    elif result == "lose":
        user_data["losses"] = user_data.get("losses", 0) + 1
        user_data["total_loss_amount"] = user_data.get("total_loss_amount", 0) + amount
    save_user_data(user_id, user_data)

def get_rank(user_data):
    wins = user_data.get("wins", 0)
    losses = user_data.get("losses", 0)
    total_games = wins + losses
    if total_games == 0:
        return "Unranked"
    win_rate = wins / total_games
    if win_rate >= 0.75:
        return "💎 Diamond"
    elif win_rate >= 0.60:
        return "🥇 Gold"
    elif win_rate >= 0.45:
        return "🥈 Silver"
    elif win_rate >= 0.30:
        return "🥉 Bronze"
    else:
        return "🔰 Beginner"

# -------------------
# Bot events & commands
# -------------------

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
    for _ in range(6):  # faster animation
        spin_frame = ''.join(random.choices(EMOJIS, k=3))
        await spin_msg.edit(content=spin_frame)
        await asyncio.sleep(0.07)

    result = [random.choice(EMOJIS) for _ in range(3)]
    result_str = ''.join(result)
    await spin_msg.edit(content=result_str)

    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            winnings = amount * 10
            add_balance(ctx.author.id, winnings)
            add_game_result(ctx.author.id, "win", winnings)
            await ctx.send(f"{ctx.author.mention} JACKPOT!  +{winnings} SHITCOINI! 🎉")
        else:
            winnings = amount * 2
            add_balance(ctx.author.id, winnings)
            add_game_result(ctx.author.id, "win", winnings)
            await ctx.send(f"{ctx.author.mention} GG EZ +{winnings} SHITCOINI 🎊")
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        winnings = int(amount * 1.5)
        add_balance(ctx.author.id, winnings)
        add_game_result(ctx.author.id, "win", winnings)
        await ctx.send(f"{ctx.author.mention} Maladec +{winnings} SHITCOINI 👏")
    else:
        add_balance(ctx.author.id, -amount)
        add_game_result(ctx.author.id, "lose", amount)
        await ctx.send(f"{ctx.author.mention} Gaasxi {amount} SHITCOINI lol 💀")

@bet.error
async def bet_error(ctx, error):
    if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("sheiyvane ricxvi mag: !bet 50")

@bot.command()
async def leaderboard(ctx):
    data = load_data()
    if not data:
        await ctx.send("maca")
        return

    # Sort by balance descending
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]

    msg = "**Top 10 SHITCOIN Holders:**\n"
    for i, (uid, user_data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(uid))
            bal = user_data.get("balance", 0)
            msg += f"{i}. {user.name} — {bal} 💸\n"
        except:
            bal = user_data.get("balance", 0)
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

@bot.command()
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_data = get_user_data(member.id)
    balance = user_data.get("balance", 0)
    wins = user_data.get("wins", 0)
    losses = user_data.get("losses", 0)
    total_win = user_data.get("total_win_amount", 0)
    total_loss = user_data.get("total_loss_amount", 0)
    total_games = wins + losses
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    rank = get_rank(user_data)

    embed = discord.Embed(title=f"{member.name}'s Profile", color=discord.Color.blue())
    embed.add_field(name="Balance", value=f"{balance} SHITCOINI")
    embed.add_field(name="Wins", value=f"{wins} (Total Won: {total_win})")
    embed.add_field(name="Losses", value=f"{losses} (Total Lost: {total_loss})")
    embed.add_field(name="Win Rate", value=f"{win_rate:.2f}%")
    embed.add_field(name="Rank", value=rank)

    await ctx.send(embed=embed)

OWNER_ID = 1108816483976491089  # Replace with your Discord user ID

@bot.command()
async def factoryreset(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ You don't have permission to do that.")
        return

    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    await ctx.send("✅ Casino data has been reset to factory settings.")

bot.run(os.environ["DISCORD_TOKEN"])
