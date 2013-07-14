'''
Created on May 3, 2012

@author: rob
'''

import Image
import ImageDraw
import datetime
import math

from quartjes.models.drink import Drink, to_quartjes
from quartjes.gui.cocos.mix_drawer import get_image_data

grid_color = (127, 127, 127, 255)
axis_color = (255, 255, 255, 255)
graph_color = (255, 0, 0, 255)

margin_x = 30
margin_y = 15

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
    
    data = drink.price_history

    if len(data) < 5:
        txt = "Not enough data"
        txt_size = draw.textsize(txt)
        draw.text((width / 2 - txt_size[0] / 2, height / 2 - txt_size[1] / 2), txt)
        return image

    # Draw axis
    draw.line(((margin_x, 0), (margin_x, height - margin_y)), fill=axis_color, width=2)
    draw.line(((margin_x, height - margin_y), (width, height - margin_y)), fill=axis_color, width=2)
    
    # Determine min and max values
    max_x = 0
    max_y = 0
    for history_item in data:
        if history_item.timestamp > max_x:
            max_x = history_item.timestamp
        y = to_quartjes(history_item.price)
        if y > max_y:
            max_y = y
    min_x = max_x
    min_y = max_y
    for history_item in data:
        if history_item.timestamp < min_x:
            min_x = history_item.timestamp
        y = to_quartjes(history_item.price)
        if y < min_y:
            min_y = y

    # draw x axis marks
    x_count = len(data)
    x_spacing = (width - 2 * margin_x) / (x_count - 1)
    x_label_interval = 1
    while x_spacing * x_label_interval < 100:
        x_label_interval += 1

    for i in range(x_count -1, -1, 0 - x_label_interval):
        x = margin_x + i * x_spacing
        draw.line(((x, height - margin_y), (x, height - (margin_y * 3/4))), fill=axis_color, width=1)
        draw.line(((x, height - margin_y), (x, 0)), fill=grid_color, width=1)

        txt = datetime.datetime.fromtimestamp(data[i].timestamp).strftime("%H:%M")
        txt_size = draw.textsize(txt)

        draw.text((x - (txt_size[0] / 2), height - (margin_y * 3/4)), txt)
        
    # draw y axis marks
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
        draw.line(((margin_x, y), (width, y)), fill=grid_color, width=1)
        
        txt = str(y_val)
        txt_size = draw.textsize(txt)
        
        draw.text(((margin_x * 3/4) - txt_size[0], y - (txt_size[1] / 2)), txt)
        
    # draw the graph
    line = []
    x = margin_x
    for history_item in data:
        y_val = to_quartjes(history_item.price)
        y = height - (margin_y + (y_val - min_y) * y_spacing)
        line.append((x, y))
        x += x_spacing
    
    draw.line(line, fill=graph_color, width=3)

    # Draw axis again
    draw.line(((margin_x, 0), (margin_x, height - margin_y)), fill=axis_color, width=2)
    draw.line(((margin_x, height - margin_y), (width, height - margin_y)), fill=axis_color, width=2)
        
    return image


def self_test():
    """
    Perform a self test.
    """
    drink = Drink()
    
    import time
    import subprocess
    import random
    t = time.time()
    val = 1.5
    
    for _ in range(0, 100):
        drink.add_price_history(t, val)
        t += 60
        val += float(random.randint(-5, 5))/10
        if val < 0:
            val = 0 - val
        
    image = create_image(drink, 800, 600)
    
    image.save('test.png')
    subprocess.Popen(['/usr/bin/eog', 'test.png'])
    
if __name__ == "__main__":
    self_test()
    