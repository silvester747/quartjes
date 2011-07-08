# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *
from quartjes.models.drink import *
from mix_dialog import * 
from drink_dialog import *

class edit_db_dialog(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        
        #if master.conn is not None:
        #   self.db = self.master.conn.get_service_interface("database")
        #  drinks = self.db.get_drinks()
        
        self.createWidgets(type)
        self.pack()

    def add_drink(self):
        d = Drink()
        master = Tk()
        drink_dialog(master,d)
        master.wait_window()
                
        self.master.drinks.append(d)
        self.update_listbox()

    def add_mix(self):
        mix = Mix()
        master = Tk()
        master.drinks = self.master.drinks
        mix_dialog(master,mix)
        master.wait_window()

        self.master.drinks.append(mix)
        self.update_listbox()

    def edit_drink(self):        
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            master = Tk()
            master.drinks = self.master.drinks
            selected = int(selection[0])
            drink = self.master.drinks[selected]
            if drink.__class__.__name__ == "Drink":
                drink_dialog(master,drink)
            elif drink.__class__.__name__ == "Mix":
                mix_dialog(master,drink)
            master.wait_window()
            self.update_listbox()

    def remove_drink(self):
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            selected = int(selection[0])            
            self.master.drinks.pop(selected)
            self.update_listbox()

    def update_listbox(self):
        self.lb_drinks.delete(0,END)
        for d in self.master.drinks:
            self.lb_drinks.insert(END,d.name)

    def createWidgets(self,type):
        font16 = ("Arial", 16, "bold")
        
        self.lb_drinks = Listbox(self,font = font16)
        self.b_add_drink = Button(self, text = "Add drink",command =  self.add_drink, width = 20, height = 2, font = font16)
        self.b_add_mix = Button(self, text = "Add mix",command =  self.add_mix, width = 20, height = 2, font = font16)
        self.b_edit_drink = Button(self, text = "Edit drink",command =  self.edit_drink, width = 20, height = 2, font = font16)
        self.b_remove_drink = Button(self, text = "Remove drink", command = self.remove_drink, width = 20, height = 2, font = font16)

        self.lb_drinks.grid(row = 0,column=0,rowspan=10,sticky=EW, padx = 20, pady = 20)
        self.b_add_drink.grid(row = 0,column=1,sticky=EW, padx = 20, pady = 20)
        self.b_add_mix.grid(row = 1,column=1,sticky=EW, padx = 20, pady = 20)
        self.b_edit_drink.grid(row = 2,column=1,sticky=EW, padx = 20, pady = 20)
        self.b_remove_drink.grid(row = 3,column = 1,sticky=EW, padx = 20, pady = 20)

        self.update_listbox()

if __name__ == "__main__":
    master = Tk()
    master.conn = None
    master.drinks = [Drink(name="cola"),Drink(name="bacardi",alc_perc=40)]
    
    app = edit_db_dialog(master)
    app.mainloop()
