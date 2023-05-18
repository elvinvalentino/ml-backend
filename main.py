from flask import Flask, request
from controllers.PredictController import PredictController
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/predict", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return {"data": "hello world"}
    if request.method == "POST":
        return PredictController.index()
