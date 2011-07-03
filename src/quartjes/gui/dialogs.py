# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *

class dialog(Frame):
    def __init__(self, root, type):
        root.title('Edit database')
        Frame.__init__(self, root)
        self.root = root
        self.pack()
        self.createWidgets(type)

    def connect_to_server(self):
        print 'hoi'

    def edit_db(self):
        print 'hoi'

    def sell(self):
        print 'hoi'

    def createWidgets(self,type):
        font16 = ("Arial", 26, "bold")
        if type is "edit_db":
            self.b_add_drink = Button(self, text = "Edit database",command =  self.edit_db, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)

            self.b_remove_drink = Button(self, text = "Sell dialog", command = self.sell, width = 20, height = 2, font = font16)
            self.b_remove_drink.grid(row = 2,column = 0,sticky=EW, padx = 20, pady = 20)

            self.b_connect_to_server = Button(self, text = "Not connected", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, width = 20, height = 2, font = font16)
            self.b_connect_to_server.grid(row = 0,column=0,sticky=EW, padx = 20, pady = 20)
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
            self.b_add_drink = Button(self, text = "Edit database",command =  self.edit_db, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)

            self.b_remove_drink = Button(self, text = "Sell dialog", command = self.sell, width = 20, height = 2, font = font16)
            self.b_remove_drink.grid(row = 2,column = 0,sticky=EW, padx = 20, pady = 20)

            self.b_connect_to_server = Button(self, text = "Not connected", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, width = 20, height = 2, font = font16)
            self.b_connect_to_server.grid(row = 0,column=0,sticky=EW, padx = 20, pady = 20)

if __name__ == "__main__":
    print "Hello World"