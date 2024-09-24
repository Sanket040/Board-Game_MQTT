# Importing Packages
import paho.mqtt.client as mqttClient
import time
import random
import math
import sys
import ast
import ssl


# Getting player info of given line number 
def get_player_info(line_number):
	input_file = f"player-{player_id}.txt"   
	with open(input_file, 'r') as file:     # Opening input text file to get Data point and power of perticular line number
		lines = file.readlines()      
		if 0 < line_number <= len(lines):
			line = lines[line_number - 1].strip()
			if line:
				player_data = line.split()
				x, y, power_status = map(int, player_data)
				return {"x": x, "y": y, "power_status": power_status}   # Returning Dictionary of player location and power status
			else :
				return {}  # Returns empty dictionary if line is empty
		else:
			return {}    # Returns empty dictionary if line_number is out of range


# Calculating distance between 2 players 
def distance(curr,to):
    return math.sqrt((to['x']-curr['x'])**2+(to['y']-curr['y'])**2)   



# Function call of On connect Method
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker\n")
        global Connected  # Use global variable
        Connected = True  # Signal connection
    else:
        print("Connection failed Return Code : ",rc)
        
        
# Function call for On Message method
def on_message(client, userdata, message):
	global total
	print("message received")
	
	# for getting player location
	if(message.topic.startswith("Player_location")):      
		time.sleep(0.25)
		print("Location : " + str(message.payload))  #  {'x': 4, 'y': 3, 'power_status': 1}
		pl = message.topic.split("/")[-1]
		print("Received from - " + str(pl))  #  Player_location/player-i
		to = ast.literal_eval(message.payload.decode())
		dist = distance(location, to)
		print(f"Distance : {dist} \n")   # Print Distance
		
		# Check if Player is adjacent or not if power is 1
		if(dist <= math.sqrt(2) and to['power_status'] == 1 and location['power_status'] != 1):     
			killer = message.topic.split("/")[-1]
			msg = killer + f" Killed Player-{player_id}"
			print("player-"+player_id+"/status\n")
			client.publish("player-"+player_id+"/status", msg)    # Publishing Kill message to other players
			print(f".........player-{player_id}.........")
			print(msg) 
			print(".........You are Out.........")
			client.disconnect()
			client.loop_stop()   # Stoping player which is Out of the game
			
	
	# for Killing message
	if(message.topic.startswith("player-")):       
		total -= 1
		print(".............................")
		print(str(message.payload.decode()))  #  Player-i Killed by player player-j
		print(".............................\n\n")
		if(total == 1):
			print("-------------------------------------")
			print(f"    player-{player_id} is the Winner    ")    # Winning message
			print("-------------------------------------")
			client.disconnect()
			client.loop_stop()     
	
	
Connected = False
client_name = sys.argv[1].split(".")[0]
player_id = sys.argv[1].split("-")[1].split(".")[0]  # Getting Player ID
with open('player-1.txt', 'r') as file:
    num_players = int(file.readline())  # Getting total number of players joined
total = num_players


#AWS_PART
client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1, client_name)  # create new instance
client.on_connect = on_connect  # attach function to callback
client.on_message = on_message  # attach function to callback

awshost = "a1vg3m1my288z3-ats.iot.us-east-1.amazonaws.com" #replace
awsport = 8883

caPath = "./root-CA.crt" # Root certificate authority, comes from AWS (Replace)
certPath = "./IOT_sample.cert.pem" #Replace
keyPath = "./IOT_sample.private.key" #Replace

client.tls_set(caPath, 
    certfile=certPath, 
    keyfile=keyPath, 
    cert_reqs=ssl.CERT_REQUIRED, 
    tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

client.connect(awshost, port = awsport)  # connect to broker
#AWS PART ENDS


client.loop_start()  # start the loop


print(" current Player ID " + player_id)
p_id = int(player_id)

# Subscribe to all player topics
for other_player_id in range(1, num_players + 1):
    if other_player_id != p_id:
        client.subscribe(f"Player_location/player-{other_player_id}")    # Subscribing to Player_location/player-1
        print(f"Player subscribed for Player_location/player-{other_player_id}")   # Player_location/player-1 

for other_player_id in range(1, num_players + 1):
    if other_player_id != p_id:
        client.subscribe(f"player-{other_player_id}/status")    # Subscribing to player-ID/status
        print(f"Player subscribed for player-{other_player_id}/status")
 
 
print("-------------------------------------")
print(f"    Waiting for Players to Join    ")
print("-------------------------------------")

timer = 10
if num_players > 12 and num_players < 20:
	timer = 12
if num_players >= 20:
	timer = 15
	 
time.sleep(timer)
location = get_player_info(2)
time.sleep(timer-3)  # Wait while other players subscribe
client.publish("Player_location/player-"+player_id, str(location))
print("Message published is : " + str(location))
line_number = 2

# Try Except Block
try:
    while(1):
    	if total == 1 :
    		break
    	line_number +=1
    	time.sleep(timer)  # Wait while other players subscribe
    	location = get_player_info(line_number)
    	time.sleep(timer-3)
    	client.publish("Player_location/player-"+player_id, str(location))
    	print("Message published is : " + str(location))

except KeyboardInterrupt:
     print("exiting")
     client.disconnect()
     client.loop_stop()

client.loop_stop()


