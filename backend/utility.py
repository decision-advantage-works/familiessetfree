from collections import defaultdict
from laborer import (
    BrickMaker,Dryer, Transporter,
    Loader, Extractor, BrickBaker,
    CoalLoader, Insulator
)


def update_workforce(kiln):
    brickmakers = list(kiln.agents.select(agent_type=BrickMaker)) # Convert to list once
    number_to_retain = len(brickmakers) // 16
    if number_to_retain < 2: 
        number_to_retain = 2 

    # 1. Filter candidates using list comprehension (Faster than for-loop appending)
    optimal_males = [
        b for b in brickmakers 
        if b.gender == "male" and 18 <= b.age <= 50
    ]
    
    # 2. Determine who is retained (List of Agents)
    # Fix: len(optimal_males) instead of comparing list to int
    if len(optimal_males) >= number_to_retain:
        retained_agents = kiln.model.random.sample(optimal_males, number_to_retain)
    else:
        retained_agents = kiln.model.random.sample(brickmakers, number_to_retain)

    # 3. Calculate displaced using Sets (Much faster than list iteration)
    # Set difference: All Agents - Retained Agents
    retained_set = set(retained_agents)
    displaced_list = [b for b in brickmakers if b not in retained_set]

    # 4. Group displaced by family using defaultdict
    displaced_dict = defaultdict(list)
    for agent in displaced_list:
        displaced_dict[agent.family].append(agent)

    # Debug logging (Optional)
    if not len(optimal_males) >= number_to_retain:
         kiln.model.debug.append([kiln.kiln_id, len(brickmakers), [(agent.age, agent.gender) for agent in retained_agents],[(agent.age, agent.gender) for agent in displaced_list] ])

    return displaced_dict, displaced_list
   