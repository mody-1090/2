# app/services/api_service.py
import requests

def call_external_api(url, params=None):
    """مثال لاستدعاء API خارجي باستخدام requests."""
    response = requests.get(url, params=params)
    return response.json()
