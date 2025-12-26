from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
from werkzeug.utils import secure_filename
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

# API Keys
VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY')
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')

# Local blacklist for immediate detection
LOCAL_BLACKLIST = [
    'malicious.com',
    'phishing-site.com',
    'scam-website.net',
    'evil-domain.org',
    'dangerous-url.io',
    'testmalicious.com',
    'harmful-site.org'
]

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_qr_data(image_path):
    try:
        img = cv2.imread(image_path)
        decoded_objects = decode(img)
        if decoded_objects:
            results = []
            for obj in decoded_objects:
                results.append({
                    'data': obj.data.decode('utf-8'),
                    'type': obj.type,
                    'rect': {
                        'left': obj.rect.left,
                        'top': obj.rect.top,
                        'width': obj.rect.width,
                        'height': obj.rect.height
                    }
                })
            return results
        return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def check_local_blacklist(url):
    domain = urlparse(url).netloc.lower()
    for bad_domain in LOCAL_BLACKLIST:
        if bad_domain in domain:
            return {
                'is_safe': False,
                'details': {
                    'local_blacklist': {
                        'match': bad_domain,
                        'message': 'URL is in the local blacklist'
                    }
                }
            }
    return None

def check_virustotal(url):
    if not VIRUSTOTAL_API_KEY:
        return None
        
    headers = {'x-apikey': VIRUSTOTAL_API_KEY}
    try:
        response = requests.post(
            'https://www.virustotal.com/api/v3/urls',
            headers=headers,
            data={'url': url}
        )
        response.raise_for_status()
        analysis_id = response.json()['data']['id']
        time.sleep(1)
        report_url = f'https://www.virustotal.com/api/v3/analyses/{analysis_id}'
        report = requests.get(report_url, headers=headers).json()
        
        if 'data' in report and 'attributes' in report['data']:
            stats = report['data']['attributes']['last_analysis_stats']
            return {
                'is_safe': stats['malicious'] == 0 and stats['suspicious'] == 0,
                'details': {'virustotal': stats}
            }
        return None
    except Exception as e:
        print(f"VirusTotal error: {e}")
        return None

def check_google_safebrowsing(url):
    if not GOOGLE_SAFE_BROWSING_API_KEY:
        return None
        
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    payload = {
        "client": {"clientId": "SecureQRScanner", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    
    try:
        response = requests.post(f"{endpoint}?key={GOOGLE_SAFE_BROWSING_API_KEY}", json=payload)
        response.raise_for_status()
        data = response.json()
        return {
            'is_safe': not bool(data.get('matches', [])),
            'details': {'google_safebrowsing': data}
        }
    except Exception as e:
        print(f"Google Safe Browsing error: {e}")
        return None

def check_phishing(url):
    """Custom phishing detection logic can be added here."""
    # Placeholder for a phishing detection model (e.g., ML-based classification)
    # Return an example result for now
    return {
        'is_safe': True,
        'details': {'phishing_check': 'No phishing behavior detected (placeholder)'}
    }

@app.route('/scan', methods=['POST'])
def scan_qr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        qr_data = extract_qr_data(filepath)
        os.remove(filepath)
        if qr_data:
            return jsonify({'results': qr_data})
        else:
            return jsonify({'error': 'No QR code found'}), 404
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/check-safety', methods=['POST'])
def check_safety():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return jsonify({'error': 'Invalid URL'}), 400
        
        local_result = check_local_blacklist(url)
        if local_result and not local_result['is_safe']:
            return jsonify(local_result)
        
        vt_result = check_virustotal(url)
        gsb_result = check_google_safebrowsing(url)
        phishing_result = check_phishing(url)
        
        is_safe = all([result['is_safe'] for result in [vt_result, gsb_result, phishing_result] if result])
        details = {**(vt_result or {}).get('details', {}), **(gsb_result or {}).get('details', {}), **(phishing_result or {}).get('details', {})}
        
        return jsonify({'is_safe': is_safe, 'details': details})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)