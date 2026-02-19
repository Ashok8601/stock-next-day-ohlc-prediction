import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

app = Flask(__name__)
from flask_cors import CORS
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

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

    username = data.get("username")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not email or not username or not password or not name:
        return jsonify({"error": "all fields are required"}), 400

    if len(password) < 8:
        return jsonify({"error": "password should be 8 characters"}), 400

    hash_pass = generate_password_hash(password)

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO user(name,username,email,password) VALUES (?,?,?,?)",
            (name, username, email, hash_pass),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "user created successfully"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "email already exists"}), 409

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid json data"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "all fields are required"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "email or password incorrect"}), 400

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "password incorrect"}), 400

    return jsonify({
        "message": "login successful",
        "user": {
            "id": user["id"],
            "name": user["name"]
        }
    }), 200

def load_model(stock_name):
    try:
        for file in os.listdir(MODEL_DIR):
            if file.lower() == f"{stock_name.lower()}.pkl":
                with open(os.path.join(MODEL_DIR, file), "rb") as f:
                    return pickle.load(f)
        return None
    except Exception as e:
        print("Model loading error:", e)
        return None
@app.route("/select/stock", methods=["GET"])
def get_stocks():
    if not os.path.exists(MODEL_DIR):
        return jsonify({
            "status": "error",
            "message": "Model directory not found"
        }), 404

    all_files = os.listdir(MODEL_DIR)
    model_files = [f.replace(".pkl", "") for f in all_files if f.endswith(".pkl")]

    return jsonify({
        "status": "success",
        "count": len(model_files),
        "stocks": model_files
    }), 200

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid json"}), 400

    stock_name = data.get("stock_name")
    if not stock_name:
        return jsonify({"error": "Select stock name"}), 400

    stock_name = stock_name.upper()

    try:
        input_data = [
            float(data.get("prev_close", 0)),
            float(data.get("open", 0)),
            float(data.get("high", 0)),
            float(data.get("low", 0)),
            float(data.get("last", 0)),
            float(data.get("close", 0)),
            float(data.get("vwap", 0)),
            float(data.get("volume", 0)),
            float(data.get("turnover", 0))
        ]
    except:
        return jsonify({
            "status": "error",
            "message": "All input fields must be numbers"
        }), 400

    model = load_model(stock_name)
    if model is None:
        return jsonify({
            "status": "error",
            "message": f"model for {stock_name} not found"
        }), 404

    try:
        features = np.array([input_data])
        prediction_output = model.predict(features)[0]

        if len(prediction_output) < 6:
            return jsonify({
                "status": "error",
                "message": "model output size mismatch"
            }), 500

        results = {
            "Open": round(float(prediction_output[0]), 2),
            "High": round(float(prediction_output[1]), 2),
            "Low": round(float(prediction_output[2]), 2),
            "Last": round(float(prediction_output[3]), 2),
            "Close": round(float(prediction_output[4]), 2),
            "VWAP": round(float(prediction_output[5]), 2)
        }

        return jsonify({
            "status": "success",
            "stock_name": stock_name,
            "prediction": results
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"prediction failed: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
