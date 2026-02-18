import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash,check_password_hash
app = Flask(__name__)
from db import get_db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')
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
    model_path = os.path.join(MODEL_DIR, f'{stock_name.lower()}.pkl')
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading model {stock_name}: {e}")
        return None
@app.route('/')
def index():
    model_files = []
    
    
    print("--- MODEL LOADING DEBUG ---")
    print(f"1. Flask running from: {BASE_DIR}")
    print(f"2. Expected model directory path: {MODEL_DIR}")
    
    try:
        if not os.path.exists(MODEL_DIR):
            print("3. ERROR: The 'trained_models' directory does NOT exist at the expected path!")
        else:
            print("3. SUCCESS: The 'trained_models' directory exists.")
            all_files = os.listdir(MODEL_DIR)
            model_files = [f.replace('.pkl', '') for f in all_files if f.endswith('.pkl')]
            if model_files:
                print(f"4. Found models: {model_files}")
            else:
                print("4. WARNING: Directory exists, but no .pkl files were found inside.")
            
    except Exception as e:
        print(f"5. FATAL ERROR: An error occurred while listing models: {e}")
        model_files = []
        
    print("--- END DEBUG ---")
    return render_template('stock.html', stock_list=model_files)
@app.route('/predict', methods=['POST'])
def predict():
    stock_name = request.form.get('stock_name')
    try:
        input_data = [
            float(request.form['prev_close']),
            float(request.form['open']),
            float(request.form['high']),
            float(request.form['low']),
            float(request.form['last']),
            float(request.form['close']),
            float(request.form['vwap']),
            float(request.form['volume']),
            float(request.form['turnover'])
        ]
    except (ValueError, TypeError):
        return render_template('prediction.html', stock_name=stock_name, error_message='Invalid input data. All fields must be valid numbers.'), 400
    model = load_model(stock_name)
    if not model:
        return render_template('prediction.html', stock_name=stock_name, error_message=f'Model for {stock_name.upper()} not found or failed to load.'), 404
    try:
        features = np.array([input_data])
        prediction_output = model.predict(features)[0] 
        results = {
            'Open': round(float(prediction_output[0]), 2),
            'High': round(float(prediction_output[1]), 2),
            'Low': round(float(prediction_output[2]), 2),
            'Last': round(float(prediction_output[3]), 2),
            'Close': round(float(prediction_output[4]), 2),
            'VWAP': round(float(prediction_output[5]), 2)
        }
        return render_template('prediction.html', 
                               stock_name=stock_name.upper(), 
                               prediction=results,
                               input_data=request.form)

    except Exception as e:
        print(f"Prediction error: {e}")
        return render_template('prediction.html', stock_name=stock_name, error_message=f'Prediction processing failed: {e}'), 500

if __name__ == '__main__':
    if not os.path.exists(MODEL_DIR):
        print(f"Creating model directory: {MODEL_DIR}")
        os.makedirs(MODEL_DIR)  # <-- yahi missing tha, "is" nahi
    else:
        print(f"Model directory already exists: {MODEL_DIR}")
    app.run(debug=True)

