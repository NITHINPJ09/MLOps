from flask import Flask, request, render_template, jsonify, Response
import os
import re
from PIL import Image
from io import BytesIO
import base64
import numpy as np
import cv2
from prometheus_client import Counter, Histogram, CollectorRegistry, multiprocess, generate_latest, CONTENT_TYPE_LATEST
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

@app.route('/metrics')
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    start_time = time.time()
    try:
        image_data = re.sub('^data:image/.+;base64,', '', request.json)
        pil_image = Image.open(BytesIO(base64.b64decode(image_data))).convert('RGB')
        label_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
        label_names.sort()
        model_path = os.path.join('models', 'cifar_classifier.onnx')
        net = cv2.dnn.readNetFromONNX(model_path)
        img = cv2.resize(np.array(pil_image), (32, 32))
        img = np.array([img]).astype('float64') / 255.0
        net.setInput(img)
        out = net.forward()
        index = np.argmax(out[0])
        label = label_names[index].capitalize()
        latency = time.time() - start_time
        REQUEST_COUNT.labels(request.method, request.endpoint).inc()
        REQUEST_LATENCY.labels(request.method, request.endpoint).observe(latency)
        return jsonify(result=label)
    except Exception as e:
        return jsonify(error="Prediction failed", details=str(e)), 500