from flask import Flask, request, render_template, jsonify
import os
import re
from PIL import Image
from io import BytesIO
import base64
import numpy as np
import cv2
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, start_http_server
import time

app = Flask(__name__)

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time
    REQUEST_COUNT.labels(request.method, request.path).inc()
    REQUEST_LATENCY.labels(request.method, request.path).observe(request_latency)
    return response

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        image_data = re.sub('^data:image/.+;base64,', '', request.json)
        pil_image = Image.open(BytesIO(base64.b64decode(image_data))).convert('RGB')
        label_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
        label_names.sort()
        model_path = os.path.join('models', 'cifar_classifier.onnx')
        net = cv2.dnn.readNetFromONNX(model_path)
        img = cv2.resize(np.array(pil_image),(32,32))
        img = np.array([img]).astype('float64') / 255.0
        net.setInput(img)
        out = net.forward()
        index = np.argmax(out[0])
        label =  label_names[index].capitalize()
        return jsonify(result=label)
    return None