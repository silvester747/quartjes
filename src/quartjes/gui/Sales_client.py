# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 22:04:13$"

from Tkinter import *
from quartjes.gui.edit_db_dialog import edit_db_dialog
from quartjes.gui.sell_dialog import sell_dialog
import tkMessageBox
from axel import Event
from quartjes.connector.client import ClientConnector

class Sales_client(Frame):  
    f1 = ("Arial", 12, "bold")  
    def __init__(self, root):        
        root.title('Sales client')
        Frame.__init__(self, root)
        self.pack(fill=BOTH,expand=1)
        self.createWidgets()
        self.conn = ClientConnector() 

    def connect_to_server(self):        
        if self.conn.is_connected():
            self.conn.stop()
            self.b_connect_to_server.config(text = "Not connected to server", bg="#ff0000",activebackground="#ff5555")
            self.ed.destroy()
            self.sd.destroy()
        else:                        
            try:
                self.conn.host = str(self.e_server_hostname.get())
                self.conn.port = int(self.e_server_port.get())
            except:
                pass                
            
            self.conn.start()
            self.b_connect_to_server.config(text = "Connected", bg="#00ff00",activebackground="#55ff55")
            self.ed = edit_db_dialog(self)
            self.sd = sell_dialog(self)
            self.sd.pack(side=BOTTOM,fill=BOTH,expand=1)

    def edit_db(self):
        if self.conn.is_connected():
            self.sd.forget()
            self.ed.pack(side=BOTTOM,fill=BOTH,expand=1)
        else:
            tkMessageBox.showwarning("Not connected to server","Please connected to a server first.")

    def sell(self):
        if self.conn.is_connected():
            self.ed.forget()
            self.sd.pack(side=BOTTOM,fill=BOTH,expand=1)
        else:
            tkMessageBox.showwarning("Not connected to server","Please connected to a server first.")

    def createWidgets(self):                
        # frame 1
        self.frame1 = Frame(self)
        
        Label(self.frame1, text="Server hostname/IP:",font = self.f1).pack(side=LEFT,fill=X,expand=1)        
        self.e_server_hostname = Entry(self.frame1,font = self.f1).pack(side=LEFT,fill=X,expand=1)
        Label(self.frame1, text="Port:",font = self.f1).pack(side=LEFT,fill=X,expand=1)
        self.e_server_port = Entry(self.frame1, font = self.f1).pack(side=LEFT,fill=X,expand=1)
         
        self.b_connect_to_server = Button(self.frame1, text = "Connect to server", bg="#ff0000", activebackground="#ff5555", command =  self.connect_to_server, font = self.f1)
        self.b_connect_to_server.pack(side=LEFT,fill=X,expand=1,padx=10)

        self.b_edit_dialog = Button(self.frame1, text = "Edit database",command = self.edit_db, font = self.f1)
        self.b_sell_dialog = Button(self.frame1, text = "Sell dialog", command = self.sell, font = self.f1)

        self.frame1.pack(fill=X)
        self.b_edit_dialog.pack(side=LEFT,fill=X,expand=1,padx=10)
        self.b_sell_dialog.pack(side=LEFT,fill=X,expand=1,padx=10)
       
if __name__ == "__main__":    
    root = Tk()
    app = Sales_client(root)
    app.mainloop()
    
