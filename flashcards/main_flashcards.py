# --- Base Imports ---
import discord
from discord.ext import commands
from discord import Option

# --- Other Imports ---
from flashcards.flashcard_ui import CreateDeckUI  # View for creating the deck

# --- Setup Database ---
import sqlite3

con = sqlite3.connect("flashcards.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS cards (userID INTEGER, cardSET VARCHAR, cardName VARCHAR, cardDesc VARCHAR, cardAnswer VARCHAR)""")
cur.execute(
    """CREATE TABLE IF NOT EXISTS cardSETS (userID INTEGER, setName VARCHAR, setDescription VARCHAR)""")


# --- Slash Commands ---
@commands.slash_command()
async def create(ctx, name: str, description: Option(str, required=False)):
    embed = discord.Embed(title=f"Name of your deck: {name}", description=f"Description: {description}",
                          color=discord.Color.random())
    res = cur.execute("""SELECT * FROM cardSETS WHERE userID IS ? AND setName IS ?""",
                      (ctx.user.id, name))  # Search for user in the database
    fetch = res.fetchone()
    if fetch:
        return await ctx.respond("You already have a set that's named this!", ephemeral=True)
    else:
        cur.execute("""INSERT INTO cardSETS VALUES(?, ?, ?)""", (ctx.user.id, name, description))
    con.commit()
    await ctx.respond(embed=embed, view=CreateDeckUI(cur, con, name))


def getSetAutocomplete(ctx: discord.AutocompleteContext):
    res = cur.execute("""SELECT * FROM cardSETS WHERE userID LIKE ? AND setName LIKE ? """,
                      (str(ctx.interaction.user.id) + "%", ctx.value + "%"))  # Search for user in the database
    returnList = [item[1] for item in res.fetchall()]  # return string values of set names
    return list(returnList)


@commands.slash_command()
async def select_set(ctx, name: Option(autocomplete=getSetAutocomplete)):
    await ctx.respond("hi")


# noinspection PyTypeChecker
def setup(bot: discord.bot.Bot):
    bot.add_application_command(create)
    bot.add_application_command(select_set)
