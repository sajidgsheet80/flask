from flask import Flask, render_template, request, jsonify
import requests
import hmac
import hashlib
import json
import time

app = Flask(__name__)

# --- Your CoinDCX API credentials ---
API_KEY = "07cc5afaa216e1"
API_SECRET = "d6677cbcb7025b18a3bcbe62e5e933956"

@app.route('/')
def index():
    # fetch all tickers for dropdown
    url = "https://api.coindcx.com/exchange/ticker"
    response = requests.get(url)
    tickers = []
    if response.status_code == 200:
        tickers = sorted([item['market'] for item in response.json()])
    return render_template('index.html', tickers=tickers)

@app.route('/get_ticker', methods=['POST'])
def get_ticker():
    market = request.form.get('market', '').strip().upper()
    if not market:
        return jsonify({"error": "Market is required."}), 400

    try:
        url = "https://api.coindcx.com/exchange/ticker"
        response = requests.get(url)
        data = response.json()
        ticker_info = next((item for item in data if item['market'] == market), None)

        if not ticker_info:
            return jsonify({"error": f"No data found for market '{market}'"}), 404

        return jsonify({
            "market": market,
            "last_price": float(ticker_info['last_price']),
            "high": float(ticker_info['high']),
            "low": float(ticker_info['low']),
            "volume": float(ticker_info['volume']),
            "price_change": float(ticker_info.get('price_change_percent', 0.0))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        market = request.form.get('market', '').strip().upper()
        side = request.form.get('side', 'buy')
        order_type = request.form.get('order_type', 'limit_order')
        quantity = float(request.form.get('quantity', 0.001))
        price = float(request.form.get('price_per_unit', 0)) if order_type == 'limit_order' else None

        timestamp = int(time.time() * 1000)
        order_data = {
            "side": side,
            "order_type": order_type,
            "market": market,
            "total_quantity": quantity,
            "timestamp": timestamp,
            "client_order_id": f"{side}-{timestamp}"
        }
        if price:
            order_data["price_per_unit"] = price

        json_body = json.dumps(order_data, separators=(',', ':'))
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            json_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': API_KEY,
            'X-AUTH-SIGNATURE': signature
        }

        url = "https://api.coindcx.com/exchange/v1/orders/create"
        response = requests.post(url, data=json_body, headers=headers)
        return jsonify(response.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/market_rules', methods=['GET'])
def market_rules():
    try:
        url = "https://api.coindcx.com/exchange/v1/markets_details"
        response = requests.get(url)
        data = response.json()
        market_info = {item['market']: item for item in data}
        return jsonify(market_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
