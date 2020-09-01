import os
import re
import json
import pokepy
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
from pyopentdb import OpenTDBClient, Category, QuestionType, Difficulty

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#RANDOM SETUP THINGS

# instance of the trivia api wrapper library class
client = OpenTDBClient()

bot = commands.Bot(command_prefix='!')

bot.remove_command('help')

# gets the joins-leaves channel
joins_and_leaves_channel = bot.get_channel(740287906534391829)

# changes the bots working location to where it is located
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

user_data_path = 'user_data.json'

last_quote = 0
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

    # variables for on_message, put here to make it look cleaner
    global last_author
    global messages
    global muterole
    global last_time
    global emoji_channel
    
    muterole = discord.utils.get(guild.roles, id=739538288255303710)
    emoji_channel = bot.get_channel(740299204307714216)
    messages = 0
    last_author = ''
    last_time = 0


    # variables for free game check
    global old_games
    global game_deals
    game_deals = bot.get_channel(739529274964574360)
    print(f"Got channel {game_deals}\n")
    old_games = []

    
    # random words
    global r
    r = RandomWords()    

    # emojis
    global sad_zeggy
    sad_zeggy = discord.utils.get(guild.emojis, name='Sad_Zeggy')


    # generates json
    for member in guild.members:
        add_member_to_json(member)

    #starts the manage offences loop
    manage_offences.start()

    print("I'm ready to ping some pongs\n")

#event command for xp and muting
@bot.event
async def on_message(message):


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
            
            
                
            #         print("there is text!")
            #         await message.channel.send(f"""{author.name.upper()} YOU HAVE MADE A GREVIOUS ERROR, 
            # A GREAT LAPSE IN YOUR JUDGEMENT IF YOU WILL,
            # AND YOU SHALL PAY FOR YOUR SINS, 
            # YOU HAVE BEEN WARNED!!!#@!#!@#!@!!@#!@#!@#!@#!@@!@@!!!!""")
        
        else:
            
        
            #ping balance
            if str(message.content.upper()) == "!PING BUX":
                with open(user_data_path, 'r') as user_data_file:
                    await message.channel.send(f"you have {json.load(user_data_file)['money'][str(message.author.id)]} ping bucks in your ping bank account")

            #ping balance
            if str(message.content.upper()) == "!PING LEVEL":
                with open(user_data_path, 'r') as user_data_file:
                    await message.channel.send(f"you are level {json.load(user_data_file)['xp'][str(message.author.id)][1]}")

            #says hello
            if (str(message.content.upper()) in ["HELLO XIJINPING", "HELLO XI JINPING", "HELLO XI", "HELLO MR.XI"]):
                await message.channel.send(f"hello {message.author.name}")

            #says hello
            if (str(message.content.upper()) in ["GOODNIGHT XIJINPING", "GOOD NIGHT XIJINPING", "GOODNIGHT XI JINPING", "GOODNIGHT XIJINPING", "GOODNIGHT XI", "GOOD NIGHT XI", "GOODNIGHT MR.XI", "GOOD NIGHT MR.XI"]):
                await message.channel.send(f"goodnight {message.author.name}")

            #says hello
            if (str(message.content.upper()) in ["GOOD MORNING XIJINPING", "GOOD MORNING XI JINPING", "GOODMORNING XIJINPING", "GOODMORNING XI JINPING", "GOODMORNING XI", "GOOD MORNING XI", "GOODMORNING MR.XI", "GOOD MORNING MR.XI"]):
                await message.channel.send(f"good morning {message.author.name}")
            
            #says you're welcome
            if (str(message.content.upper()) in ["THANK YOU XIJINPING", "THANK YOU XI JINPING", "THANK YOU XI", "THANK YOU MR.XI", "TY XIJINPING", "TY XI JINPING", "TY XI", "TY MR.XI", "TY XIJINPING", "TY XI JINPING", "TY XI", "TY MR.XI"]):
                await message.channel.send(f"you're welcome {message.author.name}")

            #anti spam
            if time() - last_time < 0.75 and last_author == author.id:
                messages += 1

            else:
                messages = 0
            
            if messages > 4:
                
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

            else:
                #not working rn and i dont feel like fixing it
                # if str(message.content.upper()) == "!store buy test product":
                #     with open('user_data.json', 'r') as user_data_file:
                #         user_data = json.load(user_data_file)
                #         money_dict = user_data['money']
                #     for key in money_dict:
                #         if key == str(message.author.id):
                #             money = money_dict[str(key)]
                #     if int(money) > 15:
                #         await message.channel.send("gamer")
                #     else:
                #         await message.channel.send("not gamer")

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

        
            # getting a time to compare to 
            last_time = time()

            # sets who messaged last
            last_author = author.id

            # makes it so commands still work
            await bot.process_commands(message)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#CLIENT COMMANDS

#quote command
@bot.command()
async def quote(ctx):
    with open('user_data.json', 'r') as user_data_file:
        user_data = json.load(user_data_file)
        quotes = user_data['quotes']
    if datetime.today().hour >= last_quote + 1:
        quote_to_use = randint(1, 18)
        print(quotes[str(quote_to_use)])
        await ctx.send(quotes[str(quote_to_use)])

#help command
@bot.command()
async def help(ctx):
    await ctx.send('''alas, it appears that you require aid.

    !number_guess..................play a number guessing game to win ping bux
    !ping_bal......................gets your ping bux balance
    !whos_that_pokemon.............play a game of whos that pokemon to earn ping bux
    !level(dont use right now pls).........................might add soon, will probable get your level''')

#displays store items
@bot.command()
async def market(ctx):
    await ctx.send('''the ping store:
    test product....................(15 ping bux) please dont buy, this is just a test''')

#number guessing
@bot.command()
async def number_guess(ctx):
    
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
    
    #Pings the bot
    await ctx.send(f"Pong {round(bot.latency * 1000)}ms")

#put this is dev commands
@bot.command()
async def view_json(ctx):
    with open('user_data.json') as user_data_file:
        user_data = json.load(user_data_file)
        print(json.dumps(user_data, indent=4, sort_keys=True))

#gets users currnet balance
@bot.command()
async def ping_bal(ctx):
    with open(user_data_path, 'r') as user_data_file:
        await ctx.send(f"you have {json.load(user_data_file)['money'][str(ctx.message.author.id)]} ping bucks in your ping bank account")

#trivia
@bot.command(pass_context = True, aliases=['triv', 'triva'])
async def trivia(ctx):

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

#bomb, i really want this removed but i doubt that theo would permit such an action
@bot.command(pass_context=True)
async def bomb(ctx):
    if (ctx.message.author.id in [351707203981541378, 239150965217820672]):
        await ctx.message.author.voice.channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.message.author.guild)
        voice.play(discord.FFmpegPCMAudio('Boom.mp3'))
        voice.volume = 100
        while voice.is_playing():
            continue
        await voice.disconnect()

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#LOOP

# lowers offences and unmutes people (checks every 30 seconds)           
@tasks.loop(seconds=30)
async def manage_offences():

    global muterole

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

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#getting the key and starting the bot

#if it doesnt work remember to cd into the right place cam you absolute idot
f = open("token.txt", "r") # get key
# Use test token if testing new features
TOKEN = f.readline()
TEST_TOKEN = f.readline()
f.close()

bot.run(str(TOKEN))