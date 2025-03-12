import discord
from discord.ext import commands
import random

intents = discord.Intents.default()
intents.members = True  # Włączamy możliwość zarządzania rolami
intents.messages = True  # Włączanie odczytu treści wiadomości (jeśli potrzebujesz)
intents.message_content = True  # Włączanie uprawnienia do treści wiadomości

bot = commands.Bot(command_prefix="!", intents=intents)

QUIZ_CHANNEL_ID = 1329108488240107520  # 📌 ID dozwolonego kanału

quiz_questions = {
    "Ile wynosi 8 * 7?": "56",
    "Ile kontynentów jest na świecie?": "7",
    "Jak nazywa się stolica Francji?": "Paryż",
    "Kto był pierwszym królem Polski?": "Bolesław Chrobry",
    "Jak nazywa się największy ocean?": "Pacyfik",
}

# Losowe pytania dla Mistrzów Quizu (opcjonalne, 3 punkty)
master_questions = {
    "Kto wynalazł teorię względności?": "Albert Einstein",
    "Ile wynosi wartość liczby pi do dwóch miejsc po przecinku?": "3.14",
    "Co to jest Higgs boson?": "Cząstka elementarna",
    "Jak nazywa się pierwszy człon rakiety Apollo 11?": "Saturn V",
}

player_scores = {}  # Punkty graczy
player_streaks = {}  # Licznik poprawnych odpowiedzi pod rząd

# 📌 ID ról z nowymi progami punktowymi
role_rewards = {
    0: 1349419832784715829,   # Nowicjusz Quizu - za użycie komendy
    5: 1349420369919873127,   # Uczeń Quizów
    15: 1349421638449631274,  # Znawca Quizów
    30: 1349420060552335444,  # Profesor Quizów
    50: 1349419925965635676,  # Ekspert Quizów
    80: 1349419995297484852,  # Mistrz Quizów
    120: 1349420288227541032  # Bóg Quizów
}

@bot.event
async def on_ready():
    print(f"Bot {bot.user} jest online!")

@bot.command()
async def quiz(ctx):
    """Rozpoczyna quiz i nagradza Nowicjusza"""
    if ctx.channel.id != QUIZ_CHANNEL_ID:
        await ctx.send("🚫 Ten bot działa tylko na wyznaczonym kanale!")
        return

    if not quiz_questions:
        await ctx.send("🎉 Wszystkie pytania zostały wykorzystane! Zresetuj quiz.")
        return

    # 📌 Automatycznie przyznajemy rolę Nowicjusza Quizu
    await check_and_give_role(ctx, ctx.author, 0)

    question, answer = random.choice(list(quiz_questions.items()))
    await ctx.send(f"🎲 **Quiz Time!** {question}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)
    if msg.content.lower() == answer.lower():
        await ctx.send("✅ **Dobrze!**")
        player_scores[msg.author] = player_scores.get(msg.author, 0) + 1

        # 📌 Liczymy serie poprawnych odpowiedzi
        player_streaks[msg.author] = player_streaks.get(msg.author, 0) + 1
        bonus = get_bonus_points(player_streaks[msg.author])
        player_scores[msg.author] += bonus
        if bonus > 0:
            await ctx.send(f"🔥 **Seria!** Otrzymujesz dodatkowe {bonus} punkty!")

        await check_and_give_role(ctx, msg.author)  # Sprawdzamy, czy gracz zasłużył na rolę
    else:
        await ctx.send(f"❌ **Źle!** Poprawna odpowiedź to: {answer}")
        player_streaks[msg.author] = 0  # Reset serii

    del quiz_questions[question]

    # Jeśli gracz jest Mistrzem, zapytamy, czy chce odpowiedzieć na pytanie dodatkowe
    if await is_master(ctx.author):
        await ctx.send("🎉 Jako Mistrz Quizu masz szansę na dodatkowe pytanie! Chcesz spróbować? (Tak/Nie)")
        msg = await bot.wait_for("message", check=check)
        if msg.content.lower() == "tak":
            master_question, master_answer = random.choice(list(master_questions.items()))
            await ctx.send(f"💡 Dodatkowe pytanie: {master_question}")
            msg = await bot.wait_for("message", check=check)
            if msg.content.lower() == master_answer.lower():
                await ctx.send("✅ **Dobrze!** Otrzymujesz 3 punkty!")
                player_scores[msg.author] += 3
                await check_and_give_role(ctx, msg.author)  # Sprawdzamy, czy gracz zasłużył na rolę
            else:
                await ctx.send(f"❌ **Źle!** Poprawna odpowiedź to: {master_answer}")

@bot.command()
async def score(ctx):
    """Pokazuje aktualny wynik gracza"""
    score = player_scores.get(ctx.author, 0)
    await ctx.send(f"🏆 {ctx.author.mention}, masz {score} punktów!")

@bot.command()
async def ranking(ctx):
    """Pokazuje ranking TOP 10 graczy"""
    if not player_scores:
        await ctx.send("😢 Nikt jeszcze nie zdobył punktów!")
        return

    sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)
    ranking_message = "**🏆 Ranking Graczy 🏆**\n"
    
    for i, (player, score) in enumerate(sorted_scores[:10], start=1):
        ranking_message += f"**{i}.** {player.name} - {score} punktów\n"

    await ctx.send(ranking_message)

@bot.command()
async def ilepunktowdorangi(ctx):
    """Pokazuje, ile punktów brakuje do kolejnej rangi"""
    score = player_scores.get(ctx.author, 0)
    next_rank = None
    for points in sorted(role_rewards.keys()):
        if score < points:
            next_rank = points - score
            break

    if next_rank is None:
        await ctx.send(f"🎉 {ctx.author.mention}, masz już najwyższą rangę!")
    else:
        await ctx.send(f"📊 {ctx.author.mention}, brakuje Ci **{next_rank} punktów** do następnej rangi!")

async def check_and_give_role(ctx, member, force_points=None):
    """
    Sprawdza punkty gracza i nadaje odpowiednią rolę.
    Jeśli force_points nie jest None, przypisuje rolę niezależnie od wyniku.
    """
    score = force_points if force_points is not None else player_scores.get(member, 0)

    for points, role_id in role_rewards.items():
        if score >= points:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            if role and role not in member.roles:
                await member.add_roles(role)
                await ctx.send(f"🎖 {member.mention} zdobył rolę **{role.name}**!")

def get_bonus_points(streak):
    """Oblicza bonusowe punkty za serie poprawnych odpowiedzi"""
    if streak >= 10:
        return 5
    elif streak >= 5:
        return 3
    elif streak >= 3:
        return 1
    return 0

async def is_master(member):
    """Sprawdza, czy gracz ma rolę Mistrza Quizu"""
    role = discord.utils.get(member.roles, id=1349419995297484852)
    return role is not None

bot.run("MTM0OTQxNzYzODI5NTUwMjk0OA.GAhrKI.eKyzwyypxswC_ihawQ65aKN1col2VkjMiGehbo")
