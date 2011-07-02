# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jun 29, 2011 10:07:20 PM$"

from Tkinter import *
from tkColorChooser import *
from quartjes.models.drink import *

class Application(Frame):
    def __init__(self, master=None):
        self.drink = Drink()
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def set_name(self):
        print 'temp'

    def set_color(self):
        color = askcolor(master=self,initialcolor = self.drink.color)
        self.drink.color = color[0]

    def remove_drink(self):
        self.drink.name = self.e_name.get()
        print self.drink

    def createWidgets(self):
        self.b_set_color = Button(self, text = "set color", command =  self.set_color)
        self.b_remove_drink = Button(self, text = "Remove drink", command = self.remove_drink)
        self.e_name = Entry(self)
        self.e_alc_perc = Entry(self)
        self.e_unit_price = Entry(self)
        self.e_unit_amount = Entry(self)

        self.b_set_color.grid(row = 0,column=0,sticky=EW)
        self.b_remove_drink.grid(row = 1,column = 0,sticky=EW)
        self.e_name.grid(row = 2,column = 0,sticky=EW)
        self.e_name.grid(row = 2,column = 0,sticky=EW)
        self.e_name.grid(row = 2,column = 0,sticky=EW)

if __name__ == "__main__":
    root = Tk()
    app = Application(master=root)
    app.mainloop()
