#!/usr/bin/env python
'''
Created on Jun 3, 2012

@author: piet
'''
from Tkinter import Tk
from quartjes.gui.Sales_client import Sales_client
     
root = Tk()
app = Sales_client(root)
app.mainloop()