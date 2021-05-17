#!/usr/bin/env python3
import struct
def generate():
    my_dict = {}
    position_array = []
    with open("third.bmp", "rb") as f:
        f.seek(0x0A)
        pixel_array_address = struct.unpack("<I", f.read(4))[0]
        print(pixel_array_address)
        f.seek(pixel_array_address)
        for y in range(1000):
            position_array.append([])
            current_row = position_array[-1]
            for x in range(1000):
                color = f.read(1)
                color = struct.unpack("B", color)[0]
                #print(color)
                my_dict.setdefault(color, 0)
                my_dict[color] += 1
                current_row.append(color)
    print(my_dict)
    #print(position_array)
    # O # @ !
    for r in position_array:
    #    break
        string = ""
        for c in r:
            if c == 198:
                
                char = "\033[31m#\033[0m"
                char = "!"
            elif c == 0x12:
                char = "\033[32m#\033[0m"
                char = "@"
            elif c == 0xB4:
                char = "\033[33m#\033[0m"
                char = "#"
            elif c == 0x8D:
                char = "\033[34m#\033[0m"
                char = "O"
            else:
                char = "."
            string += char
        print(string)
    return position_array
#position_array = generate()
#print(hex(position_array[500][500]))
            
