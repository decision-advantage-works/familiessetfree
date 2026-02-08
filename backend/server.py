import os
import pickle
import threading
import time
import numpy as np
from flask import Flask, jsonify, request, render_template
from model import KilnModel
from kiln import KilnAgent

app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend/static')

# Global Simulation State
simulation_state = {
    "model": None,
    "status": "Not Initialized",
    "is_ready": False
}

def compute_histogram(data, bins=15):
    if not data:
        return {"labels": [], "data": [], "average": 0}
    counts, edges = np.histogram(data, bins=bins)
    average = float(np.mean(data)) if data else 0
    labels = [f"{int(edges[i])}-{int(edges[i+1])}" for i in range(len(edges)-1)]
    return {"labels": labels, "data": counts.tolist(), "average": average}

def init_worker(adoption, coal_price):
    """Background thread to initialize model"""
    global simulation_state
    
    def progress_callback(msg):
        simulation_state["status"] = msg
        print(msg) # Verify in console

    try:
        # Load population keys to determine tech adoption
        # Assuming synpop.pkl is in backend/
        with open("synpop.pkl", 'rb') as file: 
            synpop = pickle.load(file)
        
        all_ids = [k[0] for k in synpop.keys()]
        target_tech_count = int(len(all_ids) * adoption)
        
        if target_tech_count > 0:
            kilns_to_tech = np.random.choice(all_ids, target_tech_count, replace=False).tolist()
        else:
            kilns_to_tech = []
        
        # Initialize Model
        simulation_state["model"] = KilnModel(
            tech=True, 
            kilns_to_tech=kilns_to_tech, 
            coal=coal_price,
            machine_bricks=0.5,
            progress_callback=progress_callback
        )
        
        simulation_state["status"] = "Ready"
        simulation_state["is_ready"] = True
        
    except Exception as e:
        simulation_state["status"] = f"Error: {str(e)}"
        print(f"Error initializing: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_simulation', methods=['POST'])
def init_simulation():
    global simulation_state
    
    # Reset state if exists
    simulation_state["model"] = None
    simulation_state["is_ready"] = False
    simulation_state["status"] = "Starting initialization..."
    
    params = request.get_json()
    adoption = float(params.get('adoption', 0))
    coal_price = float(params.get('coal_price', 4.61))
    
    # Start background thread
    thread = threading.Thread(target=init_worker, args=(adoption, coal_price))
    thread.start()
    
    return jsonify({"message": "Initialization started"})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": simulation_state["status"],
        "ready": simulation_state["is_ready"]
    })

@app.route('/step', methods=['POST'])
def step_simulation():
    if not simulation_state["model"]:
        return jsonify({"error": "Model not initialized"}), 400
    
    model = simulation_state["model"]
    
    # Run loop to approximate 20,000 agent steps
    # We count how many relevant agents are in the model to determine loops
    # Kilns + Buyers
    num_agents = len(model.agents_by_type[KilnAgent]) + len(model.agents_by_type[KilnAgent]) # Wait, KilnAgent + BuyerAgent?
    # Correcting:
    # We can't easily access BuyerAgent class without import, but model has them in agents_by_type
    # Just count the ones we shuffle in step()
    
    # We can invoke model.step() repeatedly. 
    # If 1 model step = N agent steps (where N is total agents),
    # Then we need 20,000 / N model steps.
    # If N=1000, we need 20 steps.
    
    # Rough estimate of steps to run
    agent_count = sum(len(agents) for agent_type, agents in model.agents_by_type.items() if "KilnAgent" in str(agent_type) or "BuyerAgent" in str(agent_type))
    
    if agent_count == 0: agent_count = 1000 # Safety fallback
    
    target_agent_steps = 20000
    model_steps_needed = max(1, int(target_agent_steps / agent_count))
    
    # Run the steps
    for _ in range(model_steps_needed):
        model.step()
    
    # Extract Data
    hand_prices, machine_prices = [], []
    hand_prod, machine_prod = [], []
    hand_profit, machine_profit = [], []
    
    for kiln in model.agents_by_type[KilnAgent]:
        is_machine = kiln.kiln_tech in ["Two-Roller", "Four-Roller"]
        if is_machine:
            machine_prices.append(kiln.sale_price)
            machine_prod.append(kiln.bricks_made)
            machine_profit.append(kiln.total_profit)
        else:
            hand_prices.append(kiln.sale_price)
            hand_prod.append(kiln.bricks_made)
            hand_profit.append(kiln.total_profit)
            
    return jsonify({
        "price": { "hand": compute_histogram(hand_prices), "machine": compute_histogram(machine_prices) },
        "production": { "hand": compute_histogram(hand_prod), "machine": compute_histogram(machine_prod) },
        "profit": { "hand": compute_histogram(hand_profit), "machine": compute_histogram(machine_profit) },
        "status": f"Step {model.steps_total if hasattr(model, 'steps_total') else 'Unknown'}" # Mesa 3+ might not have steps_total in base? Usually model.schedule.steps
    })

@app.route('/reset', methods=['POST'])
def reset_simulation():
    global simulation_state
    simulation_state["model"] = None
    simulation_state["status"] = "Not Initialized"
    simulation_state["is_ready"] = False
    return jsonify({"message": "Reset complete"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)