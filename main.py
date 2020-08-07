import os
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
from random import randint, choice
from difflib import SequenceMatcher
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix='!')

bot.remove_command('help')

# gets the joins-leaves channel
joins_and_leaves_channel = bot.get_channel(740287906534391829)

# changes the bots working location to where it is located
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

user_data_path = 'user_data.json'


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
    add_or_remove_message = 'added' if add_or_remove else 'removed'
    await channel.send(f'{amount} ping bucks have been {add_or_remove_message} to your ping bank account')

#takes a PIL image and sends it to a channel
async def send_image(image, channel):

        with BytesIO() as image_binary:
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            await channel.send(file=discord.File(fp=image_binary, filename='background.png'))

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

@bot.event
async def on_ready():

    # variables for on_message, put here to make it look cleaner
    global last_author
    global messages
    global muterole
    global last_time

    # variables for free game check
    global old_games
    global game_deals
    game_deals = bot.get_channel(739529274964574360)
    print(f"Got channel {game_deals}\n")
    old_games = []

    # getting the server
    global guild
    guild = bot.get_guild(739522722169618516)


    muterole = discord.utils.get(guild.roles, id=739538288255303710)
    messages = 0
    last_author = ''
    last_time = 0


    # generates json
    for member in guild.members:
        add_member_to_json(member)


        
    #starts the thursday loop
    called_on_thursday.start()

    #starts the manage offences loop
    manage_offences.start()

    print("I'm ready to ping some pongs\n")

#MUTING AND UNMUTING
#text chat control and muting
#needs updates for ocmpatibility with xjp2
@bot.event
async def on_message(message):


    # variables for later use
    global last_author
    global messages
    global muterole
    global last_time

    # getting the author to a shorter name
    author = message.author

    # getting the role that mutes people
    

    # loading user data
    with open(user_data_path, "r") as user_data_file:
        user_data = json.load(user_data_file)
        xp_dict = user_data['xp']
        offences = user_data['offences']
    

    

    # checks that the message author is not a bot
    if not (author.id in [701139756330778745, 706689119841026128, 741016411463352362]):
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
        

            

    
    
    
    # getting a time to compare to 
    last_time = time()

    # sets who messaged last
    last_author = author.id

    # makes it so commands still work
    await bot.process_commands(message)

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
            sleep(0.5)
            await ctx.send("You really shouldn't have lost considering how easy it is to win")
            sleep(0.5)
            await ctx.send("Are you really that dumb and that much of a LOSER that you lost at a game popular among 3rd graders?")
            sleep(0.5)
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
            await change_ping_bucks(ctx.message.author, 10, ctx.message.channel, True)
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

@bot.command()
async def xi_jinping(ctx):
    
    #Pings the bot
    await ctx.send(f"Pong {round(bot.latency * 1000)}ms")

@bot.command()
async def view_json(ctx):
    with open('user_data.json') as user_data_file:
        user_data = json.load(user_data_file)
        print(json.dumps(user_data, indent=4, sort_keys=True))

@bot.command()
async def ping_bal(ctx):
    with open(user_data_path, 'r') as user_data_file:
        await ctx.send(f"you have {json.load(user_data_file)['money'][str(ctx.message.author.id)]} ping bucks in your ping bank account")

@bot.command(pass_context = True, aliases=['who_pokemon', 'whothatpokemon', 'whopokemon', 'guess_pokemon', 'guesspokemon'])
async def whos_that_pokemon(ctx):
    images = 'images'
    client = pokepy.V2Client()
    check_function = lambda x: x.author == ctx.message.author
    errors = 0
    while True:
        sad_zeggy = discord.utils.get(ctx.message.guild.emojis, name='Sad_Zeggy')
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

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def bomb(ctx):
    await ctx.message.author.voice.channel.connect()
    voice = discord.utils.get(bot.voice_clients, guild=ctx.message.author.guild)
    voice.play(discord.FFmpegPCMAudio('Boom.mp3'))
    voice.volume = 100
    while voice.is_playing():
        continue
    await voice.disconnect()

@tasks.loop(hours=1)
async def called_on_thursday():
    global old_games

    # Gets the message channel to send to 
    message_channel = bot.get_channel(739529274964574360)
    print(f"Got channel {message_channel}\n")
    
    hour = datetime.today().hour
    # Checks if it is thursday and sends reminder
    if datetime.today().weekday() == 3 and (hour == 11):

        await message_channel.send("@everyone New Epic Time Gaming Time Epic time Gaming Time Epic free time gaming ")


    HEADERS = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}

    request = get("https://steamdb.info/sales/", timeout=10, headers=HEADERS)



    html = BeautifulSoup(request.content, 'html.parser')

    discounts = html.find_all('tr')

    row_lst = [discount for discount in discounts]
    row_lst.pop(0)

    row_lst_clean = []


    for row in row_lst:
        indivdual_row = []
        for string in row.stripped_strings:
            indivdual_row.append(string)
        row_lst_clean.append(indivdual_row)


    

    for row in row_lst_clean:
        for element in row:
            
            if element == '$0.00' and old_games.count(str(row[0])) <= 0:
                
                
                old_games.append(row[0])
                
                
                await message_channel.send(f'@everyone {row[0]} is free on steam')

# lowers offences and unmutes people             
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
        if datetime.today().hour % 12 == 0:
            member_value[0] -= 1 
            
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



f = open("token.txt", "r") # get key
# Use test token if testing new features
TOKEN = f.readline()

TEST_TOKEN = f.readline()
f.close()


bot.run(str(TOKEN))