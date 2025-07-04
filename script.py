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
OWNER_ID = 1108816483976491089  # Replace with your Discord ID

pending_duels = {}  # You can keep or remove duels if you want, not used for stats

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
        data[uid] = {"balance": 0, "wins": 0, "losses": 0}
        save_data(data)
    return data[uid]

def set_user_data(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

def get_balance(user_id):
    return get_user_data(user_id).get("balance", 0)

def set_balance(user_id, amount):
    user_data = get_user_data(user_id)
    user_data["balance"] = amount
    set_user_data(user_id, user_data)

def add_balance(user_id, amount):
    user_data = get_user_data(user_id)
    user_data["balance"] = user_data.get("balance", 0) + amount
    set_user_data(user_id, user_data)

def add_game_result(user_id, result):
    user_data = get_user_data(user_id)
    if result == "win":
        user_data["wins"] = user_data.get("wins", 0) + 1
    elif result == "lose":
        user_data["losses"] = user_data.get("losses", 0) + 1
    set_user_data(user_id, user_data)

@bot.event
async def on_ready():
    print(f"🎰 SHITCOIN Casino is online as {bot.user}")

@bot.command()
async def factoryreset(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ You're not authorized to run this command.")
        return
    with open(DATA_FILE, "w") as f:
        json.dump({}, f, indent=4)
    await ctx.send("🔁 All casino data has been factory reset.")

@bot.command()
async def profile(ctx):
    user_data = get_user_data(ctx.author.id)
    bal = user_data.get("balance", 0)
    wins = user_data.get("wins", 0)
    losses = user_data.get("losses", 0)
    total = wins + losses
    winrate = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"
    await ctx.send(
        f"👤 **{ctx.author.name}'s Profile**\n"
        f"💰 Balance: {bal} SHITCOINI\n"
        f"✅ Wins: {wins}\n"
        f"❌ Losses: {losses}\n"
        f"🏆 Winrate: {winrate}"
    )

@bot.command()
async def stats(ctx):
    data = load_data()
    stats = []
    for uid, info in data.items():
        wins = info.get("wins", 0)
        losses = info.get("losses", 0)
        total = wins + losses
        if total >= 5:
            winrate = wins / total
            stats.append((uid, winrate, wins, losses))

    if not stats:
        await ctx.send("📉 Not enough data to rank players.")
        return

    sorted_stats = sorted(stats, key=lambda x: x[1], reverse=True)[:10]
    msg = "**🏅 Top 10 Winrates (min 5 games)**\n"
    for i, (uid, wr, w, l) in enumerate(sorted_stats, 1):
        try:
            user = await bot.fetch_user(int(uid))
            msg += f"{i}. {user.name} – {w}W/{l}L – {wr*100:.1f}%\n"
        except:
            msg += f"{i}. [Unknown User] – {w}W/{l}L – {wr*100:.1f}%\n"
    await ctx.send(msg)

@bot.command()
async def balance(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, balansi: {bal} SHITCOINI.")

@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def daily(ctx):
    bal = get_balance(ctx.author.id)
    bonus = 100 + bal // 10
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
        await ctx.send("Sike zango you thought?")
        return

    bal = get_balance(ctx.author.id)
    if amount > bal:
        await ctx.send("Gakotrdi zango?")
        return

    spin_msg = await ctx.send("🎰 ▫️▫️▫️")
    for _ in range(6):
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
            add_game_result(ctx.author.id, "win")
            await ctx.send(f"{ctx.author.mention} JACKPOT!  +{winnings} SHITCOINI! 🎉")
        else:
            winnings = amount * 2
            add_balance(ctx.author.id, winnings)
            add_game_result(ctx.author.id, "win")
            await ctx.send(f"{ctx.author.mention} GG EZ +{winnings} SHITCOINI 🎊")
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        winnings = int(amount * 1.5)
        add_balance(ctx.author.id, winnings)
        add_game_result(ctx.author.id, "win")
        await ctx.send(f"{ctx.author.mention} Maladec +{winnings} SHITCOINI 👏")
    else:
        add_balance(ctx.author.id, -amount)
        add_game_result(ctx.author.id, "lose")
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

    sorted_users = sorted(data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
    msg = "**Top 10 SHITCOIN Holders:**\n"
    for i, (uid, info) in enumerate(sorted_users, 1):
        bal = info.get("balance", 0)
        try:
            user = await bot.fetch_user(int(uid))
            msg += f"{i}. {user.name} — {bal} 💸\n"
        except:
            msg += f"{i}. [Unknown User] — {bal} 💸\n"
    await ctx.send(msg)

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("Sike you though zango")
        return
    if amount > get_balance(ctx.author.id):
        await ctx.send("Gakotrdi Zango?")
        return
    add_balance(ctx.author.id, -amount)
    add_balance(member.id, amount)
    await ctx.send(f"{ctx.author.mention} gadauricxa {amount} SHITCOINI → {member.mention}.(kargi qna da qvaze dado)")

# You can remove duel commands if you want since you said "no duels", but leaving them here if you want.

bot.run(os.environ["DISCORD_TOKEN"])
