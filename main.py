import discord
import os

bot = discord.Bot()


@bot.event
async def on_connect():
    bot.load_extension('flashcards.main_flashcards')  # Main flashcards extension
    print("Bot connected!")
    await bot.sync_commands()
    print("Bot commands synced!")


@bot.listen()
async def on_ready():
    print("Bot is ready!")


@bot.slash_command(name="ping")
async def ping(ctx):
    embed = discord.Embed(title='Pong!', description=f'{round(bot.latency * 1000)} ms', color=discord.Color.red())
    await ctx.respond(embed=embed)


bot.run(os.getenv('TOKEN'))
