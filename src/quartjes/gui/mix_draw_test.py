# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Oct 2, 2011 12:35:43 AM$"

import Image
import ImageDraw
import subprocess
from numpy import array
import numpy.linalg

def draw_gradient(draw, xy_rail1, xy_rail2, start_color, end_color):
    """
    Draw a gradient sweeping over two rails.
    draw = ImageDraw object
    xy_rail1 = ((x1, y1),(x2, y2)) description of the first rail to draw the gradient over
    xy_rail2 = ((x1, y1),(x2, y2)) description of the second rail to draw the gradient over
    start_color = color at the start of the gradient
    end_color = color at the end of the gradient.
    """

    rail1_start = array(xy_rail1[0])
    rail1_end = array(xy_rail1[1])
    rail2_start = array(xy_rail2[0])
    rail2_end = array(xy_rail2[1])
    
    rail1 = rail1_end - rail1_start
    rail2 = rail2_end - rail2_start
    
    len1 = numpy.linalg.norm(rail1)
    len2 = numpy.linalg.norm(rail2)

    if len2 > len1:
        xy_rail1, xy_rail2 = xy_rail2, xy_rail1
        rail1_start, rail2_start = rail2_start, rail1_start
        rail1_end, rail2_end = rail2_end, rail1_end
        rail1, rail2 = rail2, rail1
        len1, len2 = len2, len1
        
    delta1 = rail1 / len1
    delta2 = rail2 / len1
    
    point1 = rail1_start
    point2 = rail2_start
    
    start_color = array(start_color)
    end_color = array(end_color)
    color_delta = (end_color - start_color) / len1
    color = start_color
    
    for _ in range(0, int(len1)):
        draw.line((tuple(point1.tolist()), tuple(point2.tolist())), fill=tuple(color.tolist()))
    
        color += color_delta
        point1 += delta1
        point2 += delta2
    

width = 250
height = 400
taper = 30
thickness = 5
fill = 0.9

colors = (((255, 0, 0, 255), (255, 255, 0, 255)),
          ((0, 255, 0, 255), (255, 255, 0, 255)),
          ((0, 255, 0, 255), (255, 255, 0, 255)),
          ((0, 255, 0, 255), (255, 255, 0, 255)))

im = Image.new("RGBA", (width, height))

width -= 1

draw = ImageDraw.Draw(im)
draw.polygon(((0,0), (width, 0), (width-taper, height), (taper, height)),
    fill=(200,200,255,255))
draw.polygon(((thickness,0), (width-thickness, 0),
    (width-taper-thickness, height-thickness), (taper+thickness, height-thickness)),
    fill=(222,222,255,255))

taper_from_y = lambda y: int((float(y) / height) * taper)
start_x_from_y = lambda y: taper_from_y(y) + thickness
end_x_from_y = lambda y: width - taper_from_y(y) - thickness

delta_y = int (((height - thickness) * fill) / len(colors))
y = thickness + (1-fill) * (height - thickness)

for (start_color, end_color) in colors:

    draw_gradient(draw, ((start_x_from_y(y), y), (end_x_from_y(y), y)),
        ((start_x_from_y(y+delta_y), y + delta_y), (end_x_from_y(y+delta_y), y + delta_y)),
        start_color, end_color)
    y += delta_y

del draw

im.save('test.png')
subprocess.Popen(['/usr/bin/eog', 'test.png'])