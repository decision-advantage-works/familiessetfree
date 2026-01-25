import numpy as np 
import pandas as pd
import pickle
from shapely.geometry import box
import mesa
from mesa.datacollection import DataCollector
from mesa.experimental.meta_agents.meta_agent import (
    create_meta_agent)

from laborer import Laborer
from laborer import (
    BrickMaker,Dryer, Transporter,
    Loader, Extractor, BrickBaker,
    CoalLoader, Insulator
)
from buyer import BuyerAgent

from kiln import KilnAgent
from management import Owner, Jamaadar, Watchman, Manager

def calc_production(model, age, gender):

    # Add gender factor later
    random_noise = model.random.uniform(0.95, 1.05)
    if age <= 14: 
        production = 100 * random_noise
    elif age > 14 and age <=18: 
        production = 500 * random_noise
    elif age >=18 and age <= 40: 
        production = 650 * random_noise
    else: 
        production = 500 * random_noise
    if gender == "female":
        production -= 50 * random_noise
    
    return production 
    


class KilnModel(mesa.Model):

    def __init__(self, seed=42,tech=False ): 
        super().__init__(seed=seed)
        self.displaced = {}
        self.debug = []
        self.teched_up = 0
        

        #create population
        with open("synpop.pkl", 'rb') as file: 
            synpop = pickle.load(file) 
        
       
        
        teched_kiln_ids = set()
        if tech:
            all_kiln_ids = list(synpop.keys())
            all_kiln_ids = [id[0] for id in all_kiln_ids ]
            teched_kiln_ids = set(self.random.sample(all_kiln_ids, 500))
            
            print(f"Selected {len(teched_kiln_ids)} kilns for tech upgrade.")
        
        
        for kiln_data, workers in synpop.items(): 
            """
            Structure of data is 
            {(kiln id, kiln location, kiln type) : [(family id, worker dict)] 
            """
            kiln_id = kiln_data[0]
            kiln_loc = kiln_data[1]
            kiln_type = kiln_data[2]

            job_map = {
                "BrickMaker": BrickMaker,
                "Dryer": Dryer, 
                "Transporter" :Transporter,
                "Loader" :Loader, 
                "Extractor": Extractor,
                 "BrickBaker": BrickBaker,
                 "CoalLoader": CoalLoader,
                "Insulator": Insulator
            }

            # create workers
            kiln_workforce = []
            for idx in range(len(workers)):
                w_data = workers[idx][1] # The dictionary with age, gender, job

                # Select the specific laborer class
                AgentClass = job_map.get(w_data["job"])
                
                if AgentClass != BrickMaker:
                    # Instantiate workers
                    laboragent = AgentClass(
                        self, 
                        kiln=kiln_id,
                        location=kiln_loc,
                        family=workers[idx][0],
                        age=w_data["age"], 
                        gender=w_data["gender"]
                    )
                    kiln_workforce.append(laboragent)
                else: 
                    laboragent = AgentClass(
                        self, 
                        kiln=kiln_id,
                        location=kiln_loc,
                        family=workers[idx][0],
                        age=w_data["age"], 
                        gender=w_data["gender"],
                        production = int(calc_production(self,w_data["age"], w_data["gender"]))
                    )
                    kiln_workforce.append(laboragent)

            # Add Management
            kiln_workforce.append(Owner(self, kiln=kiln_id, location=kiln_loc))
            kiln_workforce.append(Jamaadar(self, kiln=kiln_id, location=kiln_loc))
            kiln_workforce.append(Watchman(self, kiln=kiln_id, location=kiln_loc))
            kiln_workforce.append(Manager(self, kiln=kiln_id, location=kiln_loc)) #aka Munshi
            
            # Determine Kiln Tech 
            if kiln_id in teched_kiln_ids:
                kiln_tech = self.random.choice(["Two-Roller", "Four-Roller"])
                self.teched_up += 1
            else: 
                kiln_tech = "Hand-Made"
            # Create kiln as meta agent
            KilnAgent(self, kiln_workforce, kiln_id, kiln_loc, kiln_type, kiln_tech)
        #Make kiln referfence
        kiln_ref = {}
        for kiln in self.agents_by_type[KilnAgent]: 
            kiln_ref[kiln.kiln_id] = kiln
        #Create buyers
        with open("buyers.pkl", 'rb') as file: 
            buyers = pickle.load(file)
        for buyer in buyers: 
            kilns  = []
            for buy_kiln in buyer["closest_kilns"]:
                kilns.append(kiln_ref[buy_kiln])
            BuyerAgent(self, buyer["id"], buyer["location"], kilns)

        self.datacollector = DataCollector(model_reporters={"Revenue":self.get_revenue, "Profit": self.get_profit, "Bricks": self.get_production},
                                           agenttype_reporters={KilnAgent:{"Kiln":"kiln_id", "Revenue": "revenue","Profit": "total_profit", "Bricks": "bricks_made",
                                                                           "Location": "location", "Tech":"kiln_tech", "Labor": "total_labor", "Resources": "total_resources",
                                                                            "Workers":"num_workers", "Sale Price":"sale_price", "Inventory": "brick_inventory" }})

    def get_profit(self): 
        profit = 0
        for kiln in self.agents_by_type[KilnAgent]:
            profit += kiln.total_profit
        return profit
    
    def get_production(self): 
        bricks = 0
        for kiln in self.agents_by_type[KilnAgent]:
            bricks += kiln.brick_inventory
        return bricks
    
    def get_revenue(self): 
        revenue = 0
        for kiln in self.agents_by_type[KilnAgent]:
            revenue += kiln.revenue
        return revenue
    
    def step(self): 

        self.agents_by_type[KilnAgent].shuffle_do("make_bricks")
        self.agents_by_type[BuyerAgent].shuffle_do("buy_bricks")
        self.agents_by_type[KilnAgent].shuffle_do("adjust_price")

        self.datacollector.collect(self)
