#!/usr/bin/env python3
"""OM1 Charity Donation Trigger Script"""

import sys
import webbrowser
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import subprocess

app = Flask(__name__)
CORS(app)

donation_data = None
http_server_process = None

def start_http_server():
    """Start simple HTTP server for web UI"""
    global http_server_process
    try:
        # Check if server already running
        response = requests.get('http://localhost:8080', timeout=1)
        print("   ✅ HTTP server already running")
        return True
    except:
        # Start new server
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        http_server_process = subprocess.Popen(
            ['python3', '-m', 'http.server', '8080'],
            cwd=base_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1)
        print("   ✅ Started HTTP server on port 8080")
        return True

def open_donation_ui(amount, charity):
    url = f"http://localhost:8080/src/web_ui/charity_donation.html?amount={amount}&charity={charity}"
    
    print(f"\n🌐 Opening donation page...")
    print(f"   Amount: ${amount}")
    print(f"   Program: {charity}")
    print(f"   URL: {url}")
    
    # Start HTTP server if needed
    start_http_server()
    
    # Open browser
    webbrowser.open(url)
    return url

@app.route('/donation_complete', methods=['POST', 'OPTIONS'])
def donation_complete():
    global donation_data
    
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    donation_data = data
    
    print(f"\n✅ DONATION COMPLETED!")
    print(f"   TX Hash: {data['tx_hash']}")
    print(f"   Amount: ${data['amount']} USD")
    print(f"   Program: {data['charity']}")
    
    return jsonify({'status': 'success'})

def run_webhook_server():
    print("\n🎧 OM1 webhook listener: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 OM1 API CREDIT GIFT PROGRAM")
    print("="*60)
    
    amount = sys.argv[1] if len(sys.argv) > 1 else '10'
    charity = sys.argv[2] if len(sys.argv) > 2 else 'credit_gift'
    
    server_thread = threading.Thread(target=run_webhook_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    open_donation_ui(amount, charity)
    
    print(f"\n⏳ Waiting for ${amount} credit gift donation...")
    
    try:
        while donation_data is None:
            time.sleep(1)
        
        print("\n" + "="*60)
        print("🎉 CREDIT GIFT COMPLETE!")
        print("="*60)
        print(f"\nTX: {donation_data['tx_hash']}")
        print(f"Etherscan: https://sepolia.etherscan.io/tx/{donation_data['tx_hash']}")
        print("\n✅ Developers will receive API credits\n")
        
    except KeyboardInterrupt:
        print("\n⚠️  Cancelled\n")
        if http_server_process:
            http_server_process.terminate()
        sys.exit(0)
