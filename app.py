import os
import pickle
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # required if you use session later

# ======= Directories =======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')

# Ensure model directory exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# ======= Helper: Load Model =======
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

# ======= Routes =======
@app.route('/')
def index():
    model_files = []
    if os.path.exists(MODEL_DIR):
        all_files = os.listdir(MODEL_DIR)
        model_files = [f.replace('.pkl', '') for f in all_files if f.endswith('.pkl')]
    return render_template('stock.html', stock_list=model_files)

@app.route('/predict', methods=['POST'])
def predict():
    stock_name = request.form.get('stock_name', '').upper()
    input_dict = request.form.to_dict()  # Convert MultiDict to normal dict
    
    # Validate and convert input fields
    try:
        input_data = [
            float(input_dict.get('prev_close', 0)),
            float(input_dict.get('open', 0)),
            float(input_dict.get('high', 0)),
            float(input_dict.get('low', 0)),
            float(input_dict.get('last', 0)),
            float(input_dict.get('close', 0)),
            float(input_dict.get('vwap', 0)),
            float(input_dict.get('volume', 0)),
            float(input_dict.get('turnover', 0))
        ]
    except (ValueError, TypeError):
        return render_template('prediction.html', 
                               stock_name=stock_name,
                               error_message="Invalid input: all fields must be numbers.",
                               input_data=input_dict), 400

    model = load_model(stock_name)
    if not model:
        return render_template('prediction.html', 
                               stock_name=stock_name,
                               error_message=f"Model for {stock_name} not found.",
                               input_data=input_dict), 404

    try:
        features = np.array([input_data])
        prediction_output = model.predict(features)[0]
        if len(prediction_output) < 6:
            return render_template('prediction.html', 
                                   stock_name=stock_name,
                                   error_message="Model output shape mismatch.",
                                   input_data=input_dict), 500
        
        results = {
            'Open': round(float(prediction_output[0]), 2),
            'High': round(float(prediction_output[1]), 2),
            'Low': round(float(prediction_output[2]), 2),
            'Last': round(float(prediction_output[3]), 2),
            'Close': round(float(prediction_output[4]), 2),
            'VWAP': round(float(prediction_output[5]), 2)
        }
        return render_template('prediction.html',
                               stock_name=stock_name,
                               prediction=results,
                               input_data=input_dict)

    except Exception as e:
        print(f"Prediction error: {e}")
        return render_template('prediction.html', 
                               stock_name=stock_name,
                               error_message=f"Prediction failed: {e}",
                               input_data=input_dict), 500

# ======= Run App =======
if __name__ == '__main__':
    app.run(debug=True)
