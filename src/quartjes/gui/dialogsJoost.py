# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *

class dialogsJoost(Frame):
    def __init__(self, root, type, conn = None):
        root.title('Edit database')
        Frame.__init__(self, root)
        self.root = root
        self.pack()
        self.conn = conn
        self.db = self.conn.get_service_interface("database")
        self.createWidgets(type)

    def add_drink(self):
        print 'hoi'

    def add_mix(self):
        print 'hoi'

    def edit_drink(self):
        print 'hoi'

    def remove_drink(self):
        print 'hoi'

    def fill_drinks_listbox(self,lb_drinks):
        self.drinks = self.db.get_drinks()
        names = []
        for d in self.drinks:
            names.append(d.name)
        lb_drinks.insert(names)

    def createWidgets(self,type):
        font16 = ("Arial", 26, "bold")
        if type is "edit_db":
            self.lb_drinks = Listbox(self, height=40, width = 100)
            self.lb_drinks.grid(row = 0,column=0,rowspan=10,sticky=EW, padx = 20, pady = 20)

            self.b_add_drink = Button(self, text = "Edit database",command =  self.add_drink, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 0,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_add_drink = Button(self, text = "Edit database",command =  self.add_mix, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 1,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_add_drink = Button(self, text = "Edit database",command =  self.edit_drink, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 2,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_remove_drink = Button(self, text = "Sell dialog", command = self.remove_drink, width = 20, height = 2, font = font16)
            self.b_remove_drink.grid(row = 3,column = 1,sticky=EW, padx = 20, pady = 20)

            self.fill_drinks_listbox(self.lb_drinks)
        elif type is "drink":
            self.b_add_drink = Button(self, text = "Edit database",command =  self.edit_db, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)

            self.b_remove_drink = Button(self, text = "Sell dialog", command = self.sell, width = 20, height = 2, font = font16)
            self.b_remove_drink.grid(row = 2,column = 0,sticky=EW, padx = 20, pady = 20)

            self.b_connect_to_server = Button(self, text = "Not connected", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, width = 20, height = 2, font = font16)
            self.b_connect_to_server.grid(row = 0,column=0,sticky=EW, padx = 20, pady = 20)
        elif type is "mix":
            self.b_add_drink = Button(self, text = "Edit database",command =  self.edit_db, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)

            self.b_remove_drink = Button(self, text = "Sell dialog", command = self.sell, width = 20, height = 2, font = font16)
            self.b_remove_drink.grid(row = 2,column = 0,sticky=EW, padx = 20, pady = 20)

            self.b_connect_to_server = Button(self, text = "Not connected", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, width = 20, height = 2, font = font16)
            self.b_connect_to_server.grid(row = 0,column=0,sticky=EW, padx = 20, pady = 20)
        elif type is "sell":
            self.lb_drinks = Listbox(self, height=40, width = 100)
            self.lb_drinks.grid(row = 0,column=0,rowspan=10,sticky=EW, padx = 20, pady = 20)
            self.fill_drinks_listbox(self.lb_drinks)

            self.l_amount = Label(self, text = " Amount:", width = 20, height = 2, font = font16)
            self.l_amount.grid(row = 0,column=1,sticky=EW, padx = 20, pady = 20)

            self.e_amount = Entry(selft, width = 20, height = 2, font = font16)
            self.e_amount.grid(row = 1,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_sell = ButtonButton(self, text = "Sell", bg="#990000", activebackground="#ff5555", command =  self.connect_to_server, width = 20, height = 2, font = font16)
            self.b_sell.grid(row = 2,column=1,sticky=EW, padx = 20, pady = 20)



if __name__ == "__main__":
    root = Tk()
    app = dialogsJoost(root,"sell")
    app.mainloop()