import json
from model import KilnModel
from kiln import KilnAgent

#with open('zz_punjab.json', 'r') as f:
#    kilns_to_tech = json.load(f)

#print(f"Len of ZZ punjab kilns {len(kilns_to_tech)}")
model = KilnModel(tech = True, kilns_to_tech=[], coal=4.61,machine_bricks=0.5)
print("Number of Agents: ",  len(model.agents))
print("Techup Kilns: ", model.teched_up)

#One month of production 
for _ in range(3): 
    print(_)
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
model_data.to_csv("model_data_test.csv")
agent_data = model.datacollector.get_agenttype_vars_dataframe(KilnAgent)
agent_data.to_csv("agent_data_test.csv")
print(model.teched_up)
print("###-----------------------------------------DISPLACED---------------------------------###")
print(len(model.displaced))
#print(model.displaced)
print("#########################--------DEBUG------------------------#########################")
print(model.debug) 