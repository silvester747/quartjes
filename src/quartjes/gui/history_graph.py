'''
Created on May 3, 2012

@author: rob
'''

import Image
import ImageDraw
import datetime
import math

from quartjes.models.drink import Drink
from quartjes.gui.mix_drawer import get_image_data

def create_pyglet_image(drink, width, height):
    """
    Draw a price history graph for the given drink.
    Returns Image data for use with Pyglet.
    """
    
    return get_image_data(create_image(drink, width, height))

def create_image(drink, width, height):
    """
    Draw a price history graph for the given drink.
    Returns a PIL Image object.
    """
    
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)    
    
    grid_color = (127, 127, 127, 255)
    axis_color = (255, 255, 255, 255)
    graph_color = (255, 0, 0, 255)
    
    margin_x = 30
    margin_y = 15
    
    
    
    # Draw axis
    draw.line(((margin_x, 0), (margin_x, height - margin_y)), fill=axis_color, width=2)
    draw.line(((margin_x, height - margin_y), (width, height - margin_y)), fill=axis_color, width=2)
    
    data = drink.history
    

    if data == None:
        #print("No data")
        return image
    if len(data) < 2:
        #print("Not enough data")
        return image

    # draw x axis marks
    max_x = 0
    for (x, y) in data:
        if x > max_x:
            max_x = x
    min_x = max_x
    for (x, y) in data:
        if x < min_x:
            min_x = x

    x_count = len(data)
    x_spacing = (width - 2 * margin_x) / (x_count - 1)
    x_label_interval = 1
    while x_spacing * x_label_interval < 100:
        x_label_interval += 1

    for i in range(x_count -1, -1, 0 - x_label_interval):
        x = margin_x + i * x_spacing
        draw.line(((x, height - margin_y), (x, height - (margin_y * 3/4))), fill=axis_color, width=1)

        txt = datetime.datetime.fromtimestamp(data[i][0]).strftime("%H:%M")
        txt_size = draw.textsize(txt)

        draw.text((x - (txt_size[0] / 2), height - (margin_y * 3/4)), txt)
        
    # draw y axis marks
    max_y = 0
    for (x, y) in data:
        if y > max_y:
            max_y = y
    min_y = max_y
    for (x, y) in data:
        if y < min_y:
            min_y = y

    max_y = int(math.ceil(max_y))
    min_y = int(math.floor(min_y))

    y_count = max_y - min_y + 1
    if min_y > 0:   # only start from the bottom if we start at 0
        min_y -= 1
        y_count += 1

    y_spacing = float(height - 2 * margin_y) / (y_count - 1)
    y_label_interval = 1
    while y_spacing * y_label_interval < 50:
        y_label_interval += 1

    for y_val in range(max_y, min_y, 0 - y_label_interval):
        y = height - (margin_y + (y_val - min_y) * y_spacing)
        draw.line(((margin_x * 3/4, y), (margin_x, y)), fill=axis_color, width=1)
        
        txt = str(y_val)
        txt_size = draw.textsize(txt)
        
        draw.text(((margin_x * 3/4) - txt_size[0], y - (txt_size[1] / 2)), txt)
        
    # draw the graph
    line = []
    x = margin_x
    for (_, y_val) in data:
        y = height - (margin_y + (y_val - min_y) * y_spacing)
        line.append((x, y))
        x += x_spacing
    
    draw.line(line, fill=graph_color, width=3)
        
    return image


def self_test():
    """
    Perform a self test.
    """
    drink = Drink()
    
    import time
    import subprocess
    t = time.time()
    
    history = []
    history.append((t, 10))
    t += 60
    history.append((t, 8))
    t += 60
    history.append((t, 9))
    t += 60
    history.append((t, 5))
    t += 60
    history.append((t, 12))
    t += 60
    history.append((t, 15))
    
    drink.history = history
    
    image = create_image(drink, 800, 600)
    
    image.save('test.png')
    subprocess.Popen(['/usr/bin/eog', 'test.png'])
    
if __name__ == "__main__":
    self_test()
    