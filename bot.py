# bot.py
import os
import discord
import BingImageCreator as bic
from discord.utils import MISSING
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import sqlite3

load_dotenv()

#Discord Setup
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    try: 
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    print(f'{client.user} has connected to Discord!')

#SQlite Database Setup
conn = sqlite3.connect("api_keys.db")
cursor = conn.cursor()

# Table Def, should only need to be run once (future revision, make this only run if api_keys.db does not exist)
# cursor.execute("""CREATE TABLE keys(
#    user INTEGER PRIMARY KEY,
#    _U TEXT, 
#    SRCHHPGUSR TEXT
#    )""")

# cursor.execute("""DELETE FROM keys
#                WHERE user = 367346612441448458
#                """)
# print("delted beeny")

# Modal Class
class KeyInputs(discord.ui.Modal, title="Input keys"):
    uKey = discord.ui.TextInput( label="_U", min_length=20, style=discord.TextStyle.long)
    srchKey = discord.ui.TextInput(label="SRCHHPGUSR", min_length=20, style=discord.TextStyle.long)


    async def on_submit(self, interaction: discord.Interaction):
        user_id = int(interaction.user.id)

        try:
            cursor.execute("""INSERT INTO keys (user, _U, SRCHHPGUSR) VALUES (?, ?, ?)""", (user_id, str(self.uKey), str(self.srchKey)))
            conn.commit()
            print(f"Committed keys for user: {interaction.user.name}")
            await interaction.response.send_message("Your keys have been submitted to the db, if you submitted them correctly, you should now be able to use `/make`!")
        except Exception as e:
            print(e)
            await interaction.response.send_message("Something went horribly wrong")


###############################################################################
#############################   Commands   ####################################
###############################################################################

#Make command to actually send a request to the bing servers. Requires a user to have already submitted their API keys
@client.tree.command(name="make", description="Uses DALLE-3 and Bing to make an image given a prompt")
async def make(interaction: discord.Interaction, prompt: str):
        cursor.execute("""SELECT * FROM keys WHERE user=%s""" % (interaction.user.id))
        results = cursor.fetchall()

        if results:
            try:
                bic_object = bic.ImageGen(auth_cookie=results[0][1], auth_cookie_SRCHHPGUSR=results[0][2])

                await interaction.response.send_message("Making `{}`...".format(prompt))
                list = bic_object.get_images(prompt)
                print("\n" + prompt)
                message = ""
                for image in list:
                    message = message + " " + image
                await interaction.followup.send(message)

            except Exception as e:
                print(e)
                await interaction.followup.send(e)
        else:
            await interaction.response.send_message("""In order to maximize everyone's use of Bing Image Creation and decrease the load on my own account, you'll need to supply 
            two keys to the bot so we can authenticate your Bing account and use your (free) image credits. In order to find the keys neccesary, 
            you'll need to follow the instructions at this link: <https://github.com/acheong08/BingImageCreator#getting-authentication> (until we come
            up with a better method for authentication). When you have both the `_U` and the `SRCHHPGUSR` keys, type `/setup` to submit them to our database, and then re-run this command
            (assuming you've done this correctly, you'll only ever need to do it once). 
                                                    
            If that doesn't work, you may have to visit <https://www.bing.com/create> first and create an image before you can do it on Discord.""", ephemeral=True)

# Stop command to cleanly close the connection to the SQlite DB and Discord servers            
@client.tree.command(name="stop")
async def stop(interaction: discord.Interaction):

    if interaction.user.id == 145717043289784320: 
        cursor.close()
        conn.close()
        await interaction.response.send_message("Shutting down...")
        await client.close()
    else: 
        interaction.response.send_message("only zach runs this command 😡")


# Setup command for users to submit their API keys
@client.tree.command(name="setup", description="Command to set up your API keys for the bing image creator.")
async def setup(interaction: discord.Interaction):
    await interaction.response.send_modal(KeyInputs())

@client.tree.command(name="help", description="Help command for Jinseo bot")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("""
`/help`  --- Displays the commands that are currently supported by Jinseo bot
`/make`  --- Creates an image from a text based prompt (using Bing Images and DALLE-3)
`/setup` --- Allows a user to enter their API keys for Bing so they can utilize the `/make` command (<https://github.com/acheong08/BingImageCreator#getting-authentication>)                                    
                                            """, ephemeral=True)
    
client.run(TOKEN)
