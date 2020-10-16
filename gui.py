import PySimpleGUI as sg
import json

layout = [[sg.Text("Hello from PySimpleGUI")], [sg.Button("Sleep bot")], [sg.Button("Wake bot")], [sg.Button("Turn off bot (DONT USE)")]]

# Create the window
window = sg.Window("Demo", layout)

# Create an event loop
while True:
    event, values = window.read()
    if event == "Sleep bot":
        with open("test.json", 'r') as user_data_file:
            data = json.load(user_data_file)
            datadict = data['data']
            datadict["bot_is_sleep"] = "1"
        with open("test.json", 'w') as user_data_file:       
            json.dump(data, user_data_file)
    if event == "Wake bot":
        with open("test.json", 'r') as user_data_file:
            data = json.load(user_data_file)
            datadict = data['data']
            datadict["bot_is_sleep"] = "0"
        with open("test.json", 'w') as user_data_file:       
            json.dump(data, user_data_file)
    if event == "Turn off bot (DONT USE)":
        with open("test.json", 'r') as user_data_file:
            data = json.load(user_data_file)
            datadict = data['data']
            datadict["turn_off"] = "1"
        with open("test.json", 'w') as user_data_file:       
            json.dump(data, user_data_file)
            window.close()
    if event == sg.WIN_CLOSED:
        break
window.close()