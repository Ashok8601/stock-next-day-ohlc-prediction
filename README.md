# Stock OHLC Predictor

## Overview
**Stock OHLC Predictor** is a web-based application that predicts the **Next-Day OHLC (Open, High, Low, Close) prices** for stocks from the **Nifty 50 index**. The models are trained on **historical stock data spanning 20 years**. Users can interactively select any stock from the Nifty 50 list on the frontend and get the predicted prices for the next trading day.

The project is implemented as a **Flask web application**, with **separate HTML, CSS, and JavaScript files** for a clean, responsive user interface.

---

## Features
- Predicts **next-day OHLC prices** for Nifty 50 stocks.
- Users can select the stock of their choice via a **dynamic web interface**.
- Models are trained on **20 years of historical stock data** for accuracy.
- **Flask web app** with modular HTML, CSS, and JS structure.
- Smooth and interactive user experience with **dynamic input forms**.
- **Versioned project** for reproducibility (`v1.0`).
- Easily extensible for adding **more stocks or advanced ML models**.

---

## Tech Stack
- **Python 3.x**
- **Flask** – Web framework for backend
- **Pickle** – Model serialization for each stock
- **NumPy** – Array manipulation for model inputs
- **HTML / CSS / JavaScript** – Frontend interface
- **Kaggle dataset** – Historical Nifty 50 stock data (20 years)

---

## Dataset
- **Source:** Kaggle / Yahoo Finance (historical stock data)
- **Coverage:** Nifty 50 stocks, last 20 years
- **Columns used:** `Prev Close, Open, High, Low, Last, Close, VWAP, Volume, Turnover`
- Data preprocessing steps:
  - Missing value handling
  - Log-transform for skewed features
  - Outlier removal
  - Column normalization (as needed)

---

## Installation
1. Clone the repository:
```bash
git clone https://github.com/Ashok8601/stock-next-day-ohlc-prediction.git
cd stock-next-day-ohlc-prediction

## 2nd Create and activate vertual envoirenment
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

## 3rd Install dependency
pip install -r requirements.txt

4th Run the flask app
python app.py

## 5th navigate url

## 6th Project Structure
stock-next-day-ohlc-prediction/
│
├─ app.py                  # Main Flask app
├─ models/                 # Pickle models for each Nifty 50 stock
├─ templates/
│   ├─ stock.html          # Stock selection + input form
│   └─ prediction.html     # Prediction results page
├─ static/
│   ├─ css/style.css       # Styles
│   └─ js/script.js        # Dynamic frontend logic
├─ venv/                   # Python virtual environment
└─ README.md               # Project documentation






