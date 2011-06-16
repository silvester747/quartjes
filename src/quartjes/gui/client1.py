# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 22:04:13$"

from Tkinter import *

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def add_drink(self):
        print "Drink added"

    def remove_drink(self):
        print "Drink removed"

    def createWidgets(self):
        
        self.b_add_drink = Button(self, text = "Add drink",fg = "red", command =  self.add_drink)
        self.b_remove_drink = Button(self, text = "Remove drink", command = self.remove_drink)

        self.b_add_drink.grid(row = 0,column=0,sticky=EW)
        self.b_remove_drink.grid(row = 1,column = 0,sticky=EW)

root = Tk()
app = Application(master=root)
app.mainloop()
root.destroy()
