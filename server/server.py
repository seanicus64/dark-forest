#!/usr/bin/env python3
import random
import json
import builtins
import math
import time
import datetime

from twisted.internet import protocol, reactor, endpoints, task, defer
from twisted.protocols import basic
#random.seed(0)
class Planet:
    def __init__(self, x, y, radius, name, color, is_star=False, parent=None):
        self.x, self.y = x, y
        self.radius = radius
        self.name = name
        self.color = color
        self.is_star = is_star
        self.ships = {"passenger": random.randrange(10), "war": random.randrange(10), "container": random.randrange(10)}
        self.engines = {"gen1": random.randrange(40), "gen2": random.randrange(100), "gen3": random.randrange(4)}
        self.owner = None
        self.parent = parent
    def change_owner(self, owner):
        self.owner = owner
        owner.planets_owned.append(self)
    def __str__(self):
        return self.name
class Ship:
    def __init__(self, factory, source, dest):
        self.factory = factory
        self.source = source
        self.dest = dest
        self.x = source.x
        self.y = source.y
        self.speed = 10
        self.manifest = {
            "passengers": 0,
            "cystals": [],
            }
    def __setitem__(self, name, value): 
        self.manifest[name] = value
    def __getitem__(self, name):
        return self.manifest[name]
        if name in self.manifest:
            return self.manifest[name]
        
    def update(self):
        total_distance = self.game.find_distance(self.source_x, self.source_y, self.dest_x, self.dest_y)
        so_far_distance = self.game.find_distance(self.source_x, self.source_y, self.x, self.y)
        if so_far_distance >= total_distance:
            return True
        #XXX what if the slope is undefined?
        m = (self.dest_y - self.source_y) / (self.dest_x - self.source_x)
        b = -1 * m * self.source_x + self.source_y

        if self.dest_x >= self.source_x:
            delta_x = self.x + self.speed / math.sqrt(1+m**2)
        else:
            delta_x = self.x - self.speed / math.sqrt(1+m**2)
        delta_y = m*delta_x + b
        self.x = delta_x
        self.y = delta_y

class Player(object):
    def __init__(self, protocol):
        self.protocol = protocol
        self.planets_owned = []

class GalaxyProtocol(basic.LineReceiver):
    def connectionMade(self):
        self.transport.write(b"you've made a connection\r\n")
        self.player = self.factory.add_player(self)
        planets_owned = [p.planet_id for p in self.player.planets_owned]
        constructed_json = {"MESSAGE_TYPE": "PLANETS_OWNED_INFO", "planets": planets_owned, "PLAYER": self.player.uid}
        json_payload = bytes(json.dumps(constructed_json).encode("utf-8"))
        self.transport.write(json_payload + "\r\n".encode("utf-8"))
        for p in self.factory.planets:
            p.change_owner(self.player)
            self.send_planet(p, self.player)

    def send_planet(self, planet, player):
        print(f"planet.is_star: {planet.is_star}")
        message_dict = {"MESSAGE_TYPE": "PLANET_INFO", "x": planet.x, "y": planet.y, "radius": planet.radius, "color": planet.color, "owner": planet.owner.uid, "name": planet.name, "planet_id": planet.planet_id, "is_star": planet.is_star, "parent": planet.parent.planet_id if planet.parent else None}
        message = bytes((json.dumps(message_dict) + "\r\n").encode("utf-8"))
        player.protocol.sendLine(message)

    def lineReceived(self, line):
        print(line)
        try:
            line = line.decode("utf-8").strip().lower()
        except builtins.UnicodeDecodeError:
            print("error")
            return
        self.transport.write(f"Received line: {line}\r\n".encode("utf-8"))
        if line.strip().lower() == "quit":
            self.quit()
        try:
            message = json.loads(line)
            message_type = message.get("message_type")
            if message_type == "ship":
                source_id = message["source"]
                dest_id = message["destination"]
                source = self.factory.planet_ids[source_id]
                dest = self.factory.planet_ids[dest_id]
                manifest = message["manifest"]
                d, ship = self.factory.try_send_shipment(source=source, dest=dest, ship_type="passenger", engine_type="gen3", manifest=manifest)
                d.addCallback(self.factory.send_arrival_message, ship)

        except json.decoder.JSONDecodeError as err:
            print(err)
        
    def quit(self):
        self.transport.loseConnection()

class GalaxyFactory(protocol.ServerFactory):
    def __init__(self):
        for i in range(100):
            print(f"solar system #{i}")
            self.create_solar_system()
    protocol = GalaxyProtocol
    players = []
    planets = []
    amount = random.randrange(5, 30)
    uids = {}
    planet_ids = {}
    p_id = 0
    amount = 9 
    distances = [0, 40, 70, 100, 150, 520, 950, 1920, 3000]
    names = ["sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
    star = None
    for i in range(amount):
        radius = random.randrange(2, 20)
        radius = 5
        x = random.randrange(1000)
        y = random.randrange(1000)
        y = 500
        x = distances[i] + 500
        y = 500 - distances[i]
        if i == 0:
            y = 0
            x = 0
        else:

            y = int(random.randrange(-1* distances[i], distances[i]))
            r = distances[i]
            x = int(math.sqrt(r**2 - y**2))
            left = random.choice([True, False])
            if left:
                x *= -1
        x += 1000000
        y += 1000000
        name = ""
    
        size = random.randrange(4, 10)
        for _ in range(size):
            letter = random.choice("abcdefghijklmnopqrstuvwxyz")
            name += letter
        name = names[i]
        color = random.choice(["red", "blue", "purple", "yellow", "orange", "white"])
        is_star = False
        if i == 0:
            is_star = True
        planet = Planet(x, y, radius, name, color, is_star, star)
        if i == 0:
            star = planet
        planet.planet_id = p_id
        planet_ids[p_id] = planet
        p_id += 1
        planets.append(planet)

    def create_solar_system(self):
        amount = random.randrange(3, 12)
        distances = [0]
        for i in range(amount-1):
            number = random.randrange(100, 4000)
            print(number)
            distances.append(number)
#        distances = [0] + [lambda x: random.randrange(4000) for x in range(amount-1)]
        names = ["star"] + ["a" for i in range(amount-1)]
        star_x = random.randrange(1000000000000)
        star_y = random.randrange(1000000000000)
        star = None
        for i in range(amount):
            print(i)
            radius = 5
            if i == 0:
                x, y = 0, 0
                
            else:
                try:
                    y = int(random.randrange(-1*distances[i], distances[i]))
                except:
                    print("banana", distances[i])
                    raise
                r = distances[i]
                x = int(math.sqrt(r**2 - y**2))
                left = random.choice([True, False])
                if left:
                    x *= -1
            x += star_x
            y += star_y
            name = ""
            size = random.randrange(4, 10)
            for _ in range(size):
                letter = random.choice("abcdefghijklmnopqrstuvwxyz")
                name += letter
            color = random.choice(["red", "blue", "purple", "yellow", "orange", "white"])
            is_star = False
            if i == 0:
                is_star = True
               
            
            planet = Planet(x, y, radius, name, color, is_star, star)
            if i == 0:
                star = planet
            print(f"{i}: planet.is_star: {planet.is_star}")
            planet.planet_id = self.p_id
            self.planet_ids[self.p_id] = planet
            self.p_id += 1
            self.planets.append(planet)
#    amount = 9 
#    distances = [0, 40, 70, 100, 150, 520, 950, 1920, 3000]
#    names = ["sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
#    for i in range(amount):
#        radius = random.randrange(2, 20)
#        radius = 5
#        x = random.randrange(1000)
#        y = random.randrange(1000)
#        y = 500
#        x = distances[i] + 500
#        y = 500 - distances[i]
#        if i == 0:
#            y = 0
#            x = 0
#        else:
#
#            y = int(random.randrange(-1* distances[i], distances[i]))
#            r = distances[i]
#            x = int(math.sqrt(r**2 - y**2))
#            left = random.choice([True, False])
#            if left:
#                x *= -1
#        x += 1000000
#        y += 1000000
#        name = ""
#    
#        size = random.randrange(4, 10)
#        for _ in range(size):
#            letter = random.choice("abcdefghijklmnopqrstuvwxyz")
#            name += letter
#        name = names[i]
#        color = random.choice(["red", "blue", "purple", "yellow", "orange", "white"])
#        planet = Planet(x, y, radius, name, color)
#        planet.planet_id = p_id
#        planet_ids[p_id] = planet
#        p_id += 1
#        planets.append(planet)
        
    def send_arrival_message(self, deferred, ship):
        owner = ship.dest.owner
        message_dict = {"MESSAGE_TYPE": "ARRIVAL", "FROM": 2, "MANIFEST": ship.manifest}
        message = json.dumps(message_dict)
        owner.protocol.sendLine(bytes("hello world!!!".encode("utf-8")))
        owner.protocol.sendLine(bytes(message.encode("utf-8")))

    def try_send_shipment(self, source, dest, ship_type, engine_type, manifest):
        def runEverySecond(ship):
                source = ship.source
                dest = ship.dest
                total_distance = self.find_distance(source.x, source.y, dest.x, dest.y)
                so_far_distance = self.find_distance(source.x, source.y, ship.x, ship.y)
                if so_far_distance >= total_distance:
                    loop.stop()
                    return True

                m = (dest.y - source.y) / (dest.x - source.x)
                b = -1 * m * source.x + source.y
                if dest.x >= source.x:
                    delta_x = ship.x + ship.speed / math.sqrt(1+m**2)
                else:
                    delta_x = self.x - ship.speed / math.sqrt(1+m**2)
                delta_y = m * delta_x + b
                ship.x = delta_x
                ship.y = delta_y
        ship = Ship(self, source, dest)
        loop = task.LoopingCall(runEverySecond, ship)
        loop.i = 0
        loopDeferred = loop.start(1, now=True)
        return loopDeferred, ship

    def find_distance(self, source_x, source_y, dest_x, dest_y):
        distance = math.sqrt((dest_x-source_x)**2+(dest_y-source_y)**2)
        return distance
        
    def add_player(self, protocol):
        player = Player(protocol)
        self.players.append(player)
        self.planets[0].change_owner(player)
        max_uid = max([0]+list(self.uids.keys()))
        player.uid = max_uid + 1
        self.uids[player.uid] = player
        return player
        
galaxyEndpoint = endpoints.serverFromString(reactor, "tcp:7777")
galaxyEndpoint.listen(GalaxyFactory())
reactor.run()
        

