import os
import pickle
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 1. BASE_DIR को Flask app.py की वर्तमान डायरेक्टरी के रूप में परिभाषित करें
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# 2. मॉडल डायरेक्टरी को BASE_DIR के सापेक्ष बनाएं
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models') 

# 🛠️ एक फंक्शन जो स्टॉक मॉडल को लोड करेगा
def load_model(stock_name):
    """दिए गए स्टॉक नाम के लिए .pkl मॉडल लोड करता है।"""
    # model_path अब पूर्ण पथ (absolute path) का उपयोग करेगा
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

# 🌟 मुख्य रूट: स्टॉक सिलेक्शन पेज
@app.route('/')
def index():
    model_files = []
    
    # 🐞 डीबगिंग कोड
    print("--- MODEL LOADING DEBUG ---")
    print(f"1. Flask running from: {BASE_DIR}")
    print(f"2. Expected model directory path: {MODEL_DIR}")
    
    try:
        if not os.path.exists(MODEL_DIR):
            print("3. ERROR: The 'trained_models' directory does NOT exist at the expected path!")
        else:
            print("3. SUCCESS: The 'trained_models' directory exists.")
            
            # उपलब्ध मॉडलों की सूची प्राप्त करें
            all_files = os.listdir(MODEL_DIR)
            # केवल .pkl फ़ाइलें चुनें
            model_files = [f.replace('.pkl', '') for f in all_files if f.endswith('.pkl')]
            
            # 4. टर्मिनल में प्रिंट करके देखें कि क्या सूची मिल रही है
            if model_files:
                print(f"4. Found models: {model_files}")
            else:
                print("4. WARNING: Directory exists, but no .pkl files were found inside.")
            
    except Exception as e:
        print(f"5. FATAL ERROR: An error occurred while listing models: {e}")
        model_files = []
        
    print("--- END DEBUG ---")
    return render_template('stock.html', stock_list=model_files)

# 🚀 प्रेडिक्शन रूट: डेटा लेता है और प्रेडिक्शन दिखाता है
@app.route('/predict', methods=['POST'])
def predict():
    # 1. स्टॉक का नाम और इनपुट डेटा प्राप्त करें
    stock_name = request.form.get('stock_name')
    
    # आवश्यक इनपुट फ़ील्ड: 'Prev Close','Open','High','Low','Last','Close','VWAP','Volume','Turnover'
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

    # 2. मॉडल लोड करें
    model = load_model(stock_name)
    if not model:
        return render_template('prediction.html', stock_name=stock_name, error_message=f'Model for {stock_name.upper()} not found or failed to load.'), 404

    # 3. प्रेडिक्शन करें
    try:
        features = np.array([input_data])
        prediction_output = model.predict(features)[0] 
        
        # 4. आउटपुट को HTML में दिखाने के लिए तैयार करें (6 फीचर्स)
        results = {
            'Open': round(float(prediction_output[0]), 2),
            'High': round(float(prediction_output[1]), 2),
            'Low': round(float(prediction_output[2]), 2),
            'Last': round(float(prediction_output[3]), 2),
            'Close': round(float(prediction_output[4]), 2),
            'VWAP': round(float(prediction_output[5]), 2)
        }
        
        # prediction.html को प्रेडिक्शन रिजल्ट के साथ रेंडर करें
        return render_template('prediction.html', 
                               stock_name=stock_name.upper(), 
                               prediction=results,
                               input_data=request.form)

    except Exception as e:
        print(f"Prediction error: {e}")
        return render_template('prediction.html', stock_name=stock_name, error_message=f'Prediction processing failed: {e}'), 500

if __name__ == '__main__':
    # सुनिश्चित करें कि मॉडल डायरेक्टरी मौजूद है
    if not os.path.exists(MODEL_DIR):
        print(f"Creating model directory: {MODEL_DIR}")
        os.makedirs(MODEL_DIR)
        
    app.run(debug=True)