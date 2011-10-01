import time
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 22:04:13$"

from Tkinter import *
from quartjes.connector.client import ClientConnector
from edit_db_dialog import edit_db_dialog
from sell_dialog import dialogSell
import tkMessageBox

class Sales_client(Frame):
    def __init__(self, root,hostname,port):
        root.title('Sales client')
        Frame.__init__(self, root)
        self.root = root
        self.pack()
        self.createWidgets()     

        self.conn = ClientConnector(hostname,port)

    def connect_to_server(self):
        if self.conn.is_connected():
            self.conn.stop()
            while self.conn.is_connected():
                time.sleep(1)
            self.b_connect_to_server.config(text = "Not connected", bg="#ff0000",activebackground="#ff5555")
        else:            
            self.conn.start()
            while not self.conn.is_connected():
                time.sleep(1)
            self.b_connect_to_server.config(text = "Connected", bg="#00ff00",activebackground="#55ff55")

    def edit_db(self):
        if self.conn.is_connected():
            root = Tk()
            root.conn = self.conn
            edit_db_dialog(root)
        else:
            tkMessageBox.showwarning("Not connected to server","Please connected to a server first.")

    def sell(self):
        if self.conn.is_connected():
            root = Tk()
            dialogSell(root, conn=self.conn)
        else:
            tkMessageBox.showwarning("Not connected to server","Please connected to a server first.")


    def createWidgets(self):
        font16 = ("Arial", 26, "bold")
        
        self.b_edit_dialog = Button(self, text = "Edit database",command =  self.edit_db, width = 20, height = 2, font = font16)
        self.b_edit_dialog.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)

        self.b_sell_dialog = Button(self, text = "Sell dialog", command = self.sell, width = 20, height = 2, font = font16)
        self.b_sell_dialog.grid(row = 2,column = 0,sticky=EW, padx = 20, pady = 20)

        self.b_connect_to_server = Button(self, text = "Not connected", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, width = 20, height = 2, font = font16)
        self.b_connect_to_server.grid(row = 0,column=0,sticky=EW, padx = 20, pady = 20)
        
if __name__ == "__main__":    
    hostname = "localhost"
    port = 1234
    
    root = Tk()
    app = Sales_client(root,hostname,port)
    app.mainloop()
    
