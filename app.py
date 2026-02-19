import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

# Import your DB helper
# Ensure db.py exists in the same directory
try:
    from db import get_db
except ImportError:
    def get_db():
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# ======= Helper Functions =======

def load_model(stock_name):
    """
    Attempts to find the model file by checking lowercase, 
    uppercase, and exact matches.
    """
    # Create a list of potential filenames to check
    names_to_check = [
        f"{stock_name.lower()}.pkl",
        f"{stock_name.upper()}.pkl",
        f"{stock_name}.pkl"
    ]
    
    for filename in names_to_check:
        model_path = os.path.join(MODEL_DIR, filename)
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return None

# ======= Routes =======

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Market Trend API is Running"
    })

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid data"}), 400
    
    fields = ["username", "name", "email", "password"]
    if not all(data.get(f) for f in fields):
        return jsonify({"error": "all fields are required"}), 400
    
    if len(data.get("password")) < 8:
        return jsonify({"error": "password should be 8 characters"}), 400
        
    hash_pass = generate_password_hash(data.get("password"))
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO user(name,username,email,password) VALUES(?,?,?,?)",
            (data.get("name"), data.get("username"), data.get("email"), hash_pass)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "user created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "email or username already exists"}), 409

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "all fields are required"}), 400 
    
    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE email=?", (data.get("email"),)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user["password"], data.get("password")):
        return jsonify({"error": "invalid credentials"}), 401
        
    return jsonify({
        "message": "login successful",
        "user": {"id": user["id"], "name": user["name"]}
    }), 200

@app.route('/select/stock', methods=["GET"])
def get_stocks():
    if not os.path.exists(MODEL_DIR):
        return jsonify({"status": "error", "message": "Model directory not found"}), 404  

    model_files = [f.replace('.pkl', '') for f in os.listdir(MODEL_DIR) if f.endswith('.pkl')]
    return jsonify({
        "status": "success",
        "count": len(model_files),
        "stocks": model_files
    }), 200

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or not data.get("stock_name"):
        return jsonify({"error": "Select stock name"}), 400
    
    stock_name = data.get("stock_name")
    
    # 1. Load Model
    model = load_model(stock_name)
    if model is None:
        return jsonify({
            "status": "error", 
            "message": f"Model for '{stock_name}' not found in {MODEL_DIR}"
        }), 404                                                        
    
    # 2. Prepare Features
    try:
        # Match these exactly to how your model was trained
        feature_list = [
            'prev_close', 'open', 'high', 'low', 'last', 'close', 'vwap', 'volume', 'turnover'
        ]
        input_values = [float(data.get(f, 0)) for f in feature_list]
        features = np.array([input_values])
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "All input fields must be numbers"}), 400
                              
    # 3. Predict
    try:
        prediction_output = model.predict(features)
        
        # Handle both [[]] (2D) and [] (1D) outputs
        if len(prediction_output.shape) > 1:
            pred = prediction_output[0]
        else:
            pred = prediction_output

        # Ensure we have enough columns in output (6 expected)
        if len(pred) < 6:
            return jsonify({"status": "error", "message": "Model output format unexpected"}), 500
                                          
        results = {
            'Open': round(float(pred[0]), 2),
            'High': round(float(pred[1]), 2),
            'Low': round(float(pred[2]), 2),
            'Last': round(float(pred[3]), 2),
            'Close': round(float(pred[4]), 2),
            'VWAP': round(float(pred[5]), 2)
        }
        return jsonify({
            "status": "success",
            "stock_name": stock_name.upper(),
            "prediction": results
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Prediction failed: {str(e)}"}), 500

@app.route('/profile',methods=["GET","POST"])
def user_profile():
    id=session.get("id")
    if not id:
        return jsonify({"user not logged in "}),401
    conn=get_db()
    user=conn.execute("SELECT * FROM user WHERE id=?",(id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error":"user not logged in "}),401
    return jsonify({"username":user["username"],"name":user["name"],"email":user["email"]}),200

@app.route('/reset_password',methods=["GET","POST"])
def reset_password():
    data=request.get_json()
    old_password=data.get("old_password")
    new_password=data.get("new_password")
    username=data.get("username")
    conn=get_db()
    id=session.get("id")
    if not id:
        return jsonify({"error":"user not logged in"}),401
    user=conn.execute("SELECT * FROM user WHERE id=?",(id,)).fetchone()
    conn.close()
    if not old_password or not new_password or not username:
        return jsonify({"error":"all field are required"}),400
    if not user["username"] != username or not check_password_hash(user["password"],old_password):
        return jsonify({"error":"username and old password not matched with record"})
    hashpassword=generate_password_hash(new_password)
    conn=get_db()
    conn.execute("UPDATE user SET password =? WHERE username =?",(hashpassword,username))
    conn.commit()
    conn.close()
    return jsonify({"message":"password updated successfully"})
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
        
