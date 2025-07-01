from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/medicine-identification')
def medicine_identification():
    return render_template('medicine_identification.html')
 
 
@app.route('/prescription-analyzer')
def prescription_analyzer():
    return render_template('prescription_analyzer.html')

@app.route('/medicine-tracker')
def medicine_tracker():
    return render_template('medicine_tracker.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    files = {'file': file.stream}

    try:
        backend_response = requests.post('http://127.0.0.1:5001/process-image', files=files)
        return backend_response.json()
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
