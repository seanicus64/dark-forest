#!/usr/bin/env python3
import json
import tkinter as tk
import sys, time, math, random
import threading
import socket
import datetime
import math
from functools import partial
from datetime import date
from tkinter import tix, ttk
from PIL import ImageTk, Image, ImageDraw
#random.seed(0)
class Planet:
    def __init__(self, game, x, y, radius, name, color, planet_id, is_star, parent):
        self.game = game
        self.x, self.y = x, y
        self.radius = radius
        self.name = name
        self.color = color
        self.planet_id = planet_id
        self.is_star = is_star
        self.parent = parent
        self.ships = {"passenger": random.randrange(10), "war": random.randrange(10), "container": random.randrange(10)}
        self.engines = {"gen1": random.randrange(40), "gen2": random.randrange(100), "gen3": random.randrange(4)}
    def get_parent(self):
        parent = None
        for p in self.game.planets:
            if p.planet_id == self.parent:
                return p
        return parent
    def __str__(self):
        return self.name
class Ship:
    engine_speeds = {"gen1": 100000, "gen2": 1000000}
    def __init__(self, source, dest, source_x, source_y, dest_x, dest_y, game, engine_type):
        self.source = source
        self.dest = dest
        self.source_x, self.source_y = source_x, source_y
        self.dest_x, self.dest_y = dest_x, dest_y
        self.x, self.y = source_x, source_y
        
        self.game = game
        self.engine_type = engine_type
        self.speed = self.engine_speeds[self.engine_type]
        
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
            self.game.canvas.delete(self.game.canvas.shipment_ids[self][2])
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
        self.game.canvas.delete(self.line)
        self.shipment_obj = self.game.canvas.shipment_ids[self][2]
        self.game.canvas.delete(self.shipment_obj)
        
        self.line = self.game.canvas.create_shipment_line(self)

class Shipment_Form(tk.Toplevel):
    def __init__(self, master, game):
        super().__init__(master)
        self.game = game
        planets = self.game.planets.copy()
        self.title("Shipment form")
        self.geometry("400x400")
        self.source_combo = ttk.Combobox(self, values=planets)
        self.dest_combo = ttk.Combobox(self, values=planets)
        self.dest_combo.configure(state="disabled")
        self.source_combo.grid()
        self.canvas = SpaceCanvas(self)
        self.dest_combo.grid()
        self.source_combo.bind("<<ComboboxSelected>>", self._make_form)
        self.dependent = tk.Frame(self)
        self.dependent.grid()

    def _make_form(self, event):
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
        dest_name = self.dest_combo.get()
        self.dest_planet = self.game.get_planet_by_name(dest_name)
        source, dest = self.source_planet, self.dest_planet
        print(f"engine type: {self.engine_var.get()}")
        self.engine_type = self.engine_var.get()
        if not self.engine_type:
            self.engine_type = "gen1"
        self.ship = Ship(source, dest, self.source_planet.x, self.source_planet.y, self.dest_planet.x, self.dest_planet.y, self.game, self.engine_type)
    #def __init__(self, source, dest, source_x, source_y, dest_x, dest_y, game, speed=2):
        self.ship["passengers"] = self.passengers.get()
        planned_route = self.game.canvas.create_planned_line(self.ship)
#        planned_route = self.game.canvas.create_line(self.source_planet.x, self.source_planet.y, self.dest_planet.x, self.dest_planet.y, fill="green", width=1)
        self.game.canvas.shipment_ids[self.ship] = [planned_route, None, None]
        

    def send_shipment(self, event):
        self.prepare_shipment()
        source = self.source_planet.planet_id
        dest = self.dest_planet.planet_id
        message_dict = {"MESSAGE_TYPE": "SHIP", "SOURCE": source, "DESTINATION": dest, "ENGINE_TYPE": self.engine_type, "MANIFEST": {"crystals": [],"passengers": 0}}
        message = json.dumps(message_dict) + "\r\n"
        message = bytes(message.encode("utf-8"))
        self.game.socket.send(message)
        self.game.register_ship(self, self.ship)

class PlanetFrame(tk.Frame):
    def __init__(self, game):
        self.root = game.root
        self.game = game
        super().__init__(self.root)
        self.current_planet = tk.StringVar()
        self.current_planet.set("earth")
        self.label = tk.Label(self, textvariable=self.current_planet)
        self.label.pack(side="left")
        #self.slider = tk.Frame(self)
        #self.temp = tk.StringVar()
        #self.temp.set("This is the slider label")
        #self.slider_label = tk.Label(self.slider, textvariable=self.temp)
        #self.slider.pack(side="top")
        #self.slider_label.pack(side="left")
        #self.zoom_combo = ttk.Combobox(self.slider, values=list(range(-30, 30)), height=40, width=3)
        #self.zoom_combo.pack(side="left")
        #self.zoom_buttons = {}
        self.zoom_canvas = tk.Canvas(self.root)
        self.zoom_canvas.config(width=70, height=self.game.canvas.phys_height, bg="black")
        self.zoom_canvas.pack(side="right")
        self.zoom_canvas.create_line(30, 0, 30, self.game.canvas.phys_height, fill="white", width=4)
        self.zoom_canvas.bind("<Button-1>", self.clicked_zoom_canvas)
        for i in range(-30, 30, 1):
            y = (i+30)*(self.game.canvas.phys_height/60)
            y_min = int((i+29.5)*(self.game.canvas.phys_height/60))
            y_max = int((i+30.5)*(self.game.canvas.phys_height/60))
            self.zoom_canvas.create_line(25, y, 35, y, fill="green", width=3)
            self.zoom_canvas.create_text(45, y, text=f"{i}", fill="white")
            if i == self.game.canvas.zoom_level:
                self.current_zoom_indicator = self.zoom_canvas.create_oval(5, y-5, 15, y+5, fill="blue")
            #rect = self.zoom_canvas.create_rectangle(0, y_min, 70, y_max, fill="")
            
            #self.tag_bind(planet_cvsid, "<ButtonPress-1>", self.onObjectClick)
            #self.zoom_canvas.tag_bind(rect, "<ButtonPress-1>", self.clicked_zoom_canvas)
            command = partial(self.zoom, i)
            print(id(command))
            #button = tk.Button(self, text=str(i), command=command)
            #button.pack(side="top")
            #self.zoom_buttons[i] = button
    def zoom(self, amount):
        print(self.game)
        print(self.game.canvas)
        print(amount)
        self.game.canvas.zoom_level = amount
        self.game.canvas.redraw()
    def clicked_zoom_canvas(self, event):
        pass
        y = event.y
        x = event.x
        zoom = round((y/(self.game.canvas.phys_height/60))-30)
        
       # self.zoom_canvas.move(self.current_zoom_indicator, 5, round((zoom+30)*(self.game.canvas.phys_height/60)))
        print(self.current_zoom_indicator, 5, round(y))
        self.zoom_canvas.move(self.current_zoom_indicator, x, y)
        self.game.canvas.zoom_level = zoom
        self.game.canvas.redraw()
        print(zoom)
        #self.canvas.bind("<Button-1>", self.clicked_canvas)
    #def onObjectClick(self, event):
    #    which_object = event.widget.find_closest(event.x, event.y)
class SpaceCanvas(tk.Canvas):
    def __init__(self, game):
        self.game = game
        self.root = self.game.root
        super().__init__(self.root, bg="black", height=1000, width=1000)
        self.space_image = tk.PhotoImage(file="space2.ppm")
        self.zoom_factor = 2
        self.zoom_level = -2

        # the center x, y coordinates as they relate to the overall galaxy map
        self.x = 1000000
        self.y = 1000000
        self.phys_width = 1000
        self.phys_height = 1000
        
        # how many millionths of an au
        self.virt_width = self.phys_width * 2**self.zoom_level * 1000000
        self.virt_height = self.phys_height * 2**self.zoom_level * 1000000

        self.config(width=self.phys_width, height=self.phys_height)
        self.canvas_ids = {}
        self.shipment_ids = {}
        self.redraw()
        self.phys_planet_locations = {}
        self.last_click = None

    def redraw(self):
        self.delete("all")
        self.virt_width = self.phys_width * self.zoom_factor ** self.zoom_level * 1000000
        self.virt_height = self.phys_height * self.zoom_factor ** self.zoom_level * 1000000
        self.create_image(0, 0, image=self.space_image, anchor=tk.NW)
        up = tk.Button(self.root, text="up", command=self.move_up)
        down = tk.Button(self.root, text="down", command=self.move_down)
        left = tk.Button(self.root, text="left", command=self.move_left)
        right = tk.Button(self.root, text="right", command=self.move_right)
        zoomout = tk.Button(self.root, text="zoom out", command=self.zoom_out)
        zoomin = tk.Button(self.root, text="zoom in", command=self.zoom_in)
        button_up_window = self.create_window(40, 110, anchor=tk.NW, window=up)
        button_down_window = self.create_window(40, 150, anchor=tk.NW, window=down)
        button_left_window = self.create_window(10, 130, anchor=tk.NW, window=left)
        button_right_window = self.create_window(70, 130, anchor=tk.NW, window=right)
        button_zoomout_window = self.create_window(10, 200, anchor=tk.NW, window=zoomout)
        button_zoomin_window = self.create_window(10, 220, anchor=tk.NW, window=zoomin)
        
        text = f"{self.x},{self.y}   zoom:{self.zoom_level}"
#        name_cvsid = self.create_text(xl, yl, text=planet.name, fill="white", tag=f"{planet.name}_label")
        self.create_text(100, 10, text=text, fill="white")
        for shipment in self.shipment_ids.keys():
            self.delete(self.shipment_ids[shipment][0])
            self.delete(self.shipment_ids[shipment][1])
            self.delete(self.shipment_ids[shipment][2])
            
            planned_obj = self.create_planned_line(shipment)
            line_obj = self.create_shipment_line(shipment)
            self.shipment_ids[shipment] = [planned_obj, line_obj, None]

        for p in self.game.planets:
            if not (p.is_star or self.zoom_level <= -1): 
                continue
            x, y = self.virt_to_phys(p.x, p.y)
            planet_cvsid = None
            name_cvsid = None
            orbit_cvsid = self.draw_orbit(p)
            if 0 <= x < self.phys_width and 0 <= y < self.phys_height:
                planet_cvsid, name_cvsid = self.draw_planet(p)
            
            if any((planet_cvsid, name_cvsid, orbit_cvsid)):
                self.canvas_ids[p] = (planet_cvsid, name_cvsid, orbit_cvsid)
            if name_cvsid:
                self.tag_bind(planet_cvsid, "<ButtonPress-1>", self.onObjectClick)
                self.tag_bind(name_cvsid, "<ButtonPress-1>", self.onObjectClick)
    
    def draw_orbit(self, planet):
        draw_orbit = False
        orbit_cvsid = None
        parent = planet.get_parent()
        x_coord, y_coord = self.virt_to_phys(planet.x, planet.y)
        draw_orbit = False
        if parent:
            x, y = self.virt_to_phys(parent.x, parent.y)
            distance = self.game.find_distance(x, y, x_coord, y_coord)
            circle_distance_x = abs(x-self.phys_width/2)
            circle_distance_y = abs(y-self.phys_height/2)
            status = ""
            if circle_distance_x > (self.phys_width/2) + distance: 
                draw_orbit = False
                status += "a"
                
            if circle_distance_y > (self.phys_height/2) + distance: 
                draw_orbit = False
                status += "b"

            if (circle_distance_x <= self.phys_width/2): 
                draw_orbit = True
                status += "c"
            if (circle_distance_y <= self.phys_height/2): 
                draw_orbit = True
                status += "d"
            current_distance_sq = (circle_distance_x - self.phys_width/2)**2 +\
                    (circle_distance_y - self.phys_height/2)**2
            if current_distance_sq <= distance**2:
                draw_orbit = True
                status += "e"

            if planet.name == "earth": print(status)

#           bool intersects(CircleType circle, RectType rect)
#{
#    circleDistance.x = abs(circle.x - rect.x);
#    circleDistance.y = abs(circle.y - rect.y);
#
#    if (circleDistance.x > (rect.width/2 + circle.r)) { return false; }
#    if (circleDistance.y > (rect.height/2 + circle.r)) { return false; }
#
#    if (circleDistance.x <= (rect.width/2)) { return true; } 
#    if (circleDistance.y <= (rect.height/2)) { return true; }
#
#    cornerDistance_sq = (circleDistance.x - rect.width/2)^2 +
#                         (circleDistance.y - rect.height/2)^2;
#
#    return (cornerDistance_sq <= (circle.r^2));
#} 
##            corners = ((x-distance, y-distance), (x-distance, y+distance), (x+distance, y-distance), (x+distance, y+distance))
##            for c in corners:
##                cx, cy = c
##                if all(((0-(self.phys_width/2)<=cx<self.phys_width+(self.phys_width/2)), (0-(self.phys_height/2)<=cy<self.phys_height+(self.phys_height/2)))):
##                    draw_orbit = True
##                    break
            if draw_orbit:
                
                orbit_cvsid = self.create_oval(x - distance, y - distance, x + distance, y + distance, outline="gray", width=1, tag="something")
        return orbit_cvsid
    def virt_to_phys(self, x, y):
        new_x = int((x - self.x) / (self.zoom_factor ** self.zoom_level * 1000000)) + 500
        new_y = int((y - self.y) / (self.zoom_factor ** self.zoom_level * 1000000)) + 500
        return new_x, new_y

    def zoom_out(self):
        self.zoom("out")
    def zoom_in(self):
        self.zoom("in")
    def zoom(self, direction):
        if direction == "in":
            self.zoom_level -= 1
        else:
            self.zoom_level += 1
        self.redraw()
        
    # XXX Not currently being used, may be used in the future
    def move_object(self, xchange=0, ychange=0):
        if xchange < 0:
            self.x += self.virt_width / 5
        if ychange < 0:
            self.y += self.virt_height / 5
        if xchange > 0:
            self.x -= self.virt_width / 5
        if ychange > 0:
            self.y -= self.virt_height / 5
        self.redraw()
        return
        for k, v in self.canvas_ids.items():
            planet = k
            planet_obj, name_obj, orbit_obj= v
            self.move(planet.name, xchange, ychange)
            self.move(f"{planet.name}_label", xchange, ychange)
        for k, v in self.shipment_ids.items():
            shipment = k
            planned_obj, line_obj, ship_obj = v
            self.move(planned_obj, xchange, ychange)
            self.move(line_obj, xchange, ychange)
            self.move(ship_obj, xchange, ychange)

    def move_left(self):
        self.move_object(+200, 0)
    def move_right(self):
        self.move_object(-200, 0)
    def move_up(self):
        self.move_object(0, 200)
    def move_down(self):
        self.move_object(0, -200)
    def create_planned_line(self, shipment):
        source_x, source_y = shipment.source.x, shipment.source.y
        dest_x, dest_y = shipment.dest.x, shipment.dest.y
        phys_source_x, phys_source_y = self.virt_to_phys(source_x, source_y)
        phys_x, phys_y = self.virt_to_phys(dest_x, dest_y)
        planned_route = self.game.canvas.create_line(phys_source_x, phys_source_y, phys_x, phys_y, fill="green", width=1)
        # highest length is about 42.5billion
        # dont go over 10k objects
        return planned_route

    def create_shipment_line(self, shipment):
        source_x, source_y = shipment.source.x, shipment.source.y
        x, y = shipment.x, shipment.y
        phys_source_x, phys_source_y = self.virt_to_phys(source_x, source_y)
        phys_x, phys_y = self.virt_to_phys(x, y)
        line = self.create_line(phys_source_x, phys_source_y, phys_x, phys_y, fill="purple", width=3)
        ship_graphic = self.create_rectangle(phys_x-2, phys_y-2, phys_x+2, phys_y+2, fill="red", outline="black")
        self.shipment_ids[shipment][1] = line
        self.shipment_ids[shipment][2] = ship_graphic
        result = self.virt_to_phys(x, y)
        return line
    

    def phys_to_virt(self, x, y):
        virt_x = (x - 500) * (self.zoom_factor**self.zoom_level*1000000) + self.x
        virt_y = (y - 500) * (self.zoom_factor**self.zoom_level*1000000) + self.y
        return virt_x, virt_y
        
    def onObjectClick(self, event):
        which_object = event.widget.find_closest(event.x, event.y)
        current_time = datetime.datetime.now()
        if self.last_click:
            last_object, last_time = self.last_click
            if last_object == which_object:
                planet_obj_id = event.widget.find_closest(event.x, event.y)[0]
                planet = self.get_planet_from_object_id(planet_obj_id, self.canvas_ids)
                if not planet:
                    return
                difference = current_time - last_time
                if difference <= datetime.timedelta(milliseconds=500):
                    self.x, self.y = planet.x, planet.y
                    self.redraw()
                
        self.last_click = (which_object, current_time)

    @staticmethod
    def get_planet_from_object_id(object_id, canvas_ids_dict):
        print(object_id)
        for k, v in canvas_ids_dict.items():
            planet_obj, name_obj, orbit_obj = v
            if object_id in (name_obj, planet_obj):
                return k
        return None

            
        
    def draw_planet(self, planet):
        x_coord, y_coord = self.virt_to_phys(planet.x, planet.y)
        radius = planet.radius
        x_topleft = planet.x - planet.radius
        y_topleft = planet.y - planet.radius
        x_bottomright = planet.x + planet.radius
        y_bottomright = planet.y + planet.radius
        phys_x_topleft, phys_y_topleft = self.virt_to_phys(x_topleft, y_topleft)
        phys_x_bottomright, phys_y_bottomright = self.virt_to_phys(x_bottomright, y_bottomright)

        # Creates minimum size so we can see at least sea a planet in the system
        # or a star in the galaxy.
        if phys_x_bottomright - phys_x_topleft <= 4:
            planet_coords = self.virt_to_phys(planet.x, planet.y)
            phys_x_topleft, phys_y_topleft  = planet_coords[0] - 2, planet_coords[1] - 2
            phys_x_bottomright, phys_y_bottomright = planet_coords[0] + 2, planet_coords[1] + 2

        xl = x_coord - radius
        yl = y_coord - radius
        xr = x_coord + radius
        yr = y_coord + radius
        planet_cvsid = self.create_oval(phys_x_topleft, phys_y_topleft, phys_x_bottomright, phys_y_bottomright, fill=planet.color, outline="green", tag=planet.name)
        name_cvsid = None
        if self.zoom_level <= 10:
            name_cvsid = self.create_text(xl, yl, text=planet.name, fill="white", tag=f"{planet.name}_label")
        return planet_cvsid, name_cvsid

        name_cvsid = None
        parent = planet.get_parent()
        orbit_cvsid = None
#        if parent:
#            x, y = self.virt_to_phys(parent.x, parent.y)
#            distance = self.game.find_distance(x, y, x_coord, y_coord)
#            orbit_csvid = self.create_oval(x - distance, y - distance, x + distance, y + distance, outline="gray", width=1, tag="something")
            #planet_cvsid = self.create_oval(xl, yl, xr, yr, fill=planet.color, outline="purple", tag=planet.name)
        self.tag_bind(planet_cvsid, "<ButtonPress-1>", self.onObjectClick)
        self.canvas_ids[planet] = (planet_cvsid, name_cvsid, orbit_cvsid)
class Application():
    def __init__(self, socket):
        self.planets = []
        self.socket = socket
        self.root = tk.Tk()
        self.all_ships = []
        #canvas = tk.Canvas(self.root, bg="black", height=1000, width=1000)
        self.canvas = SpaceCanvas(self)
        
        self.planet_frame = PlanetFrame(self)
#        space_image = ImageTk.PhotoImage(Image.open("space.jpg"))
        #print(space_image)
        self.canvas.bind("<Button-1>", self.clicked_canvas)
        #button1_window.pack()
        self.canvas.pack(side="right")
        #self.main_frame = tk.Frame(self)
        self.planet_frame.pack(side="left")
        self.make_shipment_form = tk.Button(self.root, text="Create shipment")
        self.make_shipment_form["command"] = self.create_shipment_form
        self.make_shipment_form.pack(side="top")
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
#        self.root.geometry("900x900")
        self.time = tk.Label(self.root, text="")
        self.time.update()
        self.ship = None
        self.time.pack()
        self.year = 2000
        self.rate = 1
        # each pixel is 10**self.zoom AU. e.g. zoom -2 means a distance of 500 pixels will show 5 au
        # the entire inner solar system plus probably jupiter
        self.zoom_level = -2
        self.update_clock()
        thread = threading.Thread(target=self.receive_loop)
        thread.start()
    def clicked_canvas(self, event):
        pass
#        print(f"Clicked at {event.x} {event.y}")
#        print(self.canvas.phys_to_virt(event.x, event.y))
    def receive_loop(self):
        s = self.socket
        s.connect(("127.0.0.1", 7777))
        data = ""
        while True:
            # handles lines cut off by buffer size
            new_data = str(s.recv(1024).decode("utf-8")).lower()
            data += new_data
            split_data = data.split("\n")
            lines = split_data[:-1]
            data = split_data[-1]

            #lines = str(s.recv(1024).decode("utf-8")).lower().split("\r\n")
            for l in lines: 
                #print(l)
                l = l.strip()
                try:
                    message_dict = json.loads(l)
                except:
                    continue
                message_type = message_dict.get("message_type")
                if message_type == "planet_info":
                    
                    x = message_dict.get("x")
                    y = message_dict.get("y")
                    radius = message_dict.get("radius")
                    name = message_dict.get("name")
                    if name in ["sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]:
                        print(message_dict)
                    color = message_dict.get("color")
                    planet_id = message_dict.get("planet_id")
                    is_star = message_dict.get("is_star")
                    parent = message_dict.get("parent")

                    planet = Planet(self, x, y, radius, name, color, planet_id, is_star, parent)
                    self.planets.append(planet)
                    #self.draw_planet(planet)
                    #self.canvas.draw_planet(planet)

    def draw_canvas(self):
        pass
    def register_ship(self, form, ship):
        del form
        self.all_ships.append(ship)

    def create_shipment_form(self):
        self.shipment_form = Shipment_Form(self.root, self)

        def return_pressed(event):
            pass

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
            
    def find_distance(self, source_x, source_y, dest_x, dest_y):
        distance = math.sqrt((dest_x-source_x)**2+(dest_y-source_y)**2)
        return distance

    def draw_planet(self, planet):
        xl = planet.x - planet.radius
        xr = planet.x + planet.radius
        yl = planet.y - planet.radius
        yr = planet.y + planet.radius
        self.canvas.create_oval(xl, yl, xr, yr, fill=planet.color, outline="black")
        self.canvas.create_text(xl, yl-10, text=planet.name, fill="white")

    def draw_map(self):
        if not self.ship:
            return

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


    def create_widgets(self):
        pass
PORT = 7777
SERVER = "127.0.1.1"

FORMAT = "utf-8"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
app = Application(s)
app.root.mainloop()

