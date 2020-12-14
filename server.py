import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json
import requests
import math

clients_lock = threading.Lock()
connected = 0

players = []
matches = -1
inMatch = False

clients = {}

def getPlayersInfo():
   global players

   baseUrl = "https://qrjm1bxr2c.execute-api.ca-central-1.amazonaws.com"
   endPoint = "/default/GetPlayers"

   resp = requests.get(baseUrl + endPoint)
   respBody = json.loads(resp.content)
   print(respBody)

   for r in respBody:
      players.append(r)
   
   #print(players[7])
   #print(len(players))


def updatePlayerInfo(player_id, exp, lvl):
   baseUrl = "https://y5mb5h569h.execute-api.ca-central-1.amazonaws.com"
   endPoint = "/default/UpdatePlayers"
   queryParams = {"player_id" : player_id, "exp" : exp, "lvl" : lvl}

   #resp = requests.get(baseUrl + endPoint)
   resp = requests.get(baseUrl + endPoint, params=queryParams)
   respBody = json.loads(resp.content)
   print(respBody)

#Get random players with match of 2
def get2RandomPlayers(playersList):

   ranP = []

   p1 = random.randint(0, 9)
   ranP.append(playersList[p1]['player_id'])
   
   p2 = p1
   while p2 == p1:
      p2 = random.randint(0, 9)
   ranP.append(playersList[p2]['player_id'])

   return ranP


#Get random players with match of 3
def get3RandomPlayers(playersList):

   ranP = []

   p1 = random.randint(0, 9)
   ranP.append(playersList[p1]['player_id'])
   
   p2 = p1
   while p2 == p1:
      p2 = random.randint(0, 9)
   ranP.append(playersList[p2]['player_id'])

   p3 = p2
   while p3 == p2 or p3 == p1:
      p3 = random.randint(0, 9)
   ranP.append(playersList[p3]['player_id'])

   return ranP


def connectionLoop(sock):
   global matches
   global inMatch
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
         if 'matches' in data:
            data = data.replace("'","")
            data = data.replace("bmatches","")
            matches = int(data)
            inMatch = False
            #print(matches)
         if 'result' in data:
            data = data.replace("'","")
            data = data.replace("bresult","")
            print(data)
            result = data.split(',')

            listCurrentLVL = []           

            for i in range(len(result)):
               for p in players:
                  if result[i] == p['player_id']:
                     listCurrentLVL.append(int(p['lvl']))
                     break
            
            #print(listCurrentLVL)

            #print(players)

            for i in range(len(result)):
               for p in players:
                  if result[i] == p['player_id']:
                     totalEXP = 2 * (len(result) - i)
                     if i == 0:                 
                        extraEXP = abs(listCurrentLVL[0] - max(listCurrentLVL))
                        totalEXP += extraEXP
                     pEXP = int(p['exp'])
                     pEXP += totalEXP
                     p['exp'] = str(pEXP)

                     pLVL = math.floor(math.sqrt(pEXP))
                     p['lvl'] = str(pLVL)

                     updatePlayerInfo(p['player_id'], p['exp'], p['lvl'])

                     break
            
            #print(players)
                                 


      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            message = {"cmd": 0,"player":{"id":str(addr)}}
            m = json.dumps(message)
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))


def cleanClients():
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      time.sleep(1)


def gameLoop(sock):
   global matches
   global inMatch
   while True:
      if matches > 0 and inMatch == False:
         #print(matches)
         numP = random.randint(2, 3)
         playersInMatch = []
         if numP == 2:
            playersInMatch = get2RandomPlayers(players)
         else:
            playersInMatch = get3RandomPlayers(players)
         
         inMatch = True
         #print(playersInMatch)
         
         PinM = {"cmd": 2, "pinMs": []}
         for p in playersInMatch:
            pr = {}
            pr['id'] = str(p)
            for pl in players:
               if p == pl['player_id']:
                  pr['exp'] = str(pl['exp'])


            PinM['pinMs'].append(pr)

         s=json.dumps(PinM)
         for c in clients:
            sock.sendto(bytes(s,'utf8'), (c[0],c[1]))




      
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      #print (clients)
      for c in clients:
         player = {}
         #clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         #player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
     #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)


def main():
   getPlayersInfo()

   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,())
   while True:
      time.sleep(1)


if __name__ == '__main__':
   main()
