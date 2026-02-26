import json
from model import KilnModel
from kiln import KilnAgent

#with open('zz_punjab.json', 'r') as f:
#    kilns_to_tech = json.load(f)

#print(f"Len of ZZ punjab kilns {len(kilns_to_tech)}")
model = KilnModel(tech = False, kilns_to_tech=[], coal=4.61,machine_bricks=0.0)
print("Number of Agents: ",  len(model.agents))
print("Techup Kilns: ", model.teched_up)

#One month of production 
for _ in range(24): 
    print(_)
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
model_data.to_csv("ouput/model_data_test2.csv")
agent_data = model.datacollector.get_agenttype_vars_dataframe(KilnAgent)
agent_data.to_csv("ouput/agent_data_test2.csv")
print(model.teched_up)
print("###-----------------------------------------DISPLACED---------------------------------###")
print(len(model.displaced))
#print(model.displaced)
print("#########################--------DEBUG------------------------#########################")
print(model.debug) 