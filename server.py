import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
            data = data.replace("'","")
            data = data.replace("bheartbeat ","")
            pos = data.split()
            clients[addr]['position'] = {'x': float(pos[0]), 'y': float(pos[1]), 'z': float(pos[2])}
            print("Check: ", pos)
      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = 0

            #--When there is a newly connected client, send a list of all the currently connected clients to the connected clients--#
            message = {"cmd": 0,"player":[]}
            for c in clients:
               #message["player"].append((c[0],c[1]))
               player = {}
               player['id'] = str(c)
               if addr == c:
                  player['identity'] = 1
               else:
                  player['identity'] = 0
               message['player'].append(player)
            #message = {"cmd": 0,"player":{"id":str(addr)}}

            m = json.dumps(message)
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            
            #--Create message to inform all current clients about the dropped player--#
            message = {"cmd": 2,"droppedPlayer":{"id":str(c)}}
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()

            #--Format message to json and send to all current clients--#
            m = json.dumps(message)
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
            #-------------------------------------------#

      time.sleep(1/30)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print ("Current clients:",clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1/30)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1/30)

if __name__ == '__main__':
   main()
