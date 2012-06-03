'''
Created on Jun 3, 2012

@author: piet
'''
from Tkinter import Tk
from quartjes.gui.Sales_client import Sales_client
     
hostname = None
port = 1234
    
root = Tk()
app = Sales_client(root,hostname,port)
app.mainloop()