import os
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

# =========================
# Flask App Initialization
# =========================
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin requests

# =========================
# Directories & Constants
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')

# Ensure MODEL_DIR exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)
    print(f"[INFO] Created model directory at {MODEL_DIR}")

# =========================
# Load Available Model Function
# =========================
def load_model(stock_name: str):
    """
    Load a pickled model for the given stock_name.
    Returns the model object or None if failed.
    """
    model_path = os.path.join(MODEL_DIR, f'{stock_name.lower()}.pkl')
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"[ERROR] Failed to load model {stock_name}: {e}")
        return None

# =========================
# API: List Available Models
# =========================
@app.route('/models', methods=['GET'])
def list_models():
    """
    fOR Returns a JSON list of all available stock models.
    """
    try:
        if not os.path.exists(MODEL_DIR):
            return jsonify({"models": [], "message": "Model directory not found"}), 404

        model_files = [f.replace('.pkl', '') for f in os.listdir(MODEL_DIR) if f.endswith('.pkl')]
        return jsonify({"models": model_files}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to list models: {str(e)}"}), 500

# =========================
# API: For Predict Stock Prices
# =========================
@app.route('/predict', methods=['POST'])
def predict():
    """
    Expects JSON with stock_name and input features.
    Returns JSON with predicted OHLCVWAP values.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        stock_name = data.get('stock_name')
        required_fields = ['prev_close', 'open', 'high', 'low', 'last', 'close', 'vwap', 'volume', 'turnover']

        # INPUT VALIDATION
        input_data = []
        for field in required_fields:
            value = data.get(field)
            if value is None:
                return jsonify({"error": f"Missing field: {field}"}), 400
            try:
                input_data.append(float(value))
            except ValueError:
                return jsonify({"error": f"Invalid value for field: {field}. Must be a number."}), 400

        # MODEL LOADING
        model = load_model(stock_name)
        if not model:
            return jsonify({"error": f"Model for '{stock_name}' not found"}), 404

        # start prediction
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

        return jsonify({"stock": stock_name.upper(), "prediction": results}), 200

    except Exception as e:
        
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

# =========================
# Flask App Excution Code
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
