'''
Created on May 3, 2012

@author: rob
'''

import Image
import ImageDraw
import datetime

from quartjes.gui.mix_drawer import get_image_data, to_float_array4, to_int_tuple4

def create_history_graph(drink, width, height):
    """
    Draw a price history graph for the given drink.
    Returns a PIL Image object.
    """
    
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)    
    
    grid_color = (127, 127, 127, 255)
    axis_color = (255, 255, 255, 255)
    graph_color = (255, 0, 0, 255)
    
    margin = 30
    
    # Draw axis
    draw.line(((margin, 0), (margin, height - margin)), fill=axis_color, width=2)
    draw.line(((margin, height - margin), (width, height - margin)), fill=axis_color, width=2)
    
    data = drink.history
    

    if data == None:
        #print("No data")
        return image
    if len(data) < 2:
        #print("Not enough data")
        return image

    # draw x axis marks
    #print("draw x axis")
    max_x = 0
    for (x, y) in data:
        if x > max_x:
            max_x = x
    min_x = max_x
    for (x, y) in data:
        if x < min_x:
            min_x = x

    x_count = len(data)
    x_spacing = (width - margin) / (x_count - 1)
    x_label_interval = 1
    while x_spacing * x_label_interval < 100:
        x_label_interval += 1

    for i in range(x_count -1, -1, 0 - x_label_interval):
        x = margin + i * x_spacing
        draw.line(((x, margin), (x, margin* 3/4)), fill=axis_color, width=1)

        txt = datetime.datetime.fromtimestamp(data[i][0]).strftime("%H:%M")

        self.labels.add_text(txt,
                                  font_name='Times New Roman',
                                  font_size=12,
                                  anchor_x='center', anchor_y='top',
                                  position = (x, margin * 3/4))

    # draw y axis marks
    #print("draw y axis")
    max_y = 0
    for (x, y) in self.data:
        if y > max_y:
            max_y = y
    min_y = max_y
    for (x, y) in self.data:
        if y < min_y:
            min_y = y

    max_y = int(math.ceil(max_y))
    min_y = int(math.floor(min_y))

    y_count = max_y - min_y + 1
    if min_y > 0:   # only start from the bottom if we start at 0
        min_y -= 1
        y_count += 1

    y_spacing = float(h - 2 * margin) / (y_count - 1)
    #print(y_spacing)
    y_label_interval = 1
    while y_spacing * y_label_interval < 50:
        y_label_interval += 1

    #print("start drawing y")
    for y_val in range(max_y, min_y, 0 - y_label_interval):
        y = margin + (y_val - min_y) * y_spacing
        self.move_to((margin, y))
        self.line_to((margin * 3/4, y))
        self.labels.add_text(str(y_val),
                                  font_name='Times New Roman',
                                  font_size=12,
                                  anchor_x='right', anchor_y='center',
                                  position = (margin * 3/4, y))

    # draw the graph
    #print("draw graph")
    self.set_stroke_width(1.0)
    self.set_color((255, 0, 0, 255))

    x = margin
    self.move_to((x, margin + (self.data[0][1] - min_y) * y_spacing))
    x += x_spacing
    for (_, y_val) in self.data[1:]:
        y = margin + (y_val - min_y) * y_spacing
        self.line_to((x, y))
        x += x_spacing
