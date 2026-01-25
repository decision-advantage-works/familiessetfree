from model import KilnModel
from kiln import KilnAgent

model = KilnModel(tech = False)
print("Number of Agents: ",  len(model.agents))
print("Techup Kilns: ", model.teched_up)

#One month of production 
for _ in range(24): 
    print(_)
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
model_data.to_csv("model_data.csv")
agent_data = model.datacollector.get_agenttype_vars_dataframe(KilnAgent)
agent_data.to_csv("agent_data.csv")
print(model.teched_up)
print("###-----------------------------------------DISPLACED---------------------------------###")
print(len(model.displaced))
#print(model.displaced)
print("#########################--------DEBUG------------------------#########################")
print(model.debug) 