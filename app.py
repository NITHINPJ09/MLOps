from flask import Flask, request, render_template, jsonify
import os
import re
from PIL import Image
from io import BytesIO
import base64
import numpy as np
import cv2
from prometheus_client import Counter, Histogram, CollectorRegistry, multiprocess, generate_latest, CONTENT_TYPE_LATEST
import time

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"], registry=registry)
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "Latency of HTTP requests", ["endpoint"], registry=registry)

app = Flask(__name__)

label_names = sorted([
    'airplane', 'automobile', 'bird', 'cat', 'deer',
    'dog', 'frog', 'horse', 'ship', 'truck'
])
model_path = os.path.join('models', 'cifar_classifier.onnx')
net = cv2.dnn.readNetFromONNX(model_path)

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_metrics(response):
    if request.endpoint:
        latency = time.time() - request.start_time
        REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()
        REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response

@app.route("/metrics")
def metrics():
    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        image_data = re.sub('^data:image/.+;base64,', '', request.json)
        pil_image = Image.open(BytesIO(base64.b64decode(image_data))).convert('RGB')
        img = cv2.resize(np.array(pil_image), (32, 32))
        img = np.array([img]).astype('float64') / 255.0
        net.setInput(img)
        out = net.forward()
        index = np.argmax(out[0])
        label = label_names[index].capitalize()
        return jsonify(result=label)
    except Exception as e:
        return jsonify(error="Prediction failed", details=str(e)), 500
