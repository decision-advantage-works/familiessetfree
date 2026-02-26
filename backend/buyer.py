import mesa
from kiln import KilnAgent 

class BuyerAgent(mesa.Agent):
    def __init__(self, model, buyer_id, location, kilns,machine_bricks=False):
        super().__init__(model)
        self.buyer_id = buyer_id
        self.location = location
        self.demand = int(self.model.random.lognormvariate(12, 1))
        self.kilns = kilns 
        self.machine_bricks=machine_bricks
        
        # Budget
        self.max_willingness_to_pay = self.model.random.uniform(20.0, 25.0)
        
        self.bricks_bought = 0

    def step(self):
        self.buy_bricks()

    def buy_bricks(self):
        self.bricks_bought = 0
        
        # 1. Retrieve ALL kilns from the model logic
        # 2. Select a Random Sample 
        sample_size = min(100, len(self.model.all_kilns))
        if sample_size == 0:
            return
        shopping_list = self.random.sample(self.model.all_kilns, sample_size)

        # 3. Sort by Price (Cheapest First)
        shopping_list.sort(key=lambda k: k.sale_price)

        # 4. Buy Loop
        current_demand = self.demand
        
        for kiln in shopping_list:
            if current_demand <= 0:
                break
                
            if kiln.sale_price > self.max_willingness_to_pay:
                continue
                
            if kiln.brick_inventory <= 0:
                continue

            if self.machine_bricks==False and kiln.kiln_tech!="Hand-Made": 
                continue

            transaction_amount = min(current_demand, kiln.brick_inventory)
            
            # Execute Transaction
            cost = transaction_amount * kiln.sale_price
            kiln.revenue += cost
            kiln.brick_inventory -= transaction_amount
            kiln.bricks_sold += transaction_amount 
            
            self.bricks_bought += transaction_amount
            current_demand -= transaction_amount