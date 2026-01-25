import mesa
import numpy as np
from kiln import KilnAgent  # Import KilnAgent to access them from the model

class BuyerAgent(mesa.Agent):
    def __init__(self, model, buyer_id, location, kilns):
        super().__init__(model)
        self.buyer_id = buyer_id
        self.location = location
        self.demand = int(np.random.lognormal(3, 1))  
        self.kilns = kilns # Kept for reference, but not used for buying anymore
        
        # Budget: Max price they are willing to pay per brick (Reservation Price)
        # Based on typical market rates ~11-15 PKR with some variance
        self.max_willingness_to_pay = np.random.uniform(20.0, 25.0) 
        
        self.bricks_bought = 0

    def buy_bricks(self):
        self.bricks_bought = 0
        
        # 1. Retrieve ALL kilns from the model logic
        # We access the global kiln list instead of the local 'self.kilns'
        all_kilns = list(self.model.agents_by_type[KilnAgent])
        
        # 2. Select a Random Sample (e.g., 100 kilns)
        sample_size = 100
        shopping_list = self.random.sample(all_kilns, sample_size)

        # 3. Sort by Price (Cheapest First)
        shopping_list.sort(key=lambda k: k.sale_price)

        # 4. Buy Loop
        current_demand = self.demand
        
        for kiln in shopping_list:
            if current_demand <= 0:
                break
                
            # Skip if kiln is too expensive
            if kiln.sale_price > self.max_willingness_to_pay:
                continue
                
            # Skip if kiln has no stock
            if kiln.brick_inventory <= 0:
                continue

            # How much can we buy?
            transaction_amount = min(current_demand, kiln.brick_inventory)
            
            # Execute Transaction
            cost = transaction_amount * kiln.sale_price
            kiln.revenue += cost
            kiln.brick_inventory -= transaction_amount
            kiln.bricks_sold += transaction_amount 
            
            self.bricks_bought += transaction_amount
            current_demand -= transaction_amount