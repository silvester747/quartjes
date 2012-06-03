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
    def __init__(self, root):
        root.title('Sales client')
        Frame.__init__(self, root)
        self.root = root
        self.pack()
        self.createWidgets()
        self.conn = ClientConnector() 

    def connect_to_server(self):        
        if self.conn.is_connected():
            self.conn.stop()
            self.b_connect_to_server.config(text = "Not connected to server", bg="#ff0000",activebackground="#ff5555")
        else:                        
            try:
                self.conn.host = str(self.e_server_hostname.get())
                self.conn.port = int(self.e_server_port.get())
            except:
                pass                
            
            self.conn.start()
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
        
        # frame 1
        self.frame1=Frame(self, width = 20, height = 2)
        
        Label(self.frame1, text="Server hostname/IP:",font = font16).grid(row=0)
        Label(self.frame1, text="Server port:",font = font16).grid(row=1)

        self.e_server_hostname = Entry(self.frame1, font = font16)
        self.e_server_port = Entry(self.frame1, font = font16)       
        self.b_connect_to_server = Button(self.frame1, text = "Connect to server", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, font = font16)
        # populate frame
        self.e_server_hostname.grid(row=0, column=1)
        self.e_server_port.grid(row=1, column=1)
        self.b_connect_to_server.grid(row=2,columnspan=2)        
        # end frame one

        self.b_edit_dialog = Button(self, text = "Edit database",command =  self.edit_db, width = 20, height = 2, font = font16)
        self.b_sell_dialog = Button(self, text = "Sell dialog", command = self.sell, width = 20, height = 2, font = font16)

        self.frame1.grid(row = 0,column=0,sticky=EW, padx = 20, pady = 20)        
        self.b_edit_dialog.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)
        self.b_sell_dialog.grid(row = 2,column = 0,sticky=EW, padx = 20, pady = 20)
        
        #return self.e_server_hostname # initial focus
       
if __name__ == "__main__":    
    root = Tk()
    app = Sales_client(root)
    app.mainloop()
    
