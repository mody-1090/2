# app/routes/api_routes.py
from flask import Blueprint, jsonify

api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/data')
def get_data():
    data = {"message": "Hello from API"}
    return jsonify(data)
