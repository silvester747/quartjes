# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jun 29, 2011 10:07:20 PM$"

from Tkinter import *
from tkColorChooser import *
from quartjes.models.drink import *

class Application(Frame):
    def __init__(self, root, drink):
        Frame.__init__(self,root)
        self.parent = root
        self.tags = ["name","alc_perc","unit_price","unit_amount"]
        self.drink = drink
        self.temp_color = self.drink.color        
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

        self.l_color = Label(self,text = "Color")
        self.l_color.grid(row = len(self.tags)+1,column = 0,sticky=E)
        hexcolor = '#%02x%02x%02x' % self.temp_color
        self.b_color = Button(self,bg = hexcolor,command =  self.set_color)
        self.b_color.grid(row = len(self.tags)+1,column = 1,sticky=EW)

        self.b_reset = Button(self, text = "Reset values",width = 40,command = self.reset_object_values)
        self.b_reset.grid(row = len(self.tags)+2,column = 0,columnspan = 2,pady=10)

        self.b_save = Button(self, text = "Save drink & exit",width = 20, command=self.save)
        self.b_save.grid(row = len(self.tags)+3,column = 0)

        self.b_cancel = Button(self, text = "Cancel",width = 20,command=self.cancel)
        self.b_cancel.grid(row = len(self.tags)+3,column = 1)

    def set_name(self):
        print 'temp'

    def set_color(self):
        color = askcolor(master=self,initialcolor = self.temp_color)
        self.temp_color = color[0]
        self.b_color.config(bg = color[1])

    def remove_drink(self):
        self.drink.name = self.e_name.get()
        print self.drink

    def cancel(self):
        self.parent.destroy()

    def save(self):
        self.drink.color = self.temp_color
        for tag in self.tags:
            self.drink.__dict__[tag] = self.__dict__["sv_" + tag].get()

        self.parent.destroy()
        
if __name__ == "__main__":
    d = Drink()
    root = Tk()
    app = Application(root, d)
    from pprint import pprint
    pprint(vars(app))
    app.mainloop()
    pprint(vars(d))
