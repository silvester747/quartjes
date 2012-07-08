# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *
from quartjes.connector.client import tk_event_listener, tk_prepare_instance_for_events

class SellDialog(Frame):
    def __init__(self, root):
        root.title('Sell Drinks')
        Frame.__init__(self, root)
                
        # keep local drinks db in sync
        self.drinks = self.master.conn.database.get_drinks()        
        tk_prepare_instance_for_events(self)
        self.master.conn.database.on_drinks_updated += self.sell_update_listener

        self.createWidgets()
        self.pack()

    @tk_event_listener
    def sell_update_listener(self,drinks):
        self.drinks = drinks
        self.update_listbox()

    def read_inputs(self):
        # get the selected drink                     
        selection = self.lb_drinks.curselection()
        if len(selection) == 1:
            selected = int(selection[0])
        else:
            selected = 0
                
        # get the quantity
        val = self.sv_amount.get()
        if len(val) > 0:
            quantity = val
        else:
            quantity = 0
        
        return (self.drinks[selected], int(quantity))
    
    def sell_drinks(self):
        (drink, quantity) = self.read_inputs()
        print self.master.conn.stock_exchange.sell(drink,quantity)
        
    def calc_price(self,eventdata):
        (drink, quantity) = self.read_inputs()        
        newprice = quantity * int(drink.sellprice_quartjes())
        self.sv_price.set("Estimate: " + str(newprice) + " Quartjes")

    def update_listbox(self):
        self.lb_drinks.delete(0,END)
        for d in self.drinks:
            self.lb_drinks.insert(END,d.name)

    def listbox(self):
        font16 = ("Arial", 16, "bold")
        lbf = Frame(self)
        vscroll = Scrollbar(lbf)
        lb = Listbox(lbf,height=20, width=20, exportselection=0, font = font16)
        
        vscroll.config(command=lb.yview)
        lb.config(yscrollcommand=vscroll.set)
        
        lb.grid(row=1,column=1)
        vscroll.grid(row=1,column=2,sticky=NS)
        return (lb,lbf)

    def createWidgets(self):
        font16 = ("Arial", 26, "bold")
        font12 = ("Arial", 18, "bold")
        
        (self.lb_drinks,self.lbf) = self.listbox()
        self.lbf.grid(row=0, column=0, rowspan=10)
        self.lb_drinks.bind("<ButtonRelease-1>", self.calc_price)

        self.update_listbox()

        self.frame1 = Frame(self)
        self.frame1.grid(row = 0, column = 1)

        self.l_amount = Label(self.frame1, text = " Amount:", width = 30, height = 0, font = font16)
        self.l_amount.grid(row = 0,column=1,sticky=EW, padx = 20, pady = 0)

        self.sv_amount = StringVar()
        self.e_amount = Entry(self.frame1, width = 10, textvariable = self.sv_amount, font = font16, text = 1)
        self.e_amount.grid(row = 1,column=1,sticky=EW, padx = 0, pady = 0)
        self.e_amount.insert(0,1)
        self.e_amount.bind("<KeyRelease>", self.calc_price)

        self.sv_price = StringVar()
        self.l_price = Label(self.frame1, textvariable = self.sv_price, width = 20, height = 0, font = font16)
        self.l_price.grid(row = 2,column=1,sticky=EW, padx = 20, pady = 0)

        self.b_sell = Button(self, text = "Sell", bg="#999999", command = self.sell_drinks, activebackground="#ff5555", width = 20, height = 2, font = font16)
        self.b_sell.grid(row = 1,column=1,sticky=EW, padx = 20, pady = 20)


if __name__ == "__main__":    
    from quartjes.connector.client import ClientConnector
    master = Tk()
    master.conn = ClientConnector()
    master.conn.start()
    app = SellDialog(master)
    app.mainloop()