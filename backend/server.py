import os
import pickle
import numpy as np
from flask import Flask, jsonify, request, render_template
from model import KilnModel
from kiln import KilnAgent

# Initialize Flask
# We explicitly tell Flask where the frontend folder is located relative to this script
app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend/static')

def compute_histogram(data, bins=15):
    """Helper to bin data for Chart.js"""
    if not data:
        return {"labels": [], "data": [], "average": 0}
    
    counts, edges = np.histogram(data, bins=bins)
    average = float(np.mean(data)) if data else 0
    
    # Format labels as ranges (e.g., "10-20")
    labels = [f"{int(edges[i])}-{int(edges[i+1])}" for i in range(len(edges)-1)]
    
    return {
        "labels": labels,
        "data": counts.tolist(),
        "average": average
    }

@app.route('/')
def index():
    """Serves the main dashboard page"""
    return render_template('index.html')

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    # Get JSON data from the frontend
    params = request.get_json()
    adoption = float(params.get('adoption', 0))
    coal_price = float(params.get('coal_price', 4.61))
    
    print(f"Running sim with Adoption: {adoption}, Coal: {coal_price}")

    # Load population keys to determine tech adoption
    # Ensure synpop.pkl is in the backend directory
    try:
        with open("synpop.pkl", 'rb') as file: 
            synpop = pickle.load(file)
    except FileNotFoundError:
        return jsonify({"error": "synpop.pkl not found in backend directory"}), 500
    
    all_ids = [k[0] for k in synpop.keys()]
    
    # Logic for adoption slider (0.0 to 1.0)
    target_tech_count = int(len(all_ids) * adoption)
    
    # Randomly select which kilns get the tech upgrade
    if target_tech_count > 0:
        kilns_to_tech = np.random.choice(all_ids, target_tech_count, replace=False).tolist()
    else:
        kilns_to_tech = []
    
    # Initialize Model
    # NOTE: Ensure your KilnModel in model.py accepts these arguments!
    model = KilnModel(
        tech=True, 
        kilns_to_tech=kilns_to_tech, 
        coal=coal_price,
        machine_bricks=0.5 
    )
    
    # Run for 3 steps (months) to generate data
    for _ in range(3):
        model.step()
        
    # Extract Data for Histograms
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
            
    # Return JSON response
    return jsonify({
        "price": {
            "hand": compute_histogram(hand_prices),
            "machine": compute_histogram(machine_prices)
        },
        "production": {
            "hand": compute_histogram(hand_prod),
            "machine": compute_histogram(machine_prod)
        },
        "profit": {
            "hand": compute_histogram(hand_profit),
            "machine": compute_histogram(machine_profit)
        }
    })

if __name__ == '__main__':
    # Run the server
    app.run(debug=True, port=5000)