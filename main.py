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
    print("I'm ready to ping some pongs")


#MUTING AND UNMUTING
#text chat control and muting
#needs updates for ocmpatibility with xjp2
@bot.event
async def on_message(message):
    global current_time
    global last_author
    global messages
    global sender
    sender = message.author.id
    messages = ''
    last_author = ''
    roles = ""
    roles = message.author.guild.roles
    
    muterole = discord.utils.get(message.author.roles, id=739538288255303710)

    #loads the userdata json
    with open(user_data_path, "r") as user_data_file:
        userdict = json.load(user_data_file)

    current_time = time()

    #must be changed i think?
    # message_channel = bot.get_channel(target_channel_id)

    if not message.author.id == "701139756330778745" and not message.author.id == "706689119841026128" and not message.author.id == "741016411463352362":
        if time() - current_time < 0.5 and last_author == message.author:
            messages += 1

        else:
            messages = 0

        if messages > 5:
            
            offencedict = userdict["offences"] #gets the offence dictionary
            useroffences = offencedict[str(sender)] #gets users current offences    

            print("muted", sender, " for", useroffences * 60 + 60, " seconds") #self explanatory 
            print(time()) #prints the time
            print(useroffences) #if you're reading this then you are retarded
            print(useroffences + 1) #same here
            await message.author.add_roles(muterole)
            unbantime[str(sender)] = time() + int(useroffences) * 60 + 60
            print(unbantime)

            with open(user_data_path, "w") as user_data_file:
                json.dump(userdict, user_data_file) #writes the new dict to overrite the old one

        elif messages <= 5:
            xpdict = userdict["xp"]
            xp_and_lv = xpdict[str(sender)]
            experience = xp_and_lv[0]
            level = xp_and_lv[1]
            experience += 1
            if experience >= level ** 2:
                level += 1
                await message.channel.send(f'congradulations, you leveled up! your level is now {level}')
            xp_and_lv[1] = level
            xp_and_lv[0] = experience
            xpdict[str(sender)] = xp_and_lv

            with open(user_data_path, "w") as user_data_file:
                json.dump(userdict, user_data_file) #writes the new dict to overrite the old one

    last_author = message.author
    current_time = time()

    await bot.process_commands(message)

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





f = open("token.txt", "r") # get key
# Use test token if testing new features
TOKEN = f.readline()
print(TOKEN)
TEST_TOKEN = f.readline()
f.close()

bot.run(str(TOKEN))