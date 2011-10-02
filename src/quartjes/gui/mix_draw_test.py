# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Oct 2, 2011 12:35:43 AM$"

import Image
import ImageDraw
import subprocess

def draw_gradient(draw, xy_rail1, xy_rail2, start_color, end_color):
    """
    Draw a gradient sweeping over two rails.
    draw = ImageDraw object
    xy_rail1 = ((x1, y1),(x2, y2)) description of the first rail to draw the gradient over
    xy_rail2 = ((x1, y1),(x2, y2)) description of the second rail to draw the gradient over
    start_color = color at the start of the gradient
    end_color = color at the end of the gradient.
    """

    for x1 in range(xy_rail1[0][0], xy_rail1[1][0]):
        x1_factor = (float(x1 - xy_rail1[0][0]) / float(xy_rail1[1][0] - xy_rail1[0][0]))
        y1 = xy_rail1[0][1] + (x1_factor *
            (xy_rail1[1][1] - xy_rail1[0][1]))
        x2 = xy_rail2[0][0] + (x1_factor *
            (xy_rail2[1][0] - xy_rail2[0][0]))
        y2 = xy_rail2[0][1] + (x1_factor *
            (xy_rail2[1][1] - xy_rail2[0][1]))

        if x1_factor < 0.25:
            color_factor = 0
        elif x1_factor > 0.75:
            color_factor = 1
        else:
            color_factor = (x1_factor - 0.25) * 2

        r = int(start_color[0] + (color_factor * (end_color[0] - start_color[0])))
        g = int(start_color[1] + (color_factor * (end_color[1] - start_color[1])))
        b = int(start_color[2] + (color_factor * (end_color[2] - start_color[2])))
        a = int(start_color[3] + (color_factor * (end_color[3] - start_color[3])))

        #print("%f (%i, %i) - (%i, %i)" % (x1_factor, x1, y1, x2, y2))
        draw.line(((x1, y1), (x2, y2)), fill=(r, g, b, a))

        

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