import os
import pickle
import threading
import time
import numpy as np
from flask import Flask, jsonify, request, render_template
from model import KilnModel
from kiln import KilnAgent
from buyer import BuyerAgent

app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend/static')

# Global Simulation State
simulation_state = {
    "model": None,
    "status": "Not Initialized",
    "is_ready": False,
    "current_step": 0
}

def compute_histogram(data, bins=15, fixed_bins=None):
    if not data:
        return {"labels": [], "data": [], "average": 0}
    
    # Use fixed bins if provided (e.g. for Production)
    if fixed_bins is not None:
        counts, edges = np.histogram(data, bins=fixed_bins)
    else:
        counts, edges = np.histogram(data, bins=bins)
        
    average = float(np.mean(data)) if data else 0
    
    # Format labels as single numbers (midpoint of bin)
    labels = []
    for i in range(len(edges)-1):
        midpoint = (edges[i] + edges[i+1]) / 2
        # If numbers are large (like production), format nicely
        if midpoint > 1000:
            labels.append(f"{int(midpoint/1000)}k")
        else:
            labels.append(f"{int(midpoint)}")
    
    return {"labels": labels, "data": counts.tolist(), "average": average}

def init_worker(adoption, coal_price, machine_demand):
    """Background thread to initialize model"""
    global simulation_state
    
    def progress_callback(msg):
        simulation_state["status"] = msg
        print(msg) 

    try:
        with open("synpop.pkl", 'rb') as file: 
            synpop = pickle.load(file)
        
        all_ids = [k[0] for k in synpop.keys()]
        # Adoption is 0-1, maps to percentage of total kilns
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
            machine_bricks=machine_demand, # New parameter 0-1
            progress_callback=progress_callback
        )
        
        simulation_state["status"] = "Ready"
        simulation_state["is_ready"] = True
        simulation_state["current_step"] = 0
        
    except Exception as e:
        simulation_state["status"] = f"Error: {str(e)}"
        print(f"Error initializing: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_simulation', methods=['POST'])
def init_simulation():
    global simulation_state
    
    # Reset state
    simulation_state["model"] = None
    simulation_state["is_ready"] = False
    simulation_state["current_step"] = 0
    simulation_state["status"] = "Starting initialization..."
    
    params = request.get_json()
    adoption = float(params.get('adoption', 0))
    coal_price = float(params.get('coal_price', 4.61))
    machine_demand = float(params.get('machine_demand', 0.0))
    
    thread = threading.Thread(target=init_worker, args=(adoption, coal_price, machine_demand))
    thread.start()
    
    return jsonify({"message": "Initialization started"})

@app.route('/status', methods=['GET'])
def get_status():
    agent_count = 0
    if simulation_state["model"]:
        model = simulation_state["model"]
        kilns = len(model.agents_by_type[KilnAgent])
        buyers = len(model.agents_by_type[BuyerAgent])
        agent_count = kilns + buyers

    return jsonify({
        "status": simulation_state["status"],
        "ready": simulation_state["is_ready"],
        "step": simulation_state["current_step"],
        "agent_count": agent_count
    })

@app.route('/step', methods=['POST'])
def step_simulation():
    if not simulation_state["model"]:
        return jsonify({"error": "Model not initialized"}), 400
    
    model = simulation_state["model"]
    
    # Execute steps
    model.step()
    simulation_state["current_step"] = model.step_count
    
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
    
    hand_prod_bins = np.linspace(0, 10000, 15) 
    machine_prod_bins = np.linspace(0, 1500000, 15)

    # Calculate agent counts
    kiln_count = len(model.agents_by_type[KilnAgent])
    buyer_count = len(model.agents_by_type[BuyerAgent])
    total_active_agents = kiln_count + buyer_count

    return jsonify({
        "price": { 
            "hand": compute_histogram(hand_prices), 
            "machine": compute_histogram(machine_prices) 
        },
        "production": { 
            "hand": compute_histogram(hand_prod, fixed_bins=hand_prod_bins), 
            "machine": compute_histogram(machine_prod, fixed_bins=machine_prod_bins) 
        },
        "profit": { 
            "hand": compute_histogram(hand_profit), 
            "machine": compute_histogram(machine_profit) 
        },
        "step": model.step_count,
        # Return how many agents actually stepped this day
        "agents_stepped": model.agents_stepped,
        "total_agents": total_active_agents
    })

@app.route('/reset', methods=['POST'])
def reset_simulation():
    global simulation_state
    simulation_state["model"] = None
    simulation_state["status"] = "Not Initialized"
    simulation_state["is_ready"] = False
    simulation_state["current_step"] = 0
    return jsonify({"message": "Reset complete"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)