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

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def calc_production(model, age, gender):
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

    def __init__(self, rng=42, tech=False, kilns_to_tech=None, coal=4.61,
                 electricity=0.23, diesel=0.24, mud_sand_water=1.05, maintenance=0.00, 
                 machine_bricks=0.0, progress_callback=None): 
        
        super().__init__(rng=rng)
        self.displaced = {}
        self.debug = []
        self.teched_up = 0
        self.coal = coal
        self.electricity = electricity
        self.diesel = diesel
        self.mud_sand_water = mud_sand_water
        self.maintenance = maintenance
        self.machine_bricks = machine_bricks
        self.step_count = 0  # Track simulation day
        self.agents_stepped = 0 # Track agents processed in current step
        
        if progress_callback:
            progress_callback("Loading population data...")

        #create population
        try:
            with open(os.path.join(BASE_DIR, "synpop.pkl"), 'rb') as file:
                synpop = pickle.load(file) 
        except FileNotFoundError:
            # Fallback for testing if file missing
            synpop = {}
            print("Warning: synpop.pkl not found.")
        
        teched_kiln_ids = set()
        if tech==True and kilns_to_tech == None :
            all_kiln_ids = list(synpop.keys())
            if all_kiln_ids:
                all_kiln_ids = [id[0] for id in all_kiln_ids ]
                teched_kiln_ids = set(self.random.sample(all_kiln_ids, min(len(all_kiln_ids), 500)))
        elif tech==True and kilns_to_tech != None:
            teched_kiln_ids = set(kilns_to_tech)
        
        count = 0
        total_kilns = len(synpop)
        job_map = {
            "BrickMaker": BrickMaker,
            "Dryer": Dryer,
            "Transporter": Transporter,
            "Loader": Loader,
            "Extractor": Extractor,
            "BrickBaker": BrickBaker,
            "CoalLoader": CoalLoader,
            "Insulator": Insulator,
        }
        
        for kiln_data, workers in synpop.items(): 
            count += 1
            if progress_callback and count % 10 == 0:
                # Show Kiln progress
                progress_callback(f"Initializing Kilns: {count}/{total_kilns}")

            kiln_id = kiln_data[0]
            kiln_loc = kiln_data[1]
            kiln_type = kiln_data[2]

            # create workers
            kiln_workforce = []
            for family_id, w_data in workers:
                AgentClass = job_map.get(w_data["job"])
                if AgentClass is None:
                    continue
                
                if AgentClass != BrickMaker:
                    laboragent = AgentClass(
                        self, 
                        kiln=kiln_id,
                        location=kiln_loc,
                        family=family_id,
                        age=w_data["age"], 
                        gender=w_data["gender"]
                    ) # type: ignore
                    kiln_workforce.append(laboragent)
                else: 
                    laboragent = AgentClass(
                        self, 
                        kiln=kiln_id,
                        location=kiln_loc,
                        family=family_id,
                        age=w_data["age"], 
                        gender=w_data["gender"],
                        production = int(calc_production(self,w_data["age"], w_data["gender"]))
                    ) # type: ignore
                    kiln_workforce.append(laboragent)

            # Add Management
            kiln_workforce.append(Owner(self, kiln=kiln_id, location=kiln_loc))
            kiln_workforce.append(Jamaadar(self, kiln=kiln_id, location=kiln_loc))
            kiln_workforce.append(Watchman(self, kiln=kiln_id, location=kiln_loc))
            kiln_workforce.append(Manager(self, kiln=kiln_id, location=kiln_loc))
            
            # Determine Kiln Tech 
            if kiln_id in teched_kiln_ids:
                kiln_tech = self.random.choice(["Two-Roller", "Four-Roller"])
                self.teched_up += 1
            else: 
                kiln_tech = "Hand-Made"
            # Create kiln as meta agent
            KilnAgent(self, kiln_workforce, kiln_id, kiln_loc, kiln_type, kiln_tech,)
        
        #Make kiln refefence
        kiln_ref = {kiln.kiln_id: kiln for kiln in self.agents_by_type[KilnAgent]}

        if progress_callback:
            progress_callback(f"Kilns Loaded ({total_kilns}). Loading Buyers...")

        #Create buyers
        try:
            with open(os.path.join(BASE_DIR, "buyers.pkl"), 'rb') as file:
                buyers = pickle.load(file)
        except FileNotFoundError:
            buyers = []
            print("Warning: buyers.pkl not found.")

        buyer_count = 0
        total_buyers = len(buyers)

        for buyer in buyers: 
            buyer_count += 1
            if progress_callback and buyer_count % 10 == 0:
                # UPDATED: Show both Kiln completion and Buyer progress
                progress_callback(f"Initializing... Kilns: {total_kilns} (Done) | Buyers: {buyer_count}/{total_buyers}")

            kilns  = []
            for buy_kiln in buyer["closest_kilns"]:
                if buy_kiln in kiln_ref:
                    kilns.append(kiln_ref[buy_kiln])
            
            # Pass machine_bricks preference (0.0 - 1.0 probability)
            wants_machine = False
            if self.random.uniform(0,1) < self.machine_bricks: 
                wants_machine = True
            
            BuyerAgent(self, buyer["id"], buyer["location"], kilns, machine_bricks=wants_machine)

        self.all_kilns = list(self.agents_by_type[KilnAgent])
        self.all_buyers = list(self.agents_by_type[BuyerAgent])
        self.step_agents = self.all_kilns + self.all_buyers

        self.datacollector = DataCollector(model_reporters={"Revenue":self.get_revenue, "Profit": self.get_profit, "Bricks": self.get_production},
                                           agenttype_reporters={KilnAgent:{"Kiln":"kiln_id", "Revenue": "revenue","Profit": "total_profit", "Bricks": "bricks_made",
                                                                           "Location": "location", "Tech":"kiln_tech", "Labor": "total_labor", "Resources": "total_resources",
                                                                            "Workers":"num_workers", "Sale Price":"sale_price", "Inventory": "brick_inventory" }})
        
        if progress_callback:
            progress_callback("Initialization Complete!")

    def get_profit(self): 
        profit = 0
        for kiln in self.all_kilns:
            profit += kiln.total_profit
        return profit
    
    def get_production(self): 
        bricks = 0
        for kiln in self.all_kilns:
            bricks += kiln.brick_inventory
        return bricks
    
    def get_revenue(self): 
        revenue = 0
        for kiln in self.all_kilns:
            revenue += kiln.revenue
        return revenue
    
    def step(self): 
        """
        Mixed Step:
        Collects all KilnAgents and BuyerAgents, shuffles them together,
        and executes their step() method one by one.
        """
        self.step_count += 1
        self.agents_stepped = 0 # Reset counter for the new day
        
        # Shuffle pre-cached step agents in place
        self.random.shuffle(self.step_agents)
        
        # Execute steps
        for agent in self.step_agents:
            agent.step()
            self.agents_stepped += 1 # Increment counter

        self.datacollector.collect(self)