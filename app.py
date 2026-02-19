import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash,check_password_hash
app = Flask(__name__)
from flask_cors import CORS
CORS(app)
from db import get_db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)
    

# ======= Routes =======
@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Market Trend API is Running"
    })

    
@app.route("/signup",methods=["GET","POST"])
def signup():
    data=request.get_json()
    if not data:
        return jsonify({"error":"invalid data "}),400
    username=data.get("username")
    name=data.get("name")
    email=data.get("email")
    password=data.get("password")
    if not email or  not username or not password or not name:
        return jsonify({"error":"all fild are recqiured"})
    elif len(password)<8:
        return jsonify({"error":"password should be 8 charecter"})
    hash_pass=generate_password_hash(password)
    try:
        conn=get_db()
        conn.execute("INSERT INTO user(name,username,email,password)VALUES(?,?,?,?)",(name,username,email,hash_pass))
        conn.commit()
        conn.close()
        return jsonify({"message":"user created successfully "}),200
    except sqlite3.IntegrityError:
        return jsonify({"error":"email already exists"}),209
    
@app.route("/login",methods=["GET","POST"])
def login():
    data=request.get_json()
    if not data:
        return jsonify({"error":"invalid json data"}),400
    email=data.get("email")
    password=data.get("password")
    if not email or not password:
        return jsonify({"error":"all field are recquired "}),400 
    conn =get_db()
    user=conn.execute("SELECT * FROM user WHERE email=?",(email,) ).fetchone()
    conn.close()
    if not user:
        return jsonify({"error":"email or password incorect "}),400
    if not check_password_hash(user["password"],password):
        return jsonify({"error":"password incorect"}),400
    return jsonify({"message":"login successfull","user":{
        "id":user["id"],
        "name":user["name"]
        }}),200
    
    
def load_model(stock_name):
    model_path = os.path.join(MODEL_DIR, f"{stock_name.lower()}.pkl")
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except FileNotFoundError:
        print(f"Model not found: {model_path}")
        return None
    except Exception as e:
        print(f"Error loading model {stock_name}: {e}")
        return None

@app.route('/select/stock', methods=["GET"])
def get_stocks():
    if not os.path.exists(MODEL_DIR):
        return jsonify({
            "status": "error",
            "message": "Model directory not found"
        }), 404  

    all_files = os.listdir(MODEL_DIR)
    model_files = [
        f.replace('.pkl', '')
        for f in all_files
        if f.endswith('.pkl')
    ]

    return jsonify({
        "status": "success",
        "count": len(model_files),
        "stocks": model_files
    }), 200

@app.route('/predict', methods=['POST'])
def predict():
    data=request.get_json()
    if not data:
    	return jsonify({"error":"invalid json"}),400
    stock_name = data.get("stock_name")
    if not stock_name:
    	return jsonify({"error":"Select stock name"}),400
    	
    stock_name=stock_name.upper()
   
   
    try:
        input_data = [
            float(data.get('prev_close', 0)),
            float(data.get('open', 0)),
            float(data.get('high', 0)),
            float(data.get('low', 0)),
            float(data.get('last', 0)),
            float(data.get('close', 0)),
            float(data.get('vwap', 0)),
            float(data.get('volume', 0)),
            float(data.get('turnover', 0))
        ]
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "All input fields must be numbers"
        }), 400
                               
    model = load_model(stock_name)
    if model is None:
        return jsonify({"status":"error","message":f"model  for {stock_name} not found"}),404                                                        
                              
    try:
        features = np.array([input_data])
        prediction_output = model.predict(features)[0]
        if len(prediction_output) < 6:
            return jsonify({"status":"error","message":"model output size mismatch"}),505
                                          
        results = {
            'Open': round(float(prediction_output[0]), 2),
            'High': round(float(prediction_output[1]), 2),
            'Low': round(float(prediction_output[2]), 2),
            'Last': round(float(prediction_output[3]), 2),
            'Close': round(float(prediction_output[4]), 2),
            'VWAP': round(float(prediction_output[5]), 2)
        }
        return jsonify({"status":"success","stock name":stock_name,"prediction":results}),200
    except Exception as e:
        return jsonify({"status":"error","message":f"prediction fail for {stock_name} :{str(e)}"}),500
# ======= Run App =======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
