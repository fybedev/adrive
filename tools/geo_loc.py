from flask import (
    Blueprint,
    app,
    redirect,
    request,
    render_template,
    jsonify
)
import requests

geo_loc_bp = Blueprint('geo_loc', __name__)

@geo_loc_bp.route('/get-location')
def get_location():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if user_ip and ',' in user_ip:
        user_ip = user_ip.split(',')[0].strip()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        }
        
        response = requests.get(
            f'http://ip-api.com/json/{user_ip}', 
            headers=headers, 
            timeout=5
        )
        
        data = response.json()
        
        if data.get('status') == 'success':
            return jsonify({
                "status": "success",
                "city": data.get('city'),
                "country": data.get('country')
            })
        else:
            print(f"API Error Message: {data.get('message')}")
            
    except Exception as e:
        print(f"Python Request Failed: {e}")
    
    return jsonify({"status": "fail", "city": "Unknown", "country": "Location"})

@geo_loc_bp.route('/check-ip')
def check_ip():
    return {
        "remote_addr": request.remote_addr,
        "x_forwarded_for": request.headers.get('X-Forwarded-For'),
        "actual_ip_used": request.headers.get('X-Forwarded-For', request.remote_addr)
    }