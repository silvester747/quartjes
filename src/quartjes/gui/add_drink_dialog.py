# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jun 29, 2011 10:07:20 PM$"

from Tkinter import *
from tkColorChooser import *
from quartjes.models.drink import *

class Application(Frame):
    def __init__(self, master=None):
        self.tags = ["name","alc_perc","unit_price","unit_amount","color"]
        self.drink = Drink()
        self.temp_color = self.drink.color
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()
        self.reset_object_values()

    def reset_object_values(self):
        self.temp_color = self.drink.color
        hexcolor = '#%02x%02x%02x' % self.temp_color
        self.b_color.config(bg = hexcolor)

        for tag in self.tags:
            self.__dict__["sv_" + tag].set(self.drink.__dict__[tag])

    def createWidgets(self):
        self.config(padx = 20, pady = 20)        
        
        for tag in self.tags:
            self.__dict__["l_" + tag] = Label(self,text = tag)
            self.__dict__["l_" + tag].grid(row = self.tags.index(tag),column = 0,sticky=E)

            sv = StringVar()
            self.__dict__["e_" + tag] = Entry(self, textvariable = sv)
            self.__dict__["sv_" + tag] = sv
            self.__dict__["e_" + tag].grid(row = self.tags.index(tag),column = 1,sticky=EW)


        hexcolor = '#%02x%02x%02x' % self.temp_color
        self.b_color = Button(self, text = "set color",bg = hexcolor,command =  self.set_color)
        self.b_color.grid(row = self.tags.index("color"),column = 1,sticky=EW)

        self.b_commit = Button(self, text = "Save drink",width = 50)
        self.b_commit.grid(row = len(self.tags)+1,column = 0,columnspan = 2,pady=10)

    def set_name(self):
        print 'temp'

    def set_color(self):
        color = askcolor(master=self,initialcolor = self.temp_color)
        self.temp_color = color[0]
        self.b_color.config(bg = color[1])

    def remove_drink(self):
        self.drink.name = self.e_name.get()
        print self.drink
        
if __name__ == "__main__":
    root = Tk()
    app = Application(master=root)
    from pprint import pprint
    pprint(vars(app))
    app.mainloop()
