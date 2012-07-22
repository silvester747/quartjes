# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *
from quartjes.connector.client import tk_event_listener, tk_prepare_instance_for_events

class SellDialog(Frame):
    font16 = ("Arial", 16, "bold")
    
    def __init__(self, root):
        root.title('Sell Drinks')
        Frame.__init__(self, root)

        # keep local drinks db in sync
        self.drinks = self.master.conn.database.get_drinks()        
        tk_prepare_instance_for_events(self)
        self.master.conn.database.on_drinks_updated += self.sell_update_listener

        self.createWidgets()
        self.pack(fill=BOTH, expand=1)

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
        price = self.master.conn.stock_exchange.sell(drink,quantity)
        print price
        self.lb_history.insert(0, str(quantity) + ' ' + drink.name + ' for ' + str(price) + ' Quartjes')
        if self.lb_history.size() > 5:
            self.lb_history.delete ( 100, last=END )
            
    def quick_sell(self,quantity):
        self.sv_amount.set(quantity)
        self.sell_drinks()
        
    def calc_price(self,eventdata):
        (drink, quantity) = self.read_inputs()        
        newprice = quantity * int(drink.sellprice_quartjes())
        self.sv_price.set("Estimate: " + str(newprice) + " Quartjes")

    def update_listbox(self):
        self.lb_drinks.delete(0,END)
        for d in self.drinks:
            self.lb_drinks.insert(END,d.name)

    def listbox(self,lbf):
        vscroll = Scrollbar(lbf)
        lb = Listbox(lbf, exportselection=0, font = self.font16)
 
        vscroll.config(command=lb.yview)
        lb.config(yscrollcommand=vscroll.set)
        
        lb.pack(side=LEFT,fill=BOTH, expand=1)
        vscroll.pack(side=LEFT,fill=Y)
        return (lb)

    def stringvar(self,value,command=None):
        sv = StringVar()
        sv.trace("w", command)
        sv.set(value)
        return sv
    
    def createWidgets(self):
        self.frame1 = Frame(self, padx=10, pady=10)
        self.frame2 = Frame(self, padx=10, pady=10)
        self.frame3 = Frame(self.frame2)
        self.frame4 = Frame(self)
        
        # string variables
        self.sv_amount = self.stringvar(1,self.calc_price)
        self.sv_price = self.stringvar("")
        
        # frame 1 contents
        self.lb_drinks = self.listbox(self.frame1)
        self.lb_history = self.listbox(self.frame3)
        
        # frame 2 contents
        self.l_amount = Label(self.frame2, text = "Amount:", font = self.font16)         
        self.e_amount = Entry(self.frame2, textvariable = self.sv_amount, font = self.font16, text = 1)        
        self.l_price  = Label(self.frame2, textvariable = self.sv_price, font = self.font16)
        self.b_sell = Button(self.frame2, height=2, text = "Sell", bg="#999999", command = self.sell_drinks, activebackground="#ff5555", font = self.font16)
        
        # create quicksell buttons
        self.l_qs  = Label(self.frame4, text="Quick\nSell", font = self.font16)
        self.l_qs.pack(fill=BOTH, expand=1)
        self.b_qsell = list()
        for i in [1,2,5,10,20,50,100]:
            self.b_qsell.append(Button(self.frame4, text = str(i), bg="#999999", command = lambda x=i: self.quick_sell(x), activebackground="#ff5555", font = self.font16))

        for b in self.b_qsell:
            b.pack(fill=BOTH, expand=1)
        
        self.l_history  = Label(self.frame2, height=2, text="Sales history", font = self.font16)
       
        # Position frames
        self.frame1.pack(side=LEFT,fill=BOTH, expand=1)
        self.frame4.pack(side=LEFT,fill=Y)
        self.frame2.pack(side=LEFT,fill=BOTH, expand=1)
        

        # Position widgets
        self.l_amount.pack(fill=X)
        self.e_amount.pack(fill=X)
        self.l_price.pack(fill=X)
        self.b_sell.pack(fill=X)
        self.frame4.pack(fill=X)
        self.l_history.pack(fill=X)
        self.frame3.pack(fill=BOTH, expand=1)
        
        # bind commands to actions
        self.lb_drinks.bind("<ButtonRelease-1>", self.calc_price)
        self.e_amount.bind("<KeyRelease>", self.calc_price)
        
        self.update_listbox()
        self.lb_drinks.select_set(0)
        self.calc_price(None)

if __name__ == "__main__":    
    from quartjes.connector.client import ClientConnector
    master = Tk()
    master.conn = ClientConnector()
    master.conn.start()
    app = SellDialog(master)
    app.mainloop()