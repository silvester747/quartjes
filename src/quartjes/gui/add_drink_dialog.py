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
        tags = ["name","alc_perc","unit_price","unit_amount"]

        self.b_set_color = Button(self, text = "set color", command =  self.set_color).grid(row = 0,column=0,sticky=EW)

        for i in range(len(tags)):
            self.__dict__["e_" + tags[i]] = Label(self,text = tags[i]).grid(row = 1+i,column = 0,sticky=EW)

        for i in range(len(tags)):
            self.__dict__["e_" + tags[i]] = Entry(self).grid(row = 1+i,column = 1,sticky=EW)

        
if __name__ == "__main__":
    root = Tk()
    app = Application(master=root)
    app.mainloop()
