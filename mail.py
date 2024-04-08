# DO NOT REMOVE
####################################################################
#                                                                  #
#       Credit: therealOri  |  https://github.com/therealOri       #
#                                                                  #
####################################################################

import asyncio
import discord
from discord import app_commands
from discord.ui import View
import os
from libs import rnd
import datetime
import json
import string
import sqlite3
import mailtrap as mt




# Helper functions
def clear():
    os.system("cls||clear")


def load_config(file_name):
    with open(file_name, "r") as f:
        config = json.load(f)
    return config

def save_config(config, file_name):
    with open(file_name, "w") as f:
        json.dump(config, f, indent=4)


def generate_code():
    characters = string.ascii_letters + string.digits
    part1 = ''.join(rnd.choice(characters) for _ in range(3))
    part2 = ''.join(rnd.choice(characters) for _ in range(3))
    part3 = ''.join(rnd.choice(characters) for _ in range(3))
    code = f"{part1}-{part2}-{part3}"
    return code



# I am using "mailtrap" because it was the simplest way for me to be able to send emails via python to other people using api instead of smtp and ssl.
# You can by ALL means update this to send emails however you like and I'd encourage it tbh. But for the purposes of this code, I am using mailtrap.
# I am using my own domain/website that I am hosting myself for this to work (using clouflare dashboard), but if you are able to get smtp.gmail.com to work and send emails via google, then go for that. (or however else you'd send people emails)
# Just plug your code into this one function and make sure it takes the message and receiver_email arguments and I think you'll be good to go without breaking anything.
def send_email(message, receiver_email):
    global config
    api_key = config['MAIL']['api_key']
    sender = config['MAIL']['sender_email']
    mail = mt.Mail(
        sender=mt.Address(email=sender, name="MailerBot"),
        to=[mt.Address(email=receiver_email)],
        subject="MailerBot Auth Code",
        text=message,
        category="Authorization Code",
    )
    client = mt.MailtrapClient(token=api_key)
    client.send(mail)







# Definitions
__authors__ = '@therealOri'
author_logo = None # No need to mess with this.

config = load_config('config_mail.json')
TOKEN = config['BOT']["TOKEN"]
bot_logo = config['BOT']['bot_logo']
guild_id = config['BOT']["server_id"]
GUILD = discord.Object(id=guild_id)
auth_role_id = config['AUTH']['auth_role']

db_name = "user_auths.db"



#embed colors
hex_red=0xFF0000
hex_green=0x0AC700
hex_yellow=0xFFF000 # I also like -> 0xf4c50b





################### Client Setup ###################
class MailerBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild. | so you don't need to wait 2hrs+ for discord to register commands globally.
        #self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)



intents = discord.Intents.default()
mailer = MailerBot(intents=intents) # "mailer" can be changed to anything, but you'll need to update everywhere else it has been used below.
################### Client Setup ###################







################### Bot Views ###################
# Modals
class email_auth_verify(discord.ui.Modal, title='email_auth_verify'):
    code = discord.ui.TextInput(
        label='A code has been sent to your email.',
        placeholder='Please paste code here...',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT code FROM attempts WHERE user_id = ?", (interaction.user.id,))
        code_check = cur.fetchone()[0]
        if self.code.value == code_check:
            role = interaction.guild.get_role(auth_role_id)
            await interaction.response.send_message("Verified!", ephemeral=True, delete_after=5)
            await interaction.user.add_roles(role, reason="Passed mailer email verification & authorization.")
            dm_embed = discord.Embed(title='Verified!', description='Congrats! You have been verified and given access to the server. Feel free to check out the place!', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
            dm_embed.set_thumbnail(url=bot_logo)
            dm_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.user.send(embed=dm_embed)
            cur.execute("DELETE FROM attempts WHERE user_id=?", (interaction.user.id,))
            con.commit()
            con.close()
        else:
            await interaction.response.send_message("Oof, you have not been verified, you will need to try again...", ephemeral=True, delete_after=10)
            cur.execute("DELETE FROM attempts WHERE user_id=?", (interaction.user.id,))
            con.commit()
            con.close()



class email_auth(discord.ui.Modal, title='email_auth'):
    email = discord.ui.TextInput(
        label='Please provide your email. (case sensitive)',
        placeholder='Email here...',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        global config
        emails=config['USERS']['whitelist']
        if not self.email.value in emails:
            error_embed = discord.Embed(title='Error  |  Access Denied.', description="Sorry, you are not whitelisted and are not authorized to have access to the server beyond this point.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
            error_embed.set_thumbnail(url=bot_logo)
            error_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.response.send_message(embed=error_embed, ephemeral=True, delete_after=10)
            return
        else:
            user_id = interaction.user.id
            code = generate_code()
            con = sqlite3.connect(db_name)
            cur = con.cursor()
            cur.execute("INSERT INTO attempts VALUES(?, ?, ?)", (user_id, code, 0))
            con.commit()

            # idk, this is just a proof of concept. It is very SHIT xD
            # By all means, feel free to change this email message to whatever. (As long as it tells the user the auth code)
            message = f'Mailer bot auth code --> "{code}"\n\nPlease return and submit this code to Mailer to verify.'
            send_email(message, self.email.value)
            cur.execute("UPDATE attempts SET email_sent=? WHERE user_id=?", (1, user_id))
            con.commit()
            con.close()
            mail_embed = discord.Embed(title='Email authenticated!', description="An email containing an auth code has been sent to your inbox, please click the red auth button next to authenticate.\n\n(If you do not recieve an email, please contact an admin for help.)", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
            mail_embed.set_thumbnail(url=bot_logo)
            mail_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.response.send_message(embed=mail_embed, ephemeral=True, delete_after=30)






# BUTTONS
class Verification(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    # This is for how many buttons you want, what they say, etc. and what happens when the button is pressed.
    # Each "function" will be a button applied to the message/embed/view.
    # self.stop() will make it so the button will not work after being pressed once.
    @discord.ui.button(label='Email', style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT email_sent FROM attempts WHERE user_id = ?", (interaction.user.id,))
        try: # This should error if first time cliking the button because the DB would be empty for the interaction.user.
            email_flag = cur.fetchone()[0]
        except:
            email_flag = 3
        if email_flag == 0 or email_flag == 1:
            error_embed = discord.Embed(title='Error!', description="Sorry, but you have already submitted an email, please verify the code sent to your email first! or contact and Admin if you can't.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
            error_embed.set_thumbnail(url=bot_logo)
            error_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.response.send_message(embed=error_embed, ephemeral=True, delete_after=10)
            return
        else:
            ea = email_auth()
            await interaction.response.send_modal(ea)



    @discord.ui.button(label='Auth code', style=discord.ButtonStyle.red)
    async def auth(self, interaction: discord.Interaction, button: discord.ui.Button):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT email_sent FROM attempts WHERE user_id = ?", (interaction.user.id,))
        try: # this should always error as the database is empty, and would only be populated when the user presses the Email button first.
            email_flag = cur.fetchone()
        except Exception as e:
            email_flag = None

        if not email_flag:
            error_embed = discord.Embed(title='Error  |  Access Denied.', description="Sorry, you need to click the Email button first.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
            error_embed.set_thumbnail(url=bot_logo)
            error_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.response.send_message(embed=error_embed, ephemeral=True, delete_after=10)
            return
        else:
            eav = email_auth_verify()
            await interaction.response.send_modal(eav)
################### Bot Views ###################















################### Regular Functions ###################
async def status():
    while True:
        status_messages = ['my internals', '/help for help!', 'your navigation history', 'Global Global Global', 'base all your 64', 'your security camera footage', 'myself walking on the moon', 'your browser search history']
        smsg = rnd.choice(status_messages)
        activity = discord.Streaming(type=1, url='https://twitch.tv/Monstercat', name=smsg)
        await mailer.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(60) #Seconds



def random_hex_color():
    hex_digits = '0123456789abcdef'
    hex_digits = rnd.shuffle(hex_digits)
    color_code = ''
    nums = rnd.randint(0, len(hex_digits)-1, 6)
    for _ in nums:
        color_code += hex_digits[_]
    value =  int(f'0x{color_code}', 16)
    return value
################### Regular Functions ###################

















################### Bot Start/Commands/Events ###################
@mailer.event
async def on_ready():
    global author_logo
    me = await mailer.fetch_user(254148960510279683) #das me
    author_logo = me.avatar
    mailer.loop.create_task(status())
    clear()
    print(f'Logged in as {mailer.user} (ID: {mailer.user.id})')
    print('------')






@mailer.tree.command(description='Shows you what commands you can use.')
async def help(interaction: discord.Interaction):
    rnd_hex = random_hex_color()
    embed = discord.Embed(title='Commands  |  Help\n-=-=-=-=-=-=-=-=-=-=-=-=-=-', colour=rnd_hex, timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.set_thumbnail(url=bot_logo)
    embed.add_field(name='\u200B\n(Admin) - /setup set_auth_channel <channel_id>', value="Sets the channel the bot will use for its authentication embed message.", inline=True)
    embed.add_field(name='\u200B\n(Admin) - /setup update_auth_channel <channel_id>', value="Updates the channel the bot will use instead.", inline=True)
    embed.add_field(name='\u200B\n(Admin) - /setup disable_auth_channel', value="Disables the authentication feature and removes its embed/message from the set authentication channel.", inline=True)
    embed.add_field(name='\u200B\n(Admin) - /authenticate <user_id> <email>', value="Sends an auth code to the provided email. (the user will have to tell you the code)", inline=False)
    embed.add_field(name='\u200B\n(Admin) - /verify <user_id>', value="After the user has provided/presented the correct code, this command will give the user the auth role & access to the server.", inline=False)
    embed.add_field(name='\u200B\n(Admin) - /whitelist add <email>', value="Adds the email to the whitelist.", inline=True)
    embed.add_field(name='\u200B\n(Admin) - /whitelist remove <email>', value="Removes the email from the whitelist.", inline=True)
    embed.set_footer(text=__authors__, icon_url=author_logo)
    await interaction.response.send_message(embed=embed, ephemeral=True)





@mailer.tree.command(description="Sends a code to a user's email.")
async def authenticate(interaction: discord.Interaction, user_id: str, email: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        global config
        email_list = config['USERS']['whitelist']
        if not email in email_list:
            error_embed = discord.Embed(title='Error  |  Access Denied.', description=f"Sorry, but `{email}` is not authorized to have access to the server beyond this point. (not in whitelist)", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
            error_embed.set_thumbnail(url=bot_logo)
            error_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.response.send_message(embed=error_embed, ephemeral=True, delete_after=10)
            return
        else:
            user = await mailer.fetch_user(int(user_id))
            code = generate_code()
            await interaction.response.send_message(f"The auth code sent to `{email}` is `{code}`. Save this and wait for the user to respond.", ephemeral=True)

            message = f'Mailer bot auth code --> "{code}"\n\nPlease return to discord and let the admin who is verifying you know the code.'
            send_email(message, email)
            dm_embed = discord.Embed(title='Email Notification', description='An email containing an auth code has been sent to your inbox, please go take a look!\n\n\n(If you did not recieve an email, please let an admin know and or use a different email.)', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
            dm_embed.set_thumbnail(url=bot_logo)
            dm_embed.set_footer(text=__authors__, icon_url=author_logo)
            await user.send(embed=dm_embed)



@mailer.tree.command(description='Gives a user the auth role & access to the server.')
async def verify(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        await interaction.response.send_message(f"User has been verified and given access to the server!", ephemeral=True)
        role = interaction.guild.get_role(auth_role_id)
        user = await interaction.guild.fetch_member(int(user_id))
        await user.add_roles(role, reason=f"User was /verified by @{interaction.user.name} - ({interaction.user.id})")
        dm_embed = discord.Embed(title='Verified!', description='Congrats! You have been verified and given access to the server. Feel free to check out the place!', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        dm_embed.set_thumbnail(url=bot_logo)
        dm_embed.set_footer(text=__authors__, icon_url=author_logo)
        await user.send(embed=dm_embed)







whitelist_group = app_commands.Group(name="whitelist", description="Commands for managing the email whitelist.")
@whitelist_group.command(name='add', description='Adds an email to the whitelist.')
async def add(interaction: discord.Interaction, email: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        global config
        whitelist = config['USERS']['whitelist']
        if email in whitelist:
            await interaction.response.send_message(f"Error --> `{email}` seems to already be in the whitelist. (nothing to add)", ephemeral=True)
        else:
            whitelist.append(email)
            save_config(config, 'config_mail.json')
            await interaction.response.send_message("Email has been added to the whitelist.", ephemeral=True)


@whitelist_group.command(name='remove', description='removes an email from the whitelist.')
async def remove(interaction: discord.Interaction, email: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        global config
        whitelist = config['USERS']['whitelist']
        if not email in whitelist:
            await interaction.response.send_message(f"Error --> `{email}` is not in the whitelist to begin with. (nothing to remove)", ephemeral=True)
        else:
            whitelist.remove(email)
            save_config(config, 'config_mail.json')
            await interaction.response.send_message("Email has been removed from the whitelist.", ephemeral=True)













auth_setup_group = app_commands.Group(name="setup", description="Authorization setup commands.")
@auth_setup_group.command(name="set_auth_channel", description="Sets the channel that will be used for authorization/verification.")
async def set_auth_channel(interaction: discord.Interaction, channel_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        channel_id = int(channel_id)
        global config
        flag = config['AUTH']['auth_flag']
        if flag == True:
            error_embed = discord.Embed(title='Error  |  You have already set up a channel to handle user authentication.', description="Please use `/setup update_auth_channel` to change auth channels...", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
            error_embed.set_thumbnail(url=bot_logo)
            error_embed.set_footer(text=__authors__, icon_url=author_logo)
            await interaction.response.send_message(embed=error_embed, ephemeral=True, delete_after=10)
            return
        else:
            rnd_hex = random_hex_color()
            channel = mailer.get_channel(channel_id)
            verify_embed = discord.Embed(title='Start verification.', description='⚠️ READ ME ⚠️\n\nClick the green button below when you are ready to submit your email. And click the red button AFTER you have gotten your authentication code.\n\n(If you did not recieve an auth code via email, please contact an admin.)', colour=rnd_hex, timestamp=datetime.datetime.now(datetime.timezone.utc))
            verify_embed.set_thumbnail(url=bot_logo)
            verify_embed.set_footer(text=__authors__, icon_url=author_logo)
            view = Verification(timeout=None)
            msg = await channel.send(embed=verify_embed, view=view)

            config["AUTH"]["auth_message_id"] = msg.id
            config["AUTH"]["auth_channel_id"] = channel_id
            config["AUTH"]["auth_flag"] = True
            save_config(config, 'config_mail.json')
            await interaction.response.send_message("Auth channel set up!", ephemeral=True, delete_after=10)




@auth_setup_group.command(name="update_auth_channel", description="Updates the channel mailer will use for verification/authentication.")
async def update_auth_channel(interaction: discord.Interaction, channel_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        channel_id = int(channel_id)
        global config
        auth_msg_id = config['AUTH']['auth_message_id']
        auth_chnl_id = config["AUTH"]["auth_channel_id"]
        channel = mailer.get_channel(auth_chnl_id)
        message = await channel.fetch_message(auth_msg_id)
        await message.delete()

        rnd_hex = random_hex_color()
        channel = mailer.get_channel(channel_id)
        verify_embed = discord.Embed(title='Start verification.\n\n-=-=-=-=-=-=-=-=-=-=-=-=-=-', description='Click the green button when you are ready to verify.', colour=rnd_hex, timestamp=datetime.datetime.now(datetime.timezone.utc))
        verify_embed.set_thumbnail(url=bot_logo)
        verify_embed.set_footer(text=__authors__, icon_url=author_logo)
        view = Verification(timeout=None)
        nmsg = await channel.send(embed=verify_embed, view=view)

        config["AUTH"]["auth_message_id"] = nmsg.id
        config["AUTH"]["auth_channel_id"] = channel_id
        save_config(config, 'config_mail.json')
        await interaction.response.send_message("Auth channel has been changed!", ephemeral=True, delete_after=10)




@auth_setup_group.command(name="disable_auth_channel", description="Disables mailers verification/authentication system.")
async def disable_auth_channel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return
    else:
        global config
        auth_msg_id = config['AUTH']['auth_message_id']
        if not auth_msg_id:
            await interaction.response.send_message("Authentication has not been set up yet.", ephemeral=True, delete_after=10)
        else:
            auth_chnl_id = config["AUTH"]["auth_channel_id"]
            channel = mailer.get_channel(auth_chnl_id)
            message = await channel.fetch_message(auth_msg_id)
            await message.delete()
            config["AUTH"]["auth_message_id"] = None
            config["AUTH"]["auth_channel_id"] = None
            config["AUTH"]["auth_flag"] = False
            save_config(config, 'config_mail.json')

            con = sqlite3.connect(db_name)
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM attempts")
            row_count = cur.fetchone()[0]

            # Delete all data in the table if it's not empty
            if row_count > 0:
                cur.execute("DELETE FROM attempts")
                con.commit()
                con.close()

            await interaction.response.send_message("Authentication has been disabled.", ephemeral=True, delete_after=10)
################### Bot Start/Commands/Events ###################









mailer.tree.add_command(auth_setup_group)
mailer.tree.add_command(whitelist_group)
mailer.run(TOKEN, reconnect=True)
