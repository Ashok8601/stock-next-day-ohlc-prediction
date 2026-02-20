import os
import pickle
import sqlite3
import numpy as np
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "ashokkumaryadav"
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

def get_db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db()
conn.execute("""
CREATE TABLE IF NOT EXISTS user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")
conn.commit()
conn.close()

def load_model(stock_name):
    names_to_check = [f"{stock_name.lower()}.pkl", f"{stock_name.upper()}.pkl", f"{stock_name}.pkl"]
    for filename in names_to_check:
        model_path = os.path.join(MODEL_DIR, filename)
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
    return None

@app.route("/")
def home():
    return jsonify({"status": "success", "message": "Market Trend API is Running"})

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data or not all(data.get(f) for f in ["username", "name", "email", "password"]):
        return jsonify({"error": "all fields are required"}), 400
    if len(data.get("password")) < 8:
        return jsonify({"error": "password should be 8 characters"}), 400
    hash_pass = generate_password_hash(data.get("password"))
    conn = get_db()
    try:
        conn.execute("INSERT INTO user(name,username,email,password) VALUES(?,?,?,?)",
                     (data.get("name"), data.get("username"), data.get("email"), hash_pass))
        conn.commit()
        return jsonify({"message": "user created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "email or username already exists"}), 409
    finally:
        conn.close()

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
    session['user_id'] = user['id']
    session['username'] = user['username']
    return jsonify({"message": "login successful", "user": {"id": user["id"], "name": user["name"]}}), 200

@app.route("/profile", methods=["GET"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"username": user["username"], "name": user["name"], "email": user["email"]}), 200

@app.route("/reset_password", methods=["POST"])
def reset_password():
    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    username = data.get("username")
    if not old_password or not new_password or not username:
        return jsonify({"error": "All fields are required"}), 400
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    if user["username"] != username or not check_password_hash(user["password"], old_password):
        conn.close()
        return jsonify({"error": "Username or old password not matched"}), 400
    hashpassword = generate_password_hash(new_password)
    conn.execute("UPDATE user SET password=? WHERE id=?", (hashpassword, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Password updated successfully"}), 200

@app.route("/select/stock", methods=["GET"])
def get_stocks():
    if not os.path.exists(MODEL_DIR):
        return jsonify({"status": "error", "message": "Model directory not found"}), 404
    model_files = [f.replace('.pkl', '') for f in os.listdir(MODEL_DIR) if f.endswith('.pkl')]
    return jsonify({"status": "success", "count": len(model_files), "stocks": model_files}), 200

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data or not data.get("stock_name"):
        return jsonify({"error": "Select stock name"}), 400
    stock_name = data.get("stock_name")
    model = load_model(stock_name)
    if model is None:
        return jsonify({"status": "error", "message": f"Model for '{stock_name}' not found"}), 404
    try:
        feature_list = ['prev_close', 'open', 'high', 'low', 'last', 'close', 'vwap', 'volume', 'turnover']
        input_values = [float(data.get(f, 0)) for f in feature_list]
        features = np.array([input_values])
        prediction_output = model.predict(features)
        if len(prediction_output.shape) > 1:
            pred = prediction_output[0]
        else:
            pred = prediction_output
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
        return jsonify({"status": "success", "stock_name": stock_name.upper(), "prediction": results}), 200
    except:
        return jsonify({"status": "error", "message": "Prediction failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)

