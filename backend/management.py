import mesa

class Owner(mesa.Agent):

    def __init__(self, model, kiln =None , location = None, job = "owner"):
         super().__init__(model)
         self.kiln = kiln
         self.location = location
         self.job = job
         self.wealth = 0
    
    def add_wealth(self, amount):
        self.wealth += amount

class Manager(mesa.Agent): 
    def __init__(self, model, kiln =None , location = None, job = "manager"):
         super().__init__(model)
         self.kiln = kiln
         self.location = location
         self.job = job
         self.wealth = 0

    def add_wealth(self, amount):
        self.wealth += amount

class Jamaadar(mesa.Agent): 
    def __init__(self, model, kiln =None , location = None, job = "jamaadar"):
         super().__init__(model)
         self.kiln = kiln
         self.location = location
         self.job = job
         self.wealth = 0
    
    def add_wealth(self, amount):
        self.wealth += amount

class Watchman(mesa.Agent): 
    def __init__(self, model, kiln =None , location = None, job = "watchman"):
         super().__init__(model)
         self.kiln = kiln
         self.location = location
         self.job = job
         self.wealth = 0

    def add_wealth(self, amount):
        self.wealth += amount
