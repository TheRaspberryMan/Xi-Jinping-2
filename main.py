import os
import re
import json
import pokepy
import requests
import discord
import youtube_dl
import discord.utils
from os import path
from PIL import Image
from io import BytesIO
from requests import get
from time import sleep, time
from datetime import datetime
from bs4 import BeautifulSoup
from emoji import UNICODE_EMOJI
from random import randint, choice
from random_word import RandomWords
from difflib import SequenceMatcher
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
from pyopentdb import OpenTDBClient, Category, QuestionType, Difficulty

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#RANDOM SETUP THINGS

# instance of the trivia api wrapper library class
client = OpenTDBClient()


# Has role id for each person, none means change noothing, and true means you can give this person a role then has their user id
perm_votes = {
    "THUMB UP FOR YES THUMB DOWN FOR NO (BUT DON'T BE MEAN SO NOONE LOOSES KARMA)" : None,
    "ALISTAR" : 741400413689085973,
    "JACKSON" : 740011949324238899,
    "CAMRON" : 739680352993280001,
    "MAXWELL" : 743193891389440065,
    "EMILY" : 740011949324238899, 
    "VINCENT" : 750174515585089677,
    "CRAYTON" : 743198298793574483,
    "MARTY" : None,
    "GEMMA" : 758474844747595837,
    "BUBBLIES" : None,
    'ALEXIS' : 758698126961541122,
    'CROLIN (THAT MEANS COLIN)' : 758374868545962016,
    "OH NO!!!!!!!!!!!!!!!" : None,
    "KOA" : [True, 539107421784899594],
    "LEO" : [True, 381907714663776266], 
    'ANA' : 749805088607830036,
    "NATE" : [True, 560506450829639691], 
    "**SQUIRMYWORMY8**" : None,
    'walen' : [True, 552287282124685323],
    "JACBOBY" : [True, 289159053857259521]
}

has_perms = {key : False for key in perm_votes}

says_mean_thing = 0

says_butter = 0

bot = commands.Bot(command_prefix='!')

bot.remove_command('help')

# changes the bots working location to where it is located
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

user_data_path = 'user_data.json'

last_quote = 0

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#VARIOUS FUNCTIONS


# adds a member to the user data json with 0 for money, offences, and xp
def add_member_to_json(member):

    # loads the data
    with open(user_data_path, 'r') as user_data_file:
        user_data = json.load(user_data_file)
        money_dict = user_data['money']

    if str(member.id) not in money_dict:
            money_dict[member.id] = 0

    for key in ['offences', 'xp']:
        if str(member.id) not in user_data[key]:
            user_data[key][str(member.id)] = [0, 0]

    with open(user_data_path, 'w') as user_data_file:       
        json.dump(user_data, user_data_file)

# takes member to have their balance changed, the amount to add or remove, 
# the channel so Xi jinping can notify them and add_or_remove which is true 
# if adding and false if removing
async def change_ping_bucks(member_id, amount, channel, add_or_remove):

    
    # loads the data
    with open(user_data_path, 'r') as user_data_file:
        user_data = json.load(user_data_file)
        user_money = user_data['money']

    # adds or removes money
    user_money[str(member_id)] += amount if add_or_remove else -amount

    # changes the json
    with open(user_data_path, 'w') as user_data_file:
        json.dump(user_data, user_data_file)
    
    # informs the user what happend
    add_or_remove_message = 'added' if add_or_remove else 'deducted'
    await channel.send(f'{amount} ping bucks have been {add_or_remove_message} to your ping bank account')

#takes a PIL image and sends it to a channel
async def send_image(image, channel):

        with BytesIO() as image_binary:
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            await channel.send(file=discord.File(fp=image_binary, filename='background.png'))

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#EVENT COMMANDS

#assigns roles upon joining and greets member
@bot.event
async def on_member_join(member):
    holy_role = discord.utils.get(member.guild.roles, id=739594604168347789)

    # loads data
    with open(user_data_path, 'r') as user_roles_file:
            user_data = json.load(user_roles_file)
            user_roles = user_data['roles']
    
    add_member_to_json(member)
    
    # gives a user their old role if they left previously
    for user in list(user_roles):
        if str(member.id) not in user_roles:
            await member.add_roles(holy_role)
            break

        if member.id != int(user):
            continue

        for role_id in user_roles[user]:
            role = discord.utils.get(member.guild.roles, id=role_id)
            await member.add_roles(role)


        user_roles.pop(user, None)

    # changes the data
    with open(user_data_path, 'w') as user_roles_file:
        json.dump(user_data, user_roles_file)

    await joins_and_leaves_channel.send(f"OH BLESSED DAY {member.name.upper()} HAS JOINED OUR MIGHTY EMPIRE") 

#records roles upon leaving and informs all other users of the travesty
@bot.event    
async def on_member_remove(member):

    # loads data 
    with open(user_data_path, 'r') as user_data_file:
        user_data = json.load(user_data_file)
        user_roles = user_data['roles']

    # adds the user and their old role to the data file
    user_roles[member.id] =[role.id for role in member.roles if role.id != 739522722169618516]

    # changes the file
    with open(user_data_path, 'w') as user_data_file:
        json.dump(user_data, user_data_file)

    await joins_and_leaves_channel.send(f"{member.name} has left, how dismal")

#startup command for starting loops and setting status
@bot.event
async def on_ready():
    #sets status
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('sex with stalin'))
    # getting the server
    global guild
    guild = bot.get_guild(739522722169618516)

    global announcments_channel
    global joins_and_leaves_channel
    global emoji_channel
    global music_channel
    music_channel = discord.utils.get(guild.channels, id = 753352535187914863)
    joins_and_leaves_channel = discord.utils.get(guild.channels, id = 740287906534391829)
    announcments_channel = discord.utils.get(guild.channels, id = 741711058044977285)
    emoji_channel = discord.utils.get(guild.channels, id = 740299204307714216)


    # variables for on_message, put here to make it look cleaner
    global last_author
    global messages
    global muterole
    global last_time
    global product_exists
    global gaming_cam
    gaming_cam = discord.utils.get(guild.members, id=239150965217820672)
    muterole = discord.utils.get(guild.roles, id=739538288255303710)
    global gaming_cam_rol
    for roel in guild.roles:
        # print(roel)
        # print(roel.id)
        if roel.id == 739680352993280001:
            gaming_cam_rol = roel

    product_exists = False
    messages = 0
    last_author = ''
    last_time = 0

    # variables for free game check
    global old_games
    global game_deals
    global bot_is_sleep
    bot_is_sleep = False
    game_deals = bot.get_channel(739529274964574360)
    print(f"Got channel {game_deals}\n")
    old_games = []
    
    # random words
    global r
    r = RandomWords()    

    # emojis
    global sad_zeggy
    sad_zeggy = discord.utils.get(guild.emojis, name='Sad_Zeggy')
    global cool_zeggy
    cool_zeggy = discord.utils.get(guild.emojis, name='Cool_Zeggy')
    global anarchist_zeggy
    anarchist_zeggy = discord.utils.get(guild.emojis, name='Anarchist_Zeggy')
    global anime_zeggy
    anime_zeggy = discord.utils.get(guild.emojis, name='Anieggy')
    global ninja_zeggy
    ninja_zeggy = discord.utils.get(guild.emojis, name='Zinja')
    global thwomp_zeggy
    thwomp_zeggy = discord.utils.get(guild.emojis, name='Thweggy')

    # generates json
    # for member in guild.members:
    #     add_member_to_json(member)
    #     await member.edit(mute=False)
    #     await member.edit(deafen=False)

    manage_offences.start()

    print("I'm ready to ping some pongs\n")

#event command for xp and muting
@bot.event
async def on_message(message):
    if bot_is_sleep == False:
        # variables for later use
        global last_author
        global messages
        global muterole
        global last_time

        # getting the author to a shorter name
        author = message.author

        # loading user data
        with open(user_data_path, "r") as user_data_file:
            user_data = json.load(user_data_file)
            xp_dict = user_data['xp']
            offences = user_data['offences']
        
        # checks that the message author is not a bot
        if not (author.id in [701139756330778745, 706689119841026128, 741016411463352362, 748564047649177610]):
            #commands that use spaces
            #checks if the message is in emoji channel and then checks if the message is an emoji or not
            msg_content = message.content
            if str(message.channel.id) == "740299204307714216":
                #I made it so he just deletes the message
                if not (any(str(emoji) in msg_content for emoji in message.guild.emojis)) and not (any(str(emoji) in msg_content for emoji in UNICODE_EMOJI)):
                    await message.delete()

            # if str(message.channel.id) == "744264609875230741":
            #     await message.delete()
        
            #ping balance
            if str(message.content.upper()) in ["!PING BUX", "!PING BAL", "!BAL"]:
                with open(user_data_path, 'r') as user_data_file:
                    await message.channel.send(f"you have {json.load(user_data_file)['money'][str(message.author.id)]} ping bucks in your ping bank account")

            #ping level
            if str(message.content.upper()) in ["!PING LEVEL", "!LEVEL"]:
                with open(user_data_path, 'r') as user_data_file:
                    poggers_level = json.load(user_data_file)['xp'][str(message.author.id)][1]
                    await message.channel.send(f"you are level {poggers_level - 1}")

            if "DUDE" in str(message.content.upper()) or "CRINGE" in str(message.content.upper()):
                await message.add_reaction("👎")

            says_mean_thing = randint(1, 100)

            if says_mean_thing == 25:
                await message.channel.send(f"Well {message.author.name}, I guess I must have early onset Alzheimer's, because I dont remember asking.")

            #anti spam
            if time() - last_time < 0.75 and last_author == author.id:
                messages += 1

            else:
                messages = 0
            
            if messages > 4 or "@everyone" in message.content:
                
                # gets the users current offences
                current_offences = offences[str(author.id)][0] + 1
                
                # gets the time they should be muted for 
                mute_time = time() + ((current_offences - 1) * 60 + 60)
                mute_time_in_seconds = mute_time - time()
                print(f'Muted {author.name} for {mute_time_in_seconds} seconds \n{author.name} has {current_offences} offences')

                # informs the traitor
                await message.channel.send(f"""{author.name.upper()} YOU HAVE MADE A GREVIOUS ERROR, 
        A GREAT LAPSE IN YOUR JUDGEMENT IF YOU WILL,
        AND YOU SHALL PAY,
        YOU HAVE BEEN SILENCED FOR {mute_time_in_seconds} SECONDS!!#!!!@3!3!#@!!!""")

                # mutes them
                await author.add_roles(muterole)
                
                offences[str(author.id)] = [current_offences, mute_time]

                with open(user_data_path, 'w') as user_data_file:
                    json.dump(user_data, user_data_file)

                with open('user_data.json', 'r') as user_data_file:
                    user_data = json.load(user_data_file)
                    xp_and_level = user_data['xp']

                xp = xp_and_level[str(author.id)][0]
                level = xp_and_level[str(author.id)][1]

                if xp >= level ** 2:

                    xp_and_level[str(author.id)][1] += 1
                    await message.channel.send(f"WOW you just increased you ping level to {level}")
                
                xp_and_level[str(author.id)][0] += 1
                with open(user_data_path, 'w') as user_data_file:
                    json.dump(user_data, user_data_file)

                # makes it so commands still work
                await bot.process_commands(message)

            # makes it so commands still work
            await bot.process_commands(message)

            # getting a time to compare to 
            last_time = time()

            # sets who messaged last
            last_author = author.id
    await bot.process_commands(message)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#CLIENT COMMANDS

# #vote initate command
# @bot.command()
# async def init_vote(ctx):
#     await ctx.send("voting subject")
#     voting_subject = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
#     await ctx.send("time to vote (hours)")
#     voting_time = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
#     await announcments_channel.send(f"A VOTE HAS BEEN INITIATED. VOTE USING THE VOTE CHANNEL, THE SUBJECT OF THIS VOTE IS {voting_subject.content.upper()} YOU HAVE {voting_time.content} HOURS TO VOTE VOTE Y/N IN THE VOTING CHANNEL")
#     #add json to store votes and what people voted, also add a voting commadd

#toggles bot sleep
@bot.command()
async def sleep(ctx):
    global bot_is_sleep
    if ctx.message.author.id in [351707203981541378, 239150965217820672]:
        print('sleeping bot')
        bot_is_sleep = True
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('sleeping simulator'))

@bot.command()
async def wake(ctx):
    global bot_is_sleep
    if ctx.message.author.id in [351707203981541378, 239150965217820672]:
        print('waking bot')
        bot_is_sleep = False
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('sex with stalin'))

# promote and demote
@bot.command()
async def demote(ctx,*,request):
    if bot_is_sleep == False:
        member = ctx.message.author
        if str(member.id) == "261325935041576960" or str(member) == "351707203981541378":
            request = request.split(', ') 
            
            roles = member.guild.roles
            members = member.guild.members
            
            role_to_demote = None
            for role in roles:
                if str(role) == request[1]:
                    role_to_demote = role
                    
            member_to_demote = None
            for user in members:
                if str(user) == request[0]:
                    member_to_demote = user
            
            await member_to_demote.remove_roles(role_to_demote)

# promote and demote
@bot.command()
async def promote(ctx,*,request):
    if bot_is_sleep == False:
        member = ctx.message.author
        if str(member.id) == "261325935041576960" or str(member) == "351707203981541378":
            request = request.split(', ') 
            
            roles = member.guild.roles
            members = member.guild.members
            
            role_to_demote = None
            for role in roles:
                if str(role) == request[1]:
                    role_to_demote = role
                    
            member_to_demote = None
            for user in members:
                if str(user) == request[0]:
                    member_to_demote = user
            
            await member_to_demote.add_roles(role_to_demote)

#quote command
@bot.command()
async def quote(ctx):
    if bot_is_sleep == False:
        with open('user_data.json', 'r') as user_data_file:
            user_data = json.load(user_data_file)
            quotes = user_data['quotes']
            last_quote = quotes["19"]
            print(last_quote)
        if datetime.today().hour >= last_quote + 1:
            last_quote = datetime.today().hour + 1
            print(last_quote)
            quote_to_use = randint(1, 18)
            await ctx.send(quotes[str(quote_to_use)])
            quotes["19"] = last_quote
            user_data["quotes"] = quotes
            with open(user_data_path, 'w') as user_data_file:
                json.dump(user_data, user_data_file)
        else:
            await ctx.send(f"Unfortunatley, my quote reservoir has run dry, come back in a soon. {sad_zeggy}")

#help command
@bot.command()
async def help(ctx):
    if bot_is_sleep == False:
        await ctx.send('''alas, it appears that you require aid.

        !number_guess..................play a number guessing game to win ping bux
        !ping bal......................gets your ping bux balance
        !whos_that_pokemon.............play a game of whos that pokemon to earn ping bux
        !ping level....................gets your level
        !trivia........................trivia''')

#displays store items
@bot.command()
async def market(ctx,*,request):
    if bot_is_sleep == False:
        global product_exists
        request = request.split(' ')
        market_function = request[0]
        product_exists == False
        with open(user_data_path, 'r') as user_data_file:
            user_data = json.load(user_data_file)
            market_products = user_data['market products']
            money_dict = user_data['money']
            user_inventories = user_data['user inventories']
            user_inventory = user_inventories[str(ctx.message.author.id)]
        user_wallet = money_dict[str(ctx.message.author.id)]

        if market_function.upper() == "BUY":
            product_to_buy = request[1]
            quantity_to_buy = request[2]
            for product in market_products:
                if product.upper() == product_to_buy.upper():
                    if request[2] == "1":
                        product_value = market_products[product[0]]
                        product_exists = True
                        cost = int(product_value) * int(quantity_to_buy)
                        await ctx.send(f'{quantity_to_buy} {product_to_buy} will cost you {cost}, are you sure that you want to purchase this? (Y/N)')
                        response = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
                        if response.content.upper() == "Y":
                            if user_wallet >= int(product_value) * int(quantity_to_buy):
                                await ctx.send(f"{quantity_to_buy} {request[1]}s were added to your inventory")
                                money_dict[str(ctx.message.author.id)] -= cost
                                user_inventory[request[1]] += int(quantity_to_buy)
                                with open(user_data_path, 'w') as user_data_file:
                                    json.dump(user_data, user_data_file)
                            else:
                                await ctx.send(f"@Zeggy give me a line here $@# {quantity_to_buy} {request[1].upper()}")
                        else:
                            await ctx.send(f"{sad_zeggy}")
                    else:
                        product_value = market_products[product[0]]
                        product_exists = True
                        cost = int(product_value) * int(quantity_to_buy)
                        await ctx.send(f'{quantity_to_buy} {product_to_buy}s will cost you {cost}, are you sure that you want to purchase this? (Y/N)')
                        response = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
                        if response.content.upper() == "Y":
                            if user_wallet >= int(product_value) * int(quantity_to_buy):
                                await ctx.send(f"{quantity_to_buy} {request[1]}s were added to your inventory")
                                money_dict[str(ctx.message.author.id)] -= cost
                                user_inventory[request[1]] += int(quantity_to_buy)
                                with open(user_data_path, 'w') as user_data_file:
                                    json.dump(user_data, user_data_file)
                            else:
                                await ctx.send(f"@Zeggy give me a line here ($# {quantity_to_buy} {request[1].upper()}")
                        else:
                            await ctx.send(f"{sad_zeggy}")

            if product_exists == False:
                await ctx.send("@Zeggy give me a line here *$!")
        elif market_function.upper() == "SELL":
            product_to_sell = request[1]
            quantity_to_sell = request[2]
            for product in market_products:
                if product.upper() == product_to_sell.upper():
                    if request[2] == "1":
                        poggers = market_products[product]
                        product_value = poggers[1]
                        product_exists = True
                        cost = int(product_value) * int(quantity_to_sell)
                        await ctx.send(f'{quantity_to_sell} {product_to_sell} will make you {cost}, are you sure that you want to sell this? (Y/N)')
                        response = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
                        if response.content.upper() == "Y":
                            if user_inventory[request[1]] >= int(quantity_to_sell):
                                await ctx.send(f"{quantity_to_sell} {request[1]} was removed from your inventory")
                                money_dict[str(ctx.message.author.id)] += cost
                                user_inventory[request[1]] -= int(quantity_to_sell)
                                with open(user_data_path, 'w') as user_data_file:
                                    json.dump(user_data, user_data_file)
                            else:
                                await ctx.send("@Zeggy give me a line here $@#")
                        else:
                            await ctx.send(f"{sad_zeggy}")
                    else:
                        poggers = market_products[product]
                        product_value = poggers[1]
                        product_exists = True
                        cost = int(product_value) * int(quantity_to_sell)
                        await ctx.send(f'{quantity_to_sell} {product_to_sell}s will make you {cost}, are you sure that you want to sell this? (Y/N)')
                        response = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
                        if response.content.upper() == "Y":
                            if user_inventory[request[1]] >= int(quantity_to_sell):
                                await ctx.send(f"{quantity_to_sell} {request[1]}s were removed from your inventory")
                                money_dict[str(ctx.message.author.id)] += cost
                                user_inventory[request[1]] -= int(quantity_to_sell)
                                with open(user_data_path, 'w') as user_data_file:
                                    json.dump(user_data, user_data_file)
                            else:
                                await ctx.send("@Zeggy give me a line here $@#")
                        else:
                            await ctx.send(f"{sad_zeggy}")
        else:
            await ctx.send("@Zeggy give me a line here $&^")
    
@bot.command()
async def quantity(ctx,*,request):
    if bot_is_sleep == False:
        request = request.split(' ')
        with open(user_data_path, 'r') as user_data_file:
            user_data = json.load(user_data_file)
            user_inventories = user_data['user inventories']
            user_inventory = user_inventories[str(ctx.message.author.id)]
        for key in user_inventory:
            if key == request[0]:
                await ctx.send(f"you have {user_inventory[request[0]]} {request[0]}s")   

@bot.command()
async def give_money(ctx,*,request):
    if bot_is_sleep == False:
        request = request.split(' ')
        if ctx.message.author.id in [239150965217820672, 351707203981541378]:
            await change_ping_bucks(ctx.message.author.id, int(request[0]), ctx.message.channel, True)

#number guessing
@bot.command()
async def number_guess(ctx):
    if bot_is_sleep == False:    
        #variable declarations including random number
        play_again = ''
        guesses = 7
        number = randint(1, 100)
        
        #while loop to play the game
        while True:
            
            #asks the user to guess a number then checks if the next message is from the caller of  the command
            await ctx.send("Guess a number")
            guess = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
            
            #checks if the user has no  guesses left
            if guesses < 0:
                
                #says that the user is a stupid idiot because this game is extremely easy to win
                await ctx.send(f"Idiot dumb LOSER dumb idiot pogpega not epic gaming not kekaga the number was {number} dumb idiot man")
                await ctx.send("You really shouldn't have lost considering how easy it is to win")
                await ctx.send("Are you really that dumb and that much of a LOSER that you lost at a game popular among 3rd graders?")
                await ctx.send("Play Again? [Y/n]")
                #asks if the user wants to play again then declares a new number variable if they do want to
                play_again = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
                
                if play_again.content.upper() == "Y":
                    number = randint(1, 100)
                    guesses = 7 
                    continue
                
                else:
                    break
                
                
            # checks if the user has won 
            elif int(guess.content) == number:
                
                # asks the user if they want to play again     
                await ctx.send("You won, play again [Y/n]")
                await change_ping_bucks(ctx.message.author.id, 10, ctx.message.channel, True)
                play_again = await bot.wait_for('message', check=lambda x: x.author == ctx.message.author)
                if play_again.content.upper() == "Y":
                    number = randint(1, 100)
                    guesses = 7
                    continue
                else:
                    break
                    
            elif int(guess.content) < number:
                guesses -= 1
                await ctx.send("You guessed lower than the epic number")
                continue
            else:
                guesses -= 1 
                await ctx.send("You guessed Higher than the epic number")
                continue

#ping command (do we really need this?)
@bot.command()
async def xi_jinping(ctx):
    if bot_is_sleep == False:    
        #Pings the bot
        await ctx.send(f"Pong {round(bot.latency * 1000)}ms")

#put this is dev commands
@bot.command()
async def view_json(ctx):
    if bot_is_sleep == False:
        with open('user_data.json') as user_data_file:
            user_data = json.load(user_data_file)
            print(json.dumps(user_data, indent=4, sort_keys=True))
    
#gets users currnet balance
@bot.command()
async def ping_bal(ctx):
    if bot_is_sleep == False:
        with open(user_data_path, 'r') as user_data_file:
            await ctx.send(f"you have {json.load(user_data_file)['money'][str(ctx.message.author.id)]} ping bucks in your ping bank account")

#trivia
@bot.command(pass_context = True, aliases=['triv', 'triva'])
async def trivia(ctx):
    if bot_is_sleep == False:
        author = ctx.message.author.id

        # variable to get out of the while loop
        playing = True

        categories = {"general knowledge": Category.GENERAL_KNOWLEDGE, 'video games': Category.ENTERTAINMENT_VIDEO_GAMES, 'computers': Category.SCIENCE_COMPUTERS, \
            'mythology': Category.MYTHOLOGY, 'geography': Category.GEOGRAPHY, "history": Category.HISTORY, 'anime': Category.ENTERTAINMENT_JAPANESE_ANIME_MANGA, 'all': None}

        difficulties = {'hard': Difficulty.HARD, 'medium': Difficulty.MEDIUM, 'easy': Difficulty.EASY}
        while playing:
            try:
                await ctx.send(f"Which One: **{', '.join([key.title() if key.title() != 'All' else '**or** All' for key in categories])}**?")
                user_category_response = await  bot.wait_for('message', timeout=60, check = lambda message: message.author == ctx.message.author)
                user_category = categories[user_category_response.content.lower()]

                await ctx.send('what difficulty shall you choose?')
                user_difficulty_response = await  bot.wait_for('message', timeout=60, check = lambda message: message.author == ctx.message.author)
                user_difficulty =  difficulties[user_difficulty_response.content.lower()]
                questions = client.get_questions(amount=20, category=user_category, difficulty=user_difficulty)
                amount_to_win = 0
                if user_difficulty == Difficulty.EASY:
                    amount_to_win = 10
                elif user_difficulty == Difficulty.MEDIUM:
                    amount_to_win = 20
                else:
                    amount_to_win = 40
                
            except:
                await ctx.send("THAT IS NOT A VALID RESPONSE YOU DIMWITTED DONKEY, TRY AGAIN ONCE AGAIN YOU NUMSKULL OAF!!11111@2!2!32!$!q111$41!!!!!!")
                continue

            for question in questions:
                await ctx.send(f"**{question.question}**:")
                options = ''
                for i in range(len(question.choices)):
                    options += f'{i + 1}. {question.choices[i]}\n'
                await ctx.send(options)
                user_answer = await  bot.wait_for('message', timeout=60, check = lambda message: message.author == ctx.message.author)
                user_answer = user_answer.content
                if user_answer.upper() == question.answer.upper() or int(user_answer) - 1 == question.answer_index:
                    await ctx.send("WOW you just got the question correct, who could have known")
                    await change_ping_bucks(author, amount_to_win, ctx.message.channel, True)
                else:
                    await ctx.send(f"YOU FEEBLEMINDED IMBECILE, THE CORRECT ANSWER WAS **{question.answer.upper()}**, FOR THIS TREMENDOUS BLUNDER YOU SHALL PAY")
                    
                
                await ctx.send("Would you like to try you hand once again, perhaps with a different category? [Y/D/N]")
                play_again = await  bot.wait_for('message', timeout=60, check = lambda message: message.author == ctx.message.author)
                play_again_content = play_again.content.upper()
                if play_again_content == 'Y':
                    continue
                
                elif play_again_content == 'D':
                    break
                
                else:
                    await ctx.send(f"YOU HAVE FORSAKEN ME {sad_zeggy}")
                    playing = False
                    break
            if play_again_content != 'N':    
                await ctx.send("Alas, my great question river has run dry, ask me once more")

#whos that pokemon game
@bot.command(pass_context = True, aliases=['who_pokemon', 'whothatpokemon', 'whopokemon', 'guess_pokemon', 'guesspokemon'])
async def whos_that_pokemon(ctx):
    if bot_is_sleep == False:
        images = 'images'
        client = pokepy.V2Client()
        check_function = lambda x: x.author == ctx.message.author
        errors = 0
        while True:
            
            if errors >= 5:
                await ctx.send("I probably got ratelimited because you were playing to hard, try again in atleast 30 mintes")
                break

            background = Image.open(f'{images}/background.png')
            pokemon_number = choice(['{:03d}'.format(i) for i in range(1,807)])
            
            pokemon_number_lookup = pokemon_number.lstrip('0')
            pokemon = Image.open(f"{images}/{pokemon_number}.png")
            pokemon_hidden = Image.open(f"{images}/{pokemon_number}.png")
            pixels = pokemon_hidden.load()
            
            for i in range(pokemon_hidden.size[0]):    
                for j in range(pokemon_hidden.size[1]):    
                    
                    if pixels[i,j][3] != 0:
                        pixels[i,j] = (0, 0, 0) 
                    
                    
            background.paste(pokemon_hidden, (50,50,265,265), pokemon_hidden)
            await send_image(background, ctx.message.channel)
            
            try:
                pokemon_name = client.get_pokemon_species(pokemon_number_lookup).name
                
            except:
                await ctx.send("I am deeply apologetic as I have made a great blunder, I will try to do better next time, if there even is a next time")
                errors += 1
                continue

            errors = 0
            await ctx.send('WHOS THAT POKEMON!!!1!!!111!@!')

            try:    
                user_response = await bot.wait_for('message', timeout=60, check=check_function)

            except:           
                await ctx.send(f"I've been waiting here for an eternity how dare you abandon me you callous fool, YOU WILL PAY {sad_zeggy}")

            s = SequenceMatcher(None, user_response.content.upper(), pokemon_name.upper())
            percent_correct = s.ratio()
            print(f'{ctx.message.author} user answer: {user_response.content}')
            print(f'{ctx.message.author} correct answer: {pokemon_name}')
            print(f'{ctx.message.author} percent: {percent_correct}')
            background.paste(pokemon, (50,50,265,265), pokemon)

            if percent_correct > 0.7:
                await ctx.send(f"You got it correct, the pokemon was {pokemon_name.title()}")
                await change_ping_bucks(ctx.message.author.id, 50, ctx.message.channel, True)

            else:
                await ctx.send(f'You got it wrong you loser, the pokemon was obviously {pokemon_name.title()}')
            
            await send_image(background, ctx.message.channel)
            await ctx.send("Do you want to play again [Y/n]")

            try:
                play_again = await bot.wait_for('message', timeout=20, check=check_function)
                
            except:
                await ctx.send("Bye Bye")
                break
            play_again = play_again.content.upper()
            
            if play_again == 'Y' or play_again == "YES":
                continue

            else:
                await ctx.send(f"im devistated {sad_zeggy}")
                break

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#SOUNDS

@bot.command()
async def soundboard(ctx):
    if bot_is_sleep == False:
        global music_channel
        await ctx.message.author.voice.channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.message.author.guild)
        message = await music_channel.send('''react to play sounds''')
        await message.add_reaction("💣")
        await message.add_reaction("❌")

# @bot.command()
# async def soundboard_ninja(ctx):
#     global music_channel
#     await ctx.message.author.voice.channel.connect()
#     voice = discord.utils.get(bot.voice_clients, guild=ctx.message.author.guild)
#     message = await music_channel.send('''react to play ninja sounds''')
#     await message.add_reaction("💣")
#     await message.add_reaction("❌")

@bot.event
async def on_reaction_add(reaction, user):
    if bot_is_sleep == False:
        global guild
        channel = reaction.message.channel
        if channel.id == 753352535187914863:
            if user.id != 701139756330778745:
                if reaction.message.content == "react to play sounds":
                    if reaction.emoji == "💣":
                        voice = discord.utils.get(bot.voice_clients, guild=guild)
                        voice.play(discord.FFmpegPCMAudio('sounds\Boom.mp3'))
                        voice.volume = 100
                    if reaction.emoji == "❌":
                        voice = discord.utils.get(bot.voice_clients, guild=guild)
                        await voice.disconnect()

@bot.command()
async def play(ctx, url):
    if bot_is_sleep == False:
        print("joining")
        if not ctx.message.author.voice:
            await ctx.send("YOU BUFFOON YOU ARE NOT CONNECTED TO A VOICE CHANNEL, CONNECT TO ONE TO USE MY VAST MUSICAL CAPABILITIES")
            return
        
        else:
            channel = ctx.message.author.voice.channel

        await channel.connect()

        server = ctx.message.guild
        voice_channel = server.voice_client
        
        voice = discord.utils.get(bot.voice_clients, guild=ctx.message.author.guild)
        player = await YTDLSource.from_url(url, loop=bot.loop)
        voice_channel.play(player, after=lambda e: print('stupid dumb idiot thing happen: %s' % e) if e else None)

        await ctx.send('playing {}'.format(player.title))

@bot.command()
async def leave(ctx):
    if bot_is_sleep == False:
        print("leaving")
        voice = discord.utils.get(bot.voice_clients, guild=ctx.message.author.guild)
        await voice.disconnect()
        print("left")


        
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#LOOP

# lowers offences and unmutes people (checks every 30 seconds)           
@tasks.loop(minutes=30)
async def manage_offences():
    global muterole
    global gaming_cam_rol
    # perms = discord.Permissions(manage_channels=True, manage_roles=True)
    # await guild.create_role(name='poggerss', permissions=perms)
    # channel_role = discord.utils.get(guild.roles, name='poggerss')
    for member in guild.members:
        if member.id == 239150965217820672:
            await member.add_roles(gaming_cam_rol)

    # loads the data
    with open(user_data_path, 'r') as user_data_file:
        user_data = json.load(user_data_file)
        offences = user_data['offences']
        
    # loops through members
    for member_id in offences:
        member_value = offences[member_id]

            # removes one offence every 12 hours and 12 PM and AM 
            if datetime.today().hour % 12 == 0 and member_value[0] > 0:
                member_value[0] -= 1 

            else:
                member_value[0] = 0
            # checks if it is time to unmute someone    
            if (time() - member_value[1]) > 0 and member_value[1] != 0:

                #gets the member from their id
                member_to_unmute = discord.utils.get(guild.members, id=int(member_id))
                
                # removes the mute role
                await member_to_unmute.remove_roles(muterole)

                # resets their unmute time
                member_value[1] = 0
                print(f'Unmuted {member_to_unmute.name}')

        # changes the json
        with open(user_data_path, 'w') as user_data_file:
            json.dump(user_data, user_data_file)

    #await test()

    permissions_channel = discord.utils.get(guild.channels, id=741711058044977285)
    print(has_perms)
    async for message in permissions_channel.history(limit=100):
        
        
        # makes it so exeptions can be passed
        if perm_votes[message.content] == None:
            continue
        
        elif  isinstance(perm_votes[message.content], int):
            perms = discord.Permissions()
            
            thumbs_up = 0
            thumbs_down = 0
            for reaction in message.reactions:
                if reaction.emoji == '👎':
                    thumbs_down = reaction.count
                elif reaction.emoji == '👍':
                    thumbs_up = reaction.count

            role = discord.utils.get(guild.roles, id = perm_votes[message.content])
            counts = [number.count for number in message.reactions]
            if (thumbs_up >= thumbs_down or any(number >= len(guild.members) for number in counts)) and not has_perms[message.content]:
                has_perms[message.content] = True 
                perms.update(mute_members = True, move_members = True) 
                try:
                    await role.edit(permissions = perms, colour = discord.Color.dark_orange())
                    print(3)
                    sleep(10)
                except Exception as e:
                    print(e)
                    

            else:
                if has_perms[message.content]:
                    has_perms[message.content] = False
                    perms.update(mute_members = False, move_members = False)
                    try:
                        await role.edit(permissions = perms, colour = discord.Color.dark_orange())
                        print(3)
                        sleep(10)
                    except Exception as e:
                        print(e) 

@tasks.loop(hours=12)
async def change_colors():
    
    print(1)
    for role in guild.roles:    
       
        if role.name.upper() != "ZEGGY, KING OF KINGS":
            await role.edit(colour = discord.Colour.from_rgb(randint(0,256) ,randint(0,256) ,randint(0,256))) 


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#getting the key and starting the bot


#if it doesnt work remember to cd into the right place cam you absolute idot
f = open("token.txt", "r") # get key
# Use test token if testing new features
TOKEN = f.readline()
TEST_TOKEN = f.readline()
f.close()

bot.run(str(TEST_TOKEN))