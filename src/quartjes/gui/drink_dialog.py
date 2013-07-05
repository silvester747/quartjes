# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 7, 2011 9:26:44 PM$"

from Tkinter import *
from tkColorChooser import askcolor
from quartjes.models.drink import Drink

class drink_dialog(Frame):
    def __init__(self, root, drink):
        root.title('Drink dialog')
        Frame.__init__(self,root)        
        self.tags = ["name","alc_perc","unit_price","unit_amount"]
        self.drink = drink
        self.temp_color = self.drink.color
        self.pack(padx = 20, pady = 20)
        self.createWidgets()
        self.reset_object_values()
        
        self.master.save_drink = False

    def reset_object_values(self):
        self.temp_color = self.drink.color
        hexcolor = '#%02x%02x%02x' % self.temp_color
        self.b_color.config(bg = hexcolor)

        for tag in self.tags:
            text = getattr(self.drink, tag)
            self.__dict__["e_" + tag].delete(0,END)
            self.__dict__["e_" + tag].insert(END,text)

    def set_color(self):
        color = askcolor(master=self,initialcolor = self.temp_color)
        self.temp_color = color[0]
        self.b_color.config(bg = color[1])

    def cancel(self):
        self.master.save_drink = False
        self.master.destroy()

    def save(self):
        self.drink.color = self.temp_color
        self.drink.name = self.e_name.get()
        for tag in self.tags[1:]:
            setattr(self.drink, tag, float(self.__dict__["e_" + tag].get()))

        self.master.save_drink = True
        self.master.destroy()

    def createWidgets(self):
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

        for tag in self.tags:
            self.__dict__["l_" + tag] = Label(self,text = tag)
            self.__dict__["l_" + tag].grid(row = self.tags.index(tag),column = 0,sticky=E)

            self.__dict__["e_" + tag] = Entry(self)
            self.__dict__["e_" + tag].grid(row = self.tags.index(tag),column = 1,sticky=EW)

if __name__ == "__main__":
    root = Tk()
    d = Drink()
    app = drink_dialog(root,d)
    app.mainloop()