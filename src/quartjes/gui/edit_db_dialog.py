# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *
from quartjes.models.drink import Drink,Mix
from mix_dialog import mix_dialog 
from drink_dialog import drink_dialog
from quartjes.connector.client import tk_event_listener, tk_prepare_instance_for_events


class edit_db_dialog(Frame):
    def __init__(self, root):
        root.title('Database editor')
        Frame.__init__(self, root)

        # keep local drinks db in sync
        self.drinks = self.master.conn.database.get_drinks()        
        tk_prepare_instance_for_events(self)
        self.master.conn.database.on_drinks_updated += self.db_update_listener

        self.createWidgets(type)
        self.pack()

    @tk_event_listener
    def db_update_listener(self,drinks):
        self.drinks = drinks
        self.update_listbox()

    def add_drink(self):
        d = Drink()
        master = Tk()
        drink_dialog(master,d)
        master.wait_window()
                
        self.drinks.append(d)
        self.master.conn.database.add(d)
        self.update_listbox()

    def add_mix(self):
        mix = Mix()
        master = Toplevel()
        master.drinks = self.drinks
        mix_dialog(master,mix)
        master.wait_window()

        self.master.conn.database.add(mix)

    def edit_drink(self):        
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            master = Toplevel()
            master.drinks = self.drinks
            selected = int(selection[0])
            drink = self.drinks[selected]
            if drink.__class__.__name__ == "Drink":
                drink_dialog(master,drink)
            elif drink.__class__.__name__ == "Mix":
                mix_dialog(master,drink)
            master.wait_window()
            self.master.conn.database.update(drink)

    def remove_drink(self):
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            selected = int(selection[0])            
            self.master.conn.database.remove(self.drinks[selected])
            
    def drinks_update_listener(self,drinks):
        self.update_listbox()

    def update_listbox(self):
        self.lb_drinks.delete(0,END)
        for d in self.drinks:
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
    from quartjes.connector.client import ClientConnector
    master = Tk()
    master.conn = ClientConnector()
    master.conn.start()
    app = edit_db_dialog(master)
    app.mainloop()
