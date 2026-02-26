import numpy as np
import mesa

class Laborer(mesa.Agent):

    def __init__(self, model, kiln =None , location = None, family = None, 
                 gender = None, age = None, job = None):
        super().__init__(model)
        self.family = family
        self.age = age
        self.gender = gender 
        self.kiln = kiln
        self.location = location
        self.job = job
        self.wealth = 0

    def add_wealth(self, amount):
        """Adds wages to the laborer's wealth."""
        self.wealth += amount
    

class BrickMaker(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None, production = None):
        super().__init__(model, kiln, location, family, gender, age, job="BrickMaker")
        self.production = production
        self.bricks_made = 0

    def step(self):
        self.bricks_made = 0
        random_noise = self.model.random.uniform(0.95, 1.05)
        self.bricks_made += int(random_noise * self.production)


class Dryer(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="Dryer")

class Transporter(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="Transporter")

class Loader(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="Loader")

class Extractor(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="Extractor")

class BrickBaker(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="BrickBaker")

class CoalLoader(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="CoalLoader")

class Insulator(Laborer):
    def __init__(self, model, kiln=None, location=None, family=None, gender=None, age=None):
        super().__init__(model, kiln, location, family, gender, age, job="Insulator")