from flask import Flask, request
from controllers.PredictController import PredictController

app = Flask(__name__)


@app.route("/predict", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return {"data": "hello world"}
    if request.method == "POST":
        return PredictController.index()
