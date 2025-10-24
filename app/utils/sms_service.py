import http.client
import json
from django.conf import settings

def send_sms(phone_number, message):
    conn = http.client.HTTPSConnection("textflow-sms-api.p.rapidapi.com")

    payload = json.dumps({
        "data": {
            "phone_number": phone_number,
            "text": message,
            "api_key": settings.TEXTFLOW_API_KEY
        }
    })

    headers = {
        'x-rapidapi-key': settings.RAPIDAPI_KEY,
        'x-rapidapi-host': "textflow-sms-api.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    conn.request("POST", "/send-sms", payload, headers)
    res = conn.getresponse()
    response_data = res.read()
    return response_data.decode("utf-8")
