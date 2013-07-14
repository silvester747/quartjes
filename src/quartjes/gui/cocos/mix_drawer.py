"""
Module for drawing a mix drink.
"""

__author__ = "rob"
__date__ = "$Oct 2, 2011 12:35:43 AM$"

import Image
import ImageDraw
import subprocess
from numpy import array
import numpy.linalg
from pyglet.image.codecs import ImageDecodeException
from pyglet.image import ImageData

def draw_gradient(draw, rail1_start, rail1_end, rail2_start, rail2_end, 
                  start_color, end_color,
                  gradient_start=0.0, gradient_end=1.0):
    """
    Draw a gradient sweeping over two rails.
    draw = ImageDraw object
    rail1_start = Start of first rail (x,y)
    rail1_end = End of first rail (x,y)
    rail2_start = Start of second rail (x,y)
    rail2_end = End of second rail (x,y)
    start_color = color at the start of the gradient
    end_color = color at the end of the gradient.
    gradient_start = factor where to start the gradient (0.0 is start, 1.0 = end)
    gradient_end = factor where to end the gradient (0.0 is start, 1.0 = end)
    """

    rail1_start = array(rail1_start)
    rail1_end = array(rail1_end)
    rail2_start = array(rail2_start)
    rail2_end = array(rail2_end)
    
    rail1 = rail1_end - rail1_start
    rail2 = rail2_end - rail2_start
    
    len1 = numpy.linalg.norm(rail1)
    len2 = numpy.linalg.norm(rail2)

    if len2 > len1:
        rail1_start, rail2_start = rail2_start, rail1_start
        rail1_end, rail2_end = rail2_end, rail1_end
        rail1, rail2 = rail2, rail1
        len1, len2 = len2, len1
        
    delta1 = rail1 / len1
    delta2 = rail2 / len1
    
    point1 = rail1_start
    point2 = rail2_start
    
    gradient_start_pos = gradient_start * len1
    gradient_end_pos = gradient_end * len1
    
    start_color = to_float_array4(start_color)
    end_color = to_float_array4(end_color)
    color_delta = (end_color - start_color) / (gradient_end_pos - gradient_start_pos)
    color = start_color
    
    for pos in range(0, int(len1)):
        draw.line((tuple(point1.tolist()), tuple(point2.tolist())), 
                  fill=to_int_tuple4(color))
    
        if pos > gradient_start_pos and pos < gradient_end_pos:
            color += color_delta
        point1 += delta1
        point2 += delta2

def to_float_array4(arr):
    """
    Convert an iterable object of 4 nnumeric values into a NumPy array of 4 doubles.
    """
    return array((float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3])))

def to_int_tuple4(arr):
    """
    Convert an iterable object of 4 numeric values into a tuple of 4 integers.
    """
    return (int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3]))
    
def get_image_data(image):
    """
    Retrieve image data from a PIL Image so it can be loaded into a Pyglet image.
    Returns the data wrapped in a Pyglet ImageData object.
    """
    image = image.transpose(Image.FLIP_TOP_BOTTOM)

    # Convert bitmap and palette images to component
    if image.mode in ('1', 'P'):
        image = image.convert()

    if image.mode not in ('L', 'LA', 'RGB', 'RGBA'):
        raise ImageDecodeException('Unsupported mode "%s"' % image.mode)
    width, height = image.size

    return ImageData(width, height, image.mode, image.tostring())

def create_image(width, height, taper, thickness, fill, colors):
    """
    Construct an image of a mix drink in a glass.
    Returns a PIL Image object.
    """
    image = Image.new("RGBA", (width, height))
    
    width -= 1
    
    glass_outer_color = (200, 200, 255, 200)
    glass_inner_color = (200, 200, 255, 100)
    
    draw = ImageDraw.Draw(image)
    draw.polygon(((0, 0), (width, 0), (width-taper, height), (taper, height)),
        fill=glass_outer_color)
    draw.polygon(((thickness, 0), (width-thickness, 0),
        (width-taper-thickness, height-thickness), (taper+thickness, height-thickness)),
        fill=glass_inner_color)
    
    taper_from_y = lambda y: int((float(y) / height) * taper)
    start_x_from_y = lambda y: taper_from_y(y) + thickness
    end_x_from_y = lambda y: width - taper_from_y(y) - thickness
    
    delta_y = int (((height - thickness) * fill) / len(colors))
    y = thickness + (1-fill) * (height - thickness)
    
    for (start_color, end_color) in colors:
    
        draw_gradient(draw, 
                      rail1_start=(start_x_from_y(y), y), 
                      rail1_end=(end_x_from_y(y), y),
                      rail2_start = (start_x_from_y(y+delta_y), y + delta_y), 
                      rail2_end = (end_x_from_y(y+delta_y), y + delta_y),
                      start_color = start_color, 
                      end_color = end_color,
                      gradient_start = 0.1,
                      gradient_end = 0.7)
        y += delta_y
    
    del draw
    
    return image

def create_mix_drawing(height, width, mix):
    """
    Construct an image for the given mix drink.
    Returns the image wrapped in a Pyglet ImageData object.
    """
    taper = 30
    thickness = 5
    fill = 0.9
    
    mix.update_properties()
    colors = []
    for drink in mix.drinks:
        colors.append((drink.color + (140,), mix.color + (140,)))
    
    im = create_image(width, height, taper, thickness, fill, colors)
    return get_image_data(im)

def self_test():
    """
    Do a simple self test, store the result on disk and open Eye of Gnome to display the result.
    """
    
    width = 250
    height = 400
    taper = 30
    thickness = 5
    fill = 0.9
    
    colors = (((255, 0, 0, 255), (255, 255, 0, 255)),
              ((0, 255, 0, 255), (255, 255, 0, 255)),
              ((0, 255, 0, 255), (255, 255, 0, 255)),
              ((0, 255, 0, 255), (255, 255, 0, 255)))
    
    im = create_image(width, height, taper, thickness, fill, colors)
    data = get_image_data(im)
    print(data)
    
    im.save('test.png')
    subprocess.Popen(['/usr/bin/eog', 'test.png'])
    
if __name__ == "__main__":
    self_test()