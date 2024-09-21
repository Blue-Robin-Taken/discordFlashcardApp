import discord
from discord import ui, InputTextStyle
from discord.ui import InputText
import sqlite3  # For typing


class CreateDeckUI(ui.View):
    def __init__(self, cursor: sqlite3.Cursor, con, setName):
        super().__init__()
        self.add_item(self.AddCard(cursor, con, setName))

    class AddCard(ui.Button):
        def __init__(self, cursor, con, setName):
            super().__init__(label="Add Card", emoji="➕", style=discord.ButtonStyle.blurple)
            self.cursor = cursor
            self.con = con
            self.setName = setName

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(self.AddCardModal(self.cursor, self.con, self.setName))

        class AddCardModal(ui.Modal):
            def __init__(self, cursor: sqlite3.Cursor, con, setName, ):
                self.cur = cursor
                self.con = con
                self.setName = setName
                cardQuestion = InputText(style=InputTextStyle.short, label="Card Question")
                cardDescription = InputText(required=False, style=InputTextStyle.long, label="Card Description")
                cardAnswer = InputText(required=True, style=InputTextStyle.short, label="Card Answer")

                super().__init__(cardQuestion, cardDescription, cardAnswer, title="Flashcard Data")

            async def callback(self, interaction: discord.Interaction):
                """
                Cards Database Structure:
                - User ID
                - Set Name
                - Card Question
                - Card Description
                - Card Answer
                (userID INTEGER, cardSET = VARCHAR, cardName VARCHAR, cardDesc VARCHAR, cardAnswer VARCHAR)
                """
                self.cur.execute("""INSERT INTO cards VALUES(?, ?, ?, ?, ?)""",
                                 (interaction.user.id, self.setName, self.children[0].value, self.children[1].value,
                                  self.children[2].value,))
                self.cur.connection.commit()
                await interaction.response.send_message("Items stored")
