import discord
from discord import ui, InputTextStyle, SelectOption, Interaction
from discord.ui import InputText, Select
import sqlite3  # For typing


class CreateDeckUI(ui.View):
    def __init__(self, cursor: sqlite3.Cursor, con, setName, user):
        super().__init__()
        self.add_item(self.AddCard(cursor, con, setName, self))
        res = cursor.execute("""SELECT * FROM cards WHERE userID IS ? AND cardSET IS ?""", (user.id, setName))
        self.timeout = 0
        self.disable_on_timeout = True
        if res.fetchone():  # means that there are cards in the set
            self.add_item(self.cardSelect(setName, cursor, user))

    class AddCard(ui.Button):
        def __init__(self, cursor, con, setName, upper):
            super().__init__(label="Add Card", emoji="➕", style=discord.ButtonStyle.blurple)
            self.cursor = cursor
            self.con = con
            self.setName = setName
            self.upper = upper

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(
                self.AddCardModal(self.cursor, self.con, self.setName, self.view, self))

        class AddCardModal(ui.Modal):
            def __init__(self, cursor: sqlite3.Cursor, con, setName, view: discord.ui.View, upper):
                self.cur = cursor
                self.con = con
                self.setName = setName
                self.view = view
                self.upper = upper
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
                res = self.cur.execute("""SELECT * FROM cards WHERE userID IS ? AND cardSET IS ? AND cardName IS ?""",
                                       (interaction.user.id, self.setName, self.children[0].value))
                fetch = res.fetchone()
                if not fetch:
                    self.cur.execute("""INSERT INTO cards VALUES(?, ?, ?, ?, ?)""",
                                     (interaction.user.id, self.setName, self.children[0].value, self.children[1].value,
                                      self.children[2].value,))
                    self.cur.connection.commit()
                    await interaction.response.send_message("Items stored", ephemeral=True)
                    if interaction.message is not None:
                        newView = self.view
                        newView.remove_item(self.view.get_item('cardSelect'))
                        newView.add_item(self.upper.upper.cardSelect(self.setName, self.cur, interaction.user))
                        await self.upper.upper.message.edit(view=newView)
                else:
                    await interaction.response.send_message(
                        "You already have a card with the same name. Please name it something else or edit the card.",
                        ephemeral=True)

    class cardSelect(Select):
        def __init__(self, setName, cur, user):
            self.setName = setName
            self.cur = cur
            self.user = user
            res = self.cur.execute("""SELECT * FROM cards WHERE userID IS ? AND cardSET IS ?""",
                                   (self.user.id, self.setName,))
            options = [SelectOption(label=option[2], description=option[3]) for option in res.fetchall()]
            super().__init__(options=options, custom_id="cardSelect")

        class editCardView(ui.View):
            def __init__(self, cursor, con, setName, cardName):
                super().__init__(self.sendModalButton(self.cardEditModal, cursor, con, setName, cardName, self))

            class cardEditModal(ui.Modal):
                def __init__(self, cursor, con, setName, view, upper, cardName):
                    cardQuestion = InputText(style=InputTextStyle.short, label="Card Question")
                    cardDescription = InputText(required=False, style=InputTextStyle.long, label="Card Description")
                    cardAnswer = InputText(required=True, style=InputTextStyle.short, label="Card Answer")

                    self.cur = cursor
                    self.con = con
                    self.setName = setName
                    self.view = view
                    self.upper = upper
                    self.cardName = cardName

                    super().__init__(cardQuestion, cardDescription, cardAnswer, title="Flashcard Data")

                async def callback(self, interaction: discord.Interaction):
                    res = self.cur.execute(
                        """SELECT * FROM cards WHERE userID IS ? AND cardSET IS ? AND cardName IS ?""",
                        (str(interaction.user.id), self.setName, self.cardName))
                    if res.fetchone():
                        alreadyExists = self.cur.execute(
                            """SELECT * FROM cards WHERE userID IS ? AND cardSET IS ? AND cardName IS ?""",
                            (str(interaction.user.id), self.setName, self.children[0].value))
                        if alreadyExists.fetchone():
                            return await interaction.response.send_message("There is already a card with this name.",
                                                                           ephemeral=True)

                        self.cur.execute(
                            """UPDATE cards SET cardName = ?, cardDesc = ?, cardAnswer = ? WHERE cardName IS ? AND cardSET IS ? """,
                            (self.children[0].value, self.children[1].value, self.children[2].value, self.cardName,
                             self.setName))
                        self.cur.connection.commit()
                        self.cardName = self.children[0].value
                        self.upper.upper.cardName = self.children[0].value
                        self.upper.cardName = self.children[0].value
                        embed = discord.Embed(
                            title=f"Card Title: {self.children[0].value}",
                            color=discord.Color.random(),
                        )
                        embed.add_field(name="Card Set:", value=self.setName, inline=False)
                        embed.add_field(name="Card Description:", value=self.children[1].value, inline=False)
                        embed.add_field(name="Card Answer:", value=self.children[2].value, inline=False)
                        await self.upper.upper.message.edit(embed=embed)
                        await interaction.response.send_message("Card edited.", ephemeral=True)
                    else:
                        await interaction.response.send_message("An unexpected error has occurred", ephemeral=True)

            class sendModalButton(discord.ui.Button):
                def __init__(self, cardModal, cursor, con, setName, cardName, upper):
                    super().__init__(label="Edit Card", emoji="✍")
                    self.cardModal = cardModal
                    self.cursor = cursor
                    self.con = con
                    self.setName = setName
                    self.cardName = cardName
                    self.upper = upper

                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.send_modal(
                        self.cardModal(self.cursor, self.con, self.setName, self.view, self, self.cardName))

        async def callback(self, interaction: Interaction):
            res = self.cur.execute("""SELECT * FROM cards WHERE userID IS ? AND cardSET IS ? AND cardName IS ?""",
                                   (self.user.id, self.setName, self.values[0]))
            fetch = res.fetchone()
            embed = discord.Embed(
                title=f"Card Title: {fetch[2]}",
                color=discord.Color.random(),

            )
            embed.add_field(name="Card Set:", value=fetch[1], inline=False)
            embed.add_field(name="Card Description:", value=fetch[3], inline=False)
            embed.add_field(name="Card Answer:", value=fetch[4], inline=False)
            await interaction.response.send_message(embed=embed,
                                                    view=self.editCardView(self.cur, self.cur.connection, self.setName,
                                                                           self.values[0]))
