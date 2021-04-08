#!/usr/bin/env python3
import json
import tkinter as tk
import sys, time, math, random
import threading
import socket
import datetime
from datetime import date
from tkinter import tix, ttk
from PIL import ImageTk, Image, ImageDraw
random.seed(0)
class Planet:
    def __init__(self, x, y, radius, name, color, planet_id):
        self.x, self.y = x, y
        self.radius = radius
        self.name = name
        self.color = color
        self.planet_id = planet_id
        self.ships = {"passenger": random.randrange(10), "war": random.randrange(10), "container": random.randrange(10)}
        self.engines = {"gen1": random.randrange(40), "gen2": random.randrange(100), "gen3": random.randrange(4)}
    def __str__(self):
        return self.name
class Ship:
    def __init__(self, source_x, source_y, dest_x, dest_y, game, speed=10):
        self.source_x, self.source_y = source_x, source_y
        self.dest_x, self.dest_y = dest_x, dest_y
        self.x, self.y = source_x, source_y
        
        self.game = game
        self.speed = speed
        self.line = None
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
            self.game.canvas.delete(self.line)
            return True
        #XXX what if the slope is undefined?
        m = (self.dest_y - self.source_y) / (self.dest_x - self.source_x)
        b = -1 * m * self.source_x + self.source_y

        if self.dest_x >= self.source_x:
            delta_x = self.x + self.speed / math.sqrt(1+m**2)
        else:
            delta_x = self.x - self.speed / math.sqrt(1+m**2)
        delta_y = m*delta_x + b
#        print(m, b, delta_x, delta_y)
#        print(f"m:{m} b:{b} delta_x:{delta_x} delta_y:{delta_y}")
        self.x = delta_x
        self.y = delta_y
        print(f"{self.source_x} {self.source_y} - {self.x} {self.y}")

        self.game.canvas.delete(self.line)
        self.line = self.game.canvas.create_line(self.source_x, self.source_y, self.x, self.y, fill="green")
        print(self.x, self.y)
class Shipment_Form(tk.Toplevel):
    def __init__(self, master, game):
        super().__init__(master)
        self.game = game
        planets = self.game.planets.copy()
        print("ALL PLANETS ARE")
        for p in planets:
            print(p)
        self.title("Shipment form")
        self.geometry("400x400")
        self.source_combo = ttk.Combobox(self, values=planets)
        self.dest_combo = ttk.Combobox(self, values=planets)
        self.dest_combo.configure(state="disabled")
        self.source_combo.grid()
        self.dest_combo.grid()
        self.source_combo.bind("<<ComboboxSelected>>", self._make_form)
        self.dependent = tk.Frame(self)
        self.dependent.grid()

    def _make_form(self, event):
        print("hello world!")
        print("hi")
        source_name = self.source_combo.get()
        self.source_planet = self.game.get_planet_by_name(source_name)
        self.dest_combo.configure(state="enabled")
        self.ship_var = tk.StringVar()
        self.engine_var = tk.StringVar()
        for ship, amount in self.source_planet.ships.items():
            if amount == 0:
                continue
            ship_button = tk.Radiobutton(self.dependent, text=f"{ship} ({amount} available)", variable=self.ship_var, value=ship)
            ship_button.grid()
        for engine, amount in self.source_planet.engines.items():
            if amount == 0:
                continue
            engine_button = tk.Radiobutton(self.dependent, text=f"{engine} ({amount} available", variable=self.engine_var, value=engine)
            engine_button.grid()
        self.passengers_variable = tk.IntVar()
        self.passengers = tk.Spinbox(self.dependent, from_=0, to=100)
        self.passengers.grid()
        self.send_button = tk.Button(self.dependent)
        self.send_button.grid()
        self.send_button.bind("<Button>", self.send_shipment)
    
    def prepare_shipment(self):
        print("PREPARE SHIPMENT RUNNING")
        dest_name = self.dest_combo.get()
        self.dest_planet = self.game.get_planet_by_name(dest_name)
        print("s: {} d: {} p: {} sv: {} ev: {}".format(self.source_planet, self.dest_planet, self.passengers.get(), self.ship_var.get(), self.engine_var.get()) )
        self.ship = Ship(self.source_planet.x, self.source_planet.y, self.dest_planet.x, self.dest_planet.y, self.game, 10)
        self.ship["passengers"] = self.passengers.get()
        print(self.source_planet, self.dest_planet)

    def send_shipment(self, event):
        print("SEND SHIPMENT RUNNING")
        print("YYYYYYYYYYYYYYYYY")
        try:
            self.game.socket.send(bytes("banana\r\n".encode("utf-8")))
        except:
            print("IT DIDNT WORK")
        self.prepare_shipment()
        self.game.socket.send(bytes("hello world\r\n".encode("utf-8")))
        source = self.source_planet.planet_id
        dest = self.dest_planet.planet_id

        message_dict = {"MESSAGE_TYPE": "SHIP", "SOURCE": source, "DESTINATION": dest, "MANIFEST": {"crystals": [],"passengers": 0}}
        message = json.dumps(message_dict) + "\r\n"
        message = bytes(message.encode("utf-8"))
        print(f"KKKKKKKKKKKK message: {message}")
        self.game.socket.send(message)
        self.game.register_ship(self, self.ship)
#        self.game.socket.send(b"hello world")
class PlanetFrame(tk.Frame):
    def __init__(self, game):
        self.root = game.root
        self.game = game
        super().__init__(self.root)
        self.current_planet = tk.StringVar()
        self.current_planet.set("banana")
        #self.label = tk.Label(self, text="hello world")
        self.label = tk.Label(self, textvariable=self.current_planet)
        self.label.pack(side="left")
        #self.current_planet.pack()
    


        
class Application():
    def __init__(self, socket):
        self.planets = []
        self.socket = socket
        self.root = tk.Tk()
#        self.left = tk.Frame(self.root)
#        self.left.pack(side="left")
        self.all_ships = []
#        button = tk.Button(self.left, text="hello world")
#        button.pack(side="top")
#        e1 = tk.Entry(self.left)
#        e1.pack(side="top")
        canvas = tk.Canvas(self.root, bg="black", height=1000, width=1000)
        self.canvas = canvas
#        amount = random.randrange(5, 30)
#        self.planets = []
#        for i in range(amount):
#            radius = random.randrange(2, 20)
#            x = random.randrange(1000)
#            y = random.randrange(1000)
#            name = ""
#            size = random.randrange(4, 10)
#            for _ in range(size):
#                letter = random.choice("abcdefghijklmnopqrstuvwxyz")
#                name += letter
#            color = random.choice(["red", "blue", "purple", "yellow", "orange", "white"])
#            planet = Planet(x, y, radius, name, color)
#            self.planets.append(planet)
#            self.draw_planet(planet)
        
        canvas.pack(side="right")
#        n = tk.StringVar()
#        self.checkbox = tk.Checkbutton(self.left, text="interstellar?")
#        self.checkbox.pack(side="top")
#        combo = ttk.Combobox(self.left, width=27, values=self.planets)
#        self.combo = combo
#        self.combo.current(1)
#        combo.pack(side="top")
#        self.combo2 = ttk.Combobox(self.left, width=27, values=self.planets)
#        self.combo2.pack(side="top")
        self.planet_frame = PlanetFrame(self)
        self.planet_frame.pack(side="left")
        self.make_shipment_form = tk.Button(self.root, text="Create shipment")
        self.make_shipment_form["command"] = self.create_shipment_form
        self.make_shipment_form.pack(side="top")

        self.root.geometry("900x900")
        self.time = tk.Label(self.root, text="")
        self.time.update()
        self.ship = None
        self.time.pack()
        self.year = 2000
        self.rate = 1
        self.update_clock()
        thread = threading.Thread(target=self.receive_loop)
        thread.start()
    def receive_loop(self):
        pass
        s = self.socket
        s.connect(("127.0.0.1", 7777))
        while True:
            print(self.planets)
            lines = str(s.recv(1024).decode("utf-8")).lower().split("\r\n")
            for l in lines: 
                print(l)
                l = l.strip()
                try:
                    message_dict = json.loads(l)
                except:
                    continue
                print(message_dict)
                message_type = message_dict.get("message_type")
                if message_type == "planet_info":
                    print("PLANET INFO")
                    x = message_dict.get("x")
                    y = message_dict.get("y")
                    radius = message_dict.get("radius")
                    name = message_dict.get("name")
                    color = message_dict.get("color")
                    planet_id = message_dict.get("planet_id")

                    planet = Planet(x, y, radius, name, color, planet_id)
                    self.planets.append(planet)
                    self.draw_planet(planet)
#                    print(self.planets)
    #def __init__(self, x, y, radius, name, color):
            
            

        #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #    s.connect((SERVER, PORT))
        #    s.sendall(b"hello world")
        #    while True:
        #        data = s.recv(1024)
        #sys.exit()
    def register_ship(self, form, ship):
        del form
        self.all_ships.append(ship)
    def create_shipment_form(self):
        self.shipment_form = Shipment_Form(self.root, self)
        def activate_widgets1(event):
            if self._source_planet:
            #XXX yeah don't know why it doesn't recognize source_planet in this scope
                for b in self._buttons:
                    b.pack_forget()

            source_planet_name = source_combo.get()
            source_planet = self.get_planet_by_name(source_planet_name)
            if not source_planet: return 
            dest_combo.bind("<<ComboboxSelected>>", activate_widgets2)
            buttons = []
            self._buttons = buttons
            dest_combo["state"] = "enabled"
            ship_var = tk.StringVar()
            engine_var = tk.StringVar()
            for ship, amount in source_planet.ships.items():
                if amount == 0:
                    continue
                ship_button = tk.Radiobutton(ship_type_left_frame, text=f"{ship} ({amount} available)", variable=ship_var, value=ship)
                ship_button.pack()
                buttons.append(ship_button)
            for engine, amount in source_planet.engines.items():
                if amount == 0:
                    continue
                engine_button = tk.Radiobutton(ship_type_right_frame, text=f"{engine} ({amount} available)", variable=engine_var, value=engine)
                buttons.append(engine_button)
                engine_button.pack()
            
        def activate_widgets2(event):
            dest_planet_name = dest_combo.get()
            dest_planet = self.get_planet_by_name(dest_planet_name)
            button = tk.Button(self.shipment_form, text="Send shipment", command=lambda:self.launch_ship(self._source, dest_planet))
            button.pack()
        def return_pressed(event):
            print("return pressed")
        def make_form(event):
            #TODO: cleanup previous
            dependent = self.shipment_form.dependent
            for slave in dependent.grid_slaves():
                slave.grid_remove()
            source_planet_name = source_combo.get()
            source_planet = self.get_planet_by_name(source_planet_name)
            name_label = tk.Label(self.shipment_form.dependent, text = source_planet_name)
            name_label.grid()
            dest_combo.configure(state="enabled")
            ship_var = tk.StringVar(name="ship")
            engine_var = tk.StringVar(name="engine")
            for ship, amount in source_planet.ships.items():
                if amount == 0:
                    continue
                ship_button = tk.Radiobutton(dependent, text=f"{ship} ({amount} availabile)", variable=ship_var, value=ship)
                ship_button.grid()
            for engine, amount in source_planet.engines.items():
                if amount == 0:
                    continue
                engine_button = tk.Radiobutton(dependent, text=f"{engine} ({amount} available)", variable=engine_var, value=engine)
                engine_button.grid()
            passenger_variable = tk.IntVar()
            passengers = tk.Spinbox(dependent, from_=0, to=100, name="passengers")
            passengers.grid()
            send_button = tk.Button(dependent)
            send_button.grid()
            self._working_shipment = dependent
            send_button.bind("<Button>", send_shipment)

        def send_shipment(event):
            ship_form = self._working_shipment
            ship_type = ship_form.getvar(name="ship")
            engine_type = ship_form.getvar(name="engine")
            for a in ship_form.grid_slaves():
                print(a)
            print("SENDING SHIPMENT")
            
    def find_distance(self, source_x, source_y, dest_x, dest_y):
        distance = math.sqrt((dest_x-source_x)**2+(dest_y-source_y)**2)
        return distance
    def draw_planet(self, planet):
        xl = planet.x - planet.radius
        xr = planet.x + planet.radius
        yl = planet.y - planet.radius
        yr = planet.y + planet.radius
        print("------------")
        print(xl, yl, xr, yr)

        self.canvas.create_oval(xl, yl, xr, yr, fill=planet.color)
        self.canvas.create_text(xl, yl-10, text=planet.name, fill="white")
    def draw_map(self):
        if not self.ship:
            return
        pass
    def update_clock(self):
        self.year += self.rate
        self.time.configure(text=str(self.year))
        landed = False
        to_be_removed = []
        for ship in self.all_ships:
            landed = ship.update()
            if landed:
                to_be_removed.append(ship)
        for ship in to_be_removed:
            self.all_ships.remove(ship)
            del ship
        self.root.after(1000, self.update_clock)

    def get_planet_by_name(self, name):
        for p in self.planets:
            if p.name == name:
                return p
        return None
    def launch_ship(self, source, dest):
        source_x, source_y = source.x, source.y
        dest_x, dest_y = dest.x, dest.y
        self.ship = Ship(source_x, source_y, dest_x, dest_y, 1)
        self.ship.game = self
    def create_widgets(self):
        pass
PORT = 7777
#SERVER = socket.gethostbyname(socket.gethostname())
SERVER = "127.0.1.1"

FORMAT = "utf-8"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#    s.connect((SERVER, PORT))
#    s.sendall(b"hello world")
#    while True:
#        data = s.recv(1024)
#sys.exit()
app = Application(s)
app.root.mainloop()
