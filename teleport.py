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
    def __init__(self, source, dest, source_x, source_y, dest_x, dest_y, game, speed=2):
        self.source = source
        self.dest = dest
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
#        print(f"deleting canvas object {self.line}")
        self.game.canvas.delete(self.line)
        self.shipment_obj = self.game.canvas.shipment_ids[self][2]
        self.game.canvas.delete(self.shipment_obj)
        
        self.line = self.game.canvas.create_shipment_line(self)
        #self.game.canvas.delete(self.line)
        #planned_line = self.game.canvas.create_line(self.source_x, self.source_y, self.dest_x, self.dest_y, fill="green", width=1)
        #self.line = self.game.canvas.create_line(self.source_x, self.source_y, self.x, self.y, fill="green", width=3)
        #self.line = self.game.canvas.create_line(self.source_x, self.source_y, self.dest_x, self.dest_y, fill="green", width=1)
#        print(f"source_x: {self.source_x}  source_y: {self.source_y}  dest_x: {self.dest_x}  dest_y: {self.dest_y}  self.x: {self.x}  self.y: {self.y}")
#        self.game.canvas.shipment_ids[self] = self.line, planned_line

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
        self.ship = Ship(source, dest, self.source_planet.x, self.source_planet.y, self.dest_planet.x, self.dest_planet.y, self.game, 5)
        self.ship["passengers"] = self.passengers.get()
        planned_route = self.game.canvas.create_planned_line(self.ship)
#        planned_route = self.game.canvas.create_line(self.source_planet.x, self.source_planet.y, self.dest_planet.x, self.dest_planet.y, fill="green", width=1)
        self.game.canvas.shipment_ids[self.ship] = [planned_route, None, None]
        

    def send_shipment(self, event):
        self.prepare_shipment()
        source = self.source_planet.planet_id
        dest = self.dest_planet.planet_id
        message_dict = {"MESSAGE_TYPE": "SHIP", "SOURCE": source, "DESTINATION": dest, "MANIFEST": {"crystals": [],"passengers": 0}}
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
        self.current_planet.set("banana")
        self.label = tk.Label(self, textvariable=self.current_planet)
        self.label.pack(side="left")
class SpaceCanvas(tk.Canvas):
    def __init__(self, game):
        self.game = game
        self.root = self.game.root
        super().__init__(self.root, bg="black", height=1000, width=1000)
        self.space_image = tk.PhotoImage(file="space2.ppm")
        self.zoom_factor = 2
        self.zoom_level = -2
        # the top left coordinates as they relate to the overall galaxy map
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
#        self.geometry(f"{self.width}x{self.height}")
        self.phys_planet_locations = {}
        self.last_click = None
    def redraw(self):
        if hasattr(self, "a"):
            self.delete(self.a)
        if hasattr(self, "b"):
            self.delete(self.b)
        if hasattr(self, "c"):
            self.delete(self.c)
        #self.zoom += 1
        #print(dir(self))
        #print(self.find_all())
        #for i in self.find_all():
        #    print(i)
        #    print(type(i))
        #    print(self.coords(i))

        self.delete("all")
        self.virt_width = self.phys_width * self.zoom_factor ** self.zoom_level * 1000000
        self.virt_height = self.phys_height * self.zoom_factor ** self.zoom_level * 1000000


            
#        self.x += 100

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
        #button1_window = self.create_window(10, 10, anchor=tk.NW, window=button1)
#        print("============")
#        print(f"virt_width: {self.virt_width}, virt_height: {self.virt_height}")
#        print(self.shipment_ids)
        for shipment in self.shipment_ids.keys():
#            print("deleting shipment values")
            self.delete(self.shipment_ids[shipment][0])
            self.delete(self.shipment_ids[shipment][1])
            self.delete(self.shipment_ids[shipment][2])
            
        #for shipment, v in self.shipment_ids.items():
            planned_obj = self.create_planned_line(shipment)
            line_obj = self.create_shipment_line(shipment)
            #planned_obj, line_obj, ship_obj = v
#            print(f"planned: {planned_obj}")
#            print(f"line_obj: {line_obj}")
            self.shipment_ids[shipment] = [planned_obj, line_obj, None]
        planet_dict = {"yes": 0, "no": 0}
        for p in self.game.planets:
            if not (p.is_star or self.zoom_level <= -13): 
                planet_dict["no"] += 1
                continue
        
            
            
            x, y = self.virt_to_phys(p.x, p.y)
            #x, y = 0, 0
            #print(x, y)
           
            if 0 <= x < self.phys_width and 0 <= y < self.phys_height:
                planet_dict["yes"] += 1
#                print("this subfunction runs")
#                print(p.is_star)
#                print(self.zoom_level)
                self.draw_planet(p)
#                if p.is_star or self.zoom_level <= -13:
 #                   self.draw_planet(p)
#            if 0 <= x < self.phys_width and 0 <= y < self.phys_height and self.zoom_level <= -13:
#                print("it has run")
                
#                self.draw_planet(p)
            else:
                planet_dict["no"] += 1
        print(f"yes: {planet_dict['yes']}\tno: {planet_dict['no']}")
#        name_cvsid = self.create_text(xl, yl-10, text=planet.name, fill="white", tag=f"{planet.name}_label")
        self.a = self.create_text(self.x, self.y, text=f"{int(self.x)},{int(self.y)}", fill="white")
        self.b = self.create_text(80, 20, text=f"{int(self.x)},{int(self.y)} {self.zoom_level}", fill="white")
        #self.c = self.create_text(self.phys_width/2, self.phys_height/2, text=f"{int(self.x+(self.virt_width/2))}, {int(self.y+(self.virt_height/2))}", fill="white")
        #print(f"center is {int(self.x+(self.virt_width/2))}, {int(self.y+(self.virt_height/2))}")
        print(f"x, y: {int(self.x), int(self.y)}")
    def virt_to_phys(self, x, y):
        new_x = int((x - self.x) / (self.zoom_factor ** self.zoom_level * 1000000)) + 500
        new_y = int((y - self.y) / (self.zoom_factor ** self.zoom_level * 1000000)) + 500
        print("====")
        print("self.x, self.y", self.x, self.y)
        print("new_y, new_x", new_y, new_x)
        print("x, y", x, y)
        #print("a", new_x, new_y)
        #new_x -= (self.phys_width / 2)
        #new_y -= (self.phys_height / 2)
        #print("b", new_x, new_y)

#        print(f"zoom: {self.zoom_level}\tx, y: {(x, y)}\tn_x, n_y: {(new_x, new_y)}")
        return new_x, new_y
        #self.virt_width = self.phys_width * 10 ** self.zoom_level * 1000000
    def zoom_out(self):
        self.zoom("out")
    def zoom_in(self):
        self.zoom("in")
    def zoom(self, direction):
        if direction == "in":
            self.zoom_level -= 1
            #self.x += int(self.virt_width/4)
            #self.y += int(self.virt_height/4)
            change = (self.virt_width / 2) - ((self.virt_width/self.zoom_factor)/2)
            change = 0
            print("=======")
            print(f"x: {self.x}")
            print(f"virt_width: {self.virt_width}")
            print(f"v_w/2: {self.virt_width/2}")
            print(f"(virt_width/zoom_factor)/2: {(self.virt_width/self.zoom_factor)/2}")
            print(f"change: {change}")
            self.x += change
            self.y += change
            print("ZOOMING IN")

        else:
            self.zoom_level += 1
            change = (self.virt_width/2)
            change = 0
            self.x -= change
            self.y -= change
            print("=======")
            print(f"x: {self.x}")
            print(f"virt_width: {self.virt_width}")
            print(f"v_w/2: {self.virt_width/2}")
            print(f"(virt_width/zoom_factor)/2: {(self.virt_width/self.zoom_factor)/2}")
            print(f"change: {change}")
            self.x += change
            self.y += change
            print("ZOOMING OUT")
        self.redraw()
        
    def move_object(self, xchange=0, ychange=0):
#        self.x -= xchange
#        self.y -= ychange
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
            #self.move
        for k, v in self.shipment_ids.items():
            shipment = k
            planned_obj, line_obj, ship_obj = v
            print(line_obj)
            #self.delete(line_obj)
            self.move(planned_obj, xchange, ychange)
            self.move(line_obj, xchange, ychange)
            self.move(ship_obj, xchange, ychange)

    def move_left(self):
        self.move_object(+200, 0)
 #       self.x -= 100
 #       for k, v in self.canvas_ids.items():
 #           planet = k
 #           planet_obj, name_obj = v
 #           self.move(planet.name, 100, 0)
 #           self.move(f"{planet.name}_label", 100, 0)
 #       #self.redraw()
        pass
    def move_right(self):
        self.move_object(-200, 0)
#        self.x += 100
#        for k, v in self.canvas_ids.items():
#            planet = k
#            planet_obj, name_obj = v
#            self.move(planet.name, -100, 0)
#            self.move(f"{planet.name}_label", -100, 0)
#            print(f"{planet.name}_label")
        #self.redraw()
        pass
    def move_up(self):
        self.move_object(0, 200)
#        self.y -= 100
#        for k, v in self.canvas_ids.items():
#            planet = k
#            planet_obj, name_obj = v
#            self.move(planet.name, 0, 100)
#            self.move(f"{planet.name}_label",0, 100)
        #self.redraw()
        pass
    def move_down(self):
        self.move_object(0, -200)
#        self.y += 100
#        for k, v in self.canvas_ids.items():
#            planet = k
#            planet_obj, name_obj = v
#            self.move(planet.name, 0, -100)
#            self.move(f"{planet.name}_label", 0, -100)
#        #self.redraw()
        pass
    def create_planned_line(self, shipment):
        source_x, source_y = shipment.source.x, shipment.source.y
        dest_x, dest_y = shipment.dest.x, shipment.dest.y
        phys_source_x, phys_source_y = self.virt_to_phys(source_x, source_y)
        phys_x, phys_y = self.virt_to_phys(dest_x, dest_y)
#        phys_source_x = source_x - self.x
#        phys_source_y = source_y - self.y
#        phys_x = dest_x - self.x
#        phys_y = dest_y - self.y
        
        print(f"psx: {phys_source_x}, psy: {phys_source_y}, px:{phys_x}, py:{phys_y}")
        print(f"sx: {source_x}, sy:{source_y}, dx:{dest_x}, dy:{dest_y}")
        planned_route = self.game.canvas.create_line(phys_source_x, phys_source_y, phys_x, phys_y, fill="green", width=1)
        # highest length is about 42.5billion
        # dont go over 10k objects
        print("CREATED PLANNED ROUTE")
        return planned_route
        #self.shipment_ids[shipment][0] = planned_route
    def create_shipment_line(self, shipment):
        source_x, source_y = shipment.source.x, shipment.source.y
        x, y = shipment.x, shipment.y
        phys_source_x, phys_source_y = self.virt_to_phys(source_x, source_y)
        phys_x, phys_y = self.virt_to_phys(x, y)
        #phys_source_x = source_x - self.x
        #phys_source_y = source_y - self.y
        #phys_x = x - self.x
        #phys_y = y - self.y
        #print(phys_source_x, phys_source_y, phys_x, phys_y)
        
        line = self.create_line(phys_source_x, phys_source_y, phys_x, phys_y, fill="purple", width=3)
        ship_graphic = self.create_rectangle(phys_x-2, phys_y-2, phys_x+2, phys_y+2, fill="red", outline="black")
#        print(f"ship object id: {ship_graphic}")
#        try:
#            del self.shipment_ids[shipment]
#            print(f"deleted {shipment}")
#        except: pass
        self.shipment_ids[shipment][1] = line
        self.shipment_ids[shipment][2] = ship_graphic
#        print(f"shipment line is {line}")
        result = self.virt_to_phys(x, y)
#        print("virt to phys: ", result)
        return line



        
        pass
    def phys_to_virt(self, x, y):
        #nx = (x - sx) / (f**L*1000000)
        #nx * (f**L*1000000) = x-sx
        #nx * (f**L*1000000) + sx = x
        #new_x = int((x - self.x) / (self.zoom_factor ** self.zoom_level * 1000000)) + 500
        #nx = (x-sx)/(f**L*10000)+500
        #nx-500=(x-sx)/(f**L*1000)
        #(nx-500)*(f**L*1000) = (x-sx)
        #x-sx = (nx-500)*(f**L*1000)
        #x = (nx-500)*(f**L*1000)
        #px = (vx - sx) / (f**L*10000)+500
        #px - 500 = (vx-sx)/(f**L*1000)
        #(px - 500)*(f**L*1000) = (vx-sx)
        #(px - 500)*(f**L*1000) + sx = vx
        # vx = (px - 500) * (f**L*1000) + sx
        virt_x = (x ) * (self.zoom_factor**self.zoom_level*1000000) + self.x
        virt_y = (y ) * (self.zoom_factor**self.zoom_level*1000000) + self.y
        new_x = (self.zoom_factor ** self.zoom_level*1000000) * x + self.x
        new_y = (self.zoom_factor ** self.zoom_level*1000000) * x + self.y
        return virt_x, virt_y
        return new_x, new_y

#        new_x = int((x - self.x) / (self.zoom_factor ** self.zoom_level * 1000000))
#        new_y = int((y - self.y) / (self.zoom_factor ** self.zoom_level * 1000000))
#
##        print(f"zoom: {self.zoom_level}\tx, y: {(x, y)}\tn_x, n_y: {(new_x, new_y)}")
#        return new_x, new_y
        
    def onObjectClick(self, event):
        print("Got object click", event.x, event.y)
        which_object = event.widget.find_closest(event.x, event.y)
        print(event.widget.find_closest(event.x, event.y))
        current_time = datetime.datetime.now()
        if self.last_click:
            last_object, last_time = self.last_click
            if last_object == which_object:
                print(current_time - last_time)
                difference = current_time - last_time
                print(difference)
                print(datetime.timedelta(milliseconds=500))
                if difference <= datetime.timedelta(milliseconds=500):
                    print("DOUBLECLICKED")
                    x = event.x - 500
                    y = event.y - 500
                    x, y = self.phys_to_virt(x, y)
                    
                    self.x, self.y = x, y

                    self.redraw()
                
        self.last_click = (which_object, current_time)
        print(self.last_click)
        
    def draw_planet(self, planet):
        #x_coord = planet.x - self.x
        #x_coord = planet.x / self.virt_width * self.phys_width
        #y_coord = planet.y / self.virt_height * self.phys_height
        x_coord, y_coord = self.virt_to_phys(planet.x, planet.y)
        #self.virt_width = self.phys_width * 10 ** self.zoom_level * 1000000
#        y_coord = planet.y - self.y
        radius = 5
        if planet.name == "sun":
            radius = 10
        xl = x_coord - radius
        yl = y_coord - radius
        xr = x_coord + radius
        yr = y_coord + radius
        #print(x_coord, y_coord)
        name_cvsid = None
        if self.zoom_level <= 9:
            name_cvsid = self.create_text(xl, yl-10, text=planet.name, fill="white", tag=f"{planet.name}_label")
        print(f"orbit is {planet.get_parent()}")
        parent = planet.get_parent()
        orbit_csvid = None
        if parent:
            print("does this even run?")
            x, y = self.virt_to_phys(parent.x, parent.y)
        #self.canvas.create_oval(xl, yl, xr, yr, fill=planet.color, outline="black")
            distance = self.game.find_distance(x, y, x_coord, y_coord)
            print(f"distance is: {distance}")
            orbit_csvid = self.create_oval(x - distance, y - distance, x + distance, y + distance, outline="gray", width=1, tag="something")
        if planet.name == "mars":
            
            planet_cvsid = self.create_oval(xl, yl, xr, yr, fill=planet.color, outline="black", tag=planet.name)
        else:
            planet_cvsid = self.create_oval(xl, yl, xr, yr, fill=planet.color, outline="purple", tag=planet.name)
        self.tag_bind(planet_cvsid, "<ButtonPress-1>", self.onObjectClick)
        #orbit_csvid = self.create_oval(x1, y1, xr, yr
        self.canvas_ids[planet] = (planet_cvsid, name_cvsid, orbit_csvid)
class Application():
    def __init__(self, socket):
        self.planets = []
        self.socket = socket
        self.root = tk.Tk()
        self.all_ships = []
        #canvas = tk.Canvas(self.root, bg="black", height=1000, width=1000)
        canvas = SpaceCanvas(self)
        
#        space_image = ImageTk.PhotoImage(Image.open("space.jpg"))
        #print(space_image)
        self.canvas = canvas
        self.canvas.bind("<Button-1>", self.clicked_canvas)
        #button1_window.pack()
        canvas.pack(side="right")
        self.planet_frame = PlanetFrame(self)
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
        print(f"Clicked at {event.x} {event.y}")
        print(self.canvas.phys_to_virt(event.x, event.y))
    def receive_loop(self):
        s = self.socket
        s.connect(("127.0.0.1", 7777))
        while True:
            lines = str(s.recv(1024).decode("utf-8")).lower().split("\r\n")
            for l in lines: 
                l = l.strip()
                try:
                    message_dict = json.loads(l)
                except:
                    continue
                print(message_dict)
                message_type = message_dict.get("message_type")
                if message_type == "planet_info":
                    x = message_dict.get("x")
                    y = message_dict.get("y")
                    radius = message_dict.get("radius")
                    name = message_dict.get("name")
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
