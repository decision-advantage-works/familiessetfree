import numpy as np
import mesa
from mesa.experimental.meta_agents.meta_agent import MetaAgent
from management import Owner, Manager, Jamaadar, Watchman
from laborer import BrickMaker
from utility import update_workforce 

class KilnAgent(MetaAgent):
    
    def __init__(self, model, workforce, kiln_id, location, kiln_type, kiln_tech="Hand-Made"):
        super().__init__(model, workforce)
        self.kiln_id = kiln_id
        self.location = location
        self.kiln_type = kiln_type
        self.kiln_tech = kiln_tech
        self.num_workers = len(workforce)
        self.brick_inventory = 0
        self.bricks_sold = 0
        self.bricks_made = 0
        self.price_history = []
        self.total_profit = 0
        self.fixed_costs = (1100*285)/24
        self.revenue = 0
        self.total_labor = 0
        self.total_resources = 0
        self.sale_price = 0

        #--------------------------- Diversify Kilns------------------------------------
        #Base diversification approach
        scale_ratio = self.num_workers / 100.0
        urban_modifier = np.clip(0.9 + (0.15 * np.log1p(scale_ratio)), 0.9, 1.25)
        random_noise = np.random.uniform(0.95, 1.05)
        #Sale price
        base_price = { "Hand-Made" : 14,
             "Two-Roller" : 12.5, 
             "Four-Roller":12.5
             }
        if self.kiln_tech == "Hand-Made":
            self.sale_price = base_price[self.kiln_tech] * urban_modifier * random_noise
        elif self.kiln_tech == "Two-Roller":
            self.sale_price = base_price[self.kiln_tech] * urban_modifier * random_noise
        elif self.kiln_tech == "Four-Roller":
            self.sale_price = base_price[self.kiln_tech] * urban_modifier * random_noise
        else: 
            print("I knew it, I am surrounded by assholes, you didnt identify a kiln-tech!")
        
        #Wages
        self.wages = {}

        base_wages = {
            # Synpop Job
            "BrickMaker": 0.06,
            "Dryer": 0.06,
            "Transporter": 0.35 ,
            "Loader": 0.108,
            "Extractor": 0.3,
            "BrickBaker": 0.346,
            "CoalLoader": 0.138,
            "Insulator": 0.138,
            # Management/Fixed (from model.py)
            "jamaadar": 0.102,
            "watchman": 0.102,
            "manager": 0.303, }
        
        for job, base_wage in base_wages.items():
            self.wages[job] = base_wage * urban_modifier * random_noise               
        
        # Non-Labor Resources
        resource_costs = {
                "coal": self.model.coal, "electricity": self.model.electricity, "diesel": self.model.diesel,
                "mud_sand_water": self.model.mud_sand_water, "maintenance": self.model.maintenance
            }
        resource_2roller = {
            "coal": self.model.coal*0.96, "electricity": self.model.electricity*0.05, "diesel": self.model.diesel*4.7,
            "mud_sand_water": self.model.mud_sand_water*1.1, "maintenance": self.model.maintenance+0.16
        }
        resource_4roller = {
            "coal": self.model.coal, "electricity": self.model.electricity*0.02, "diesel": self.model.diesel*4.7,
            "mud_sand_water": self.model.mud_sand_water, "maintenance": self.model.maintenance+0.08
        }

        # Labor Resources
        self.resource_costs = {}
        if self.kiln_tech == "Hand-Made": 
            for res, cost in resource_costs.items():
                self.resource_costs[res] = cost * self.model.random.uniform(0.98, 1.02)
            
        elif self.kiln_tech == "Two-Roller":
            #Remove workers
            displaced_dict, displaced_list = update_workforce(self)
            self.remove_constituting_agents(displaced_list)
            self.model.displaced.update(displaced_dict)
            for res, cost in resource_2roller.items():
                self.resource_costs[res] = cost * self.model.random.uniform(0.98, 1.02)
        
        elif self.kiln_tech == "Four-Roller":
            displaced_dict, displaced_list = update_workforce(self)
            self.remove_constituting_agents(displaced_list)
            self.model.displaced.update(displaced_dict)
            for res, cost in resource_4roller.items():
                self.resource_costs[res] = cost * self.model.random.uniform(0.98, 1.02)

    def step(self):
        """
        Standard Mesa step method.
        1. Adjust Price (Close out previous cycle based on sales)
        2. Make Bricks (Start new cycle)
        """
        self.adjust_price()
        self.make_bricks()

    def make_bricks(self):
        # NOTE: Resetting variables moved to adjust_price() to allow accumulation during the step
        
        #Get bricks
        new_bricks = 0
        if self.kiln_tech == "Hand-Made": 
            for moulder in self.constituting_agents_by_type[BrickMaker]: 
                moulder.step()
                new_bricks+=moulder.bricks_made
        elif self.kiln_tech == "Two-Roller":
            #daily production +/- some noise
            new_bricks += 498333 * self.model.random.uniform(0.98, 1.02)
        elif self.kiln_tech == "Four-Roller":
            new_bricks += 1040000 * self.model.random.uniform(0.98, 1.02)
        else: 
            print("You are flung into the Gorge of Eternal Peril")

        self.brick_inventory += new_bricks
        self.bricks_made += new_bricks

        #Calculate resource costs
        self.total_resources = new_bricks * sum(self.resource_costs.values())
        #Calculate labor costs
        total_wages_to_pay = 0
        job_counts = {}
        for worker in self.agents:
            job_counts[worker.job] = job_counts.get(worker.job, 0) + 1

        for worker in self.agents:
            if worker.job == "owner":
                owner = worker
                continue
            
            # Brickmakers get paid per brick
            if worker.job == "BrickMaker":
                wage = self.wages[worker.job] * worker.bricks_made            
            else:
                # Everyone else gets paid for their share, so a manager get paid for all the bricks while a loader gets paid per portion of
                if job_counts[worker.job] > 0:
                    wage = (self.wages[worker.job] * new_bricks) / job_counts[worker.job]
                else:
                    wage = 0
            
            worker.add_wealth(wage)
            self.total_labor += wage
        
    def adjust_price(self): 

        inventory_overhang = self.brick_inventory
        
        if self.bricks_sold > 0:
             inventory_ratio = inventory_overhang / self.bricks_sold
        else:
             inventory_ratio = 999

        price_sensitivity = 0.05
        min_price = 5.0 
        max_price = 25.0

        if inventory_ratio < 0.1: # Less than 10% inventory left (High Demand)
            self.sale_price = min(max_price, self.sale_price * (1 + price_sensitivity))
        elif inventory_ratio > 0.5: # More than 50% inventory left (Low Demand)
            self.sale_price = max(min_price, self.sale_price * (1 - price_sensitivity))
            
        self.price_history.append(self.sale_price)
            
        self.revenue=round(self.revenue,2) 
       
        #Calculate worker wages --- per brick
        self.total_profit +=  round((self.revenue - self.total_resources- self.total_labor-self.fixed_costs),2)
        self.constituting_agents_by_type[Owner][0].wealth += self.total_profit

        # RESET counters for the next step cycle
        self.revenue = 0
        self.total_profit = 0
        self.bricks_made = 0
        self.bricks_sold = 0
        self.total_labor = 0
        self.total_resources = 0