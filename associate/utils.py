import jwt
import requests
import json
from datetime import timedelta, datetime
from dotenv import load_dotenv
import os
load_dotenv()
#################--------------------Create Zoom Token-----------##########
def create_zoom_token():
    """Create a Zoom Token"""
    api_secret=os.environ.get('ZOOM_API_SECRET')
    api_key=os.environ.get('ZOOM_API_KEY')
    print(f"API Secret is :{api_secret}")
    print(f"API Key is :{api_key}")
    payload={
        'iss':api_key,
        'exp': datetime.now() + timedelta(seconds=5000)
    }
    token=jwt.encode(payload,api_secret,algorithm='HS256')
    print(f"Token is :{token}")
    return token

######################-----------------Create Zoom Link Function------------############
def create_zoom_meeting(slot_date, slot_time):
    """Create a Zoom meeting based on slot date and time."""
    token = create_zoom_token()
    print(f"Token is :{token}")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Define meeting details
    meeting_details = {
        "topic": "KYC Verification Meeting",
        "type": 2,
        "start_time": f"{slot_date}T{slot_time}:00Z",  # Format: YYYY-MM-DDTHH:MM:SSZ
        "duration": 30,
        "timezone": "Asia/Kolkata",
        "agenda": "KYC verification with Associate",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": True,
            "mute_upon_entry": True,
            "watermark": False,
            "approval_type": 0,
            "audio": "both"
        }
    }

    # Zoom API URL
    url = f"https://api.zoom.us/v2/users/{os.environ.get('ZOOM_USER_ID')}/meetings"
    print(f"Url is :{url}")

    # Send request to Zoom API
    response = requests.post(url, headers=headers, data=json.dumps(meeting_details))
    print(f"Zoom Response  is  :{response.text}")

    if response.status_code == 201:
        meeting_data = response.json()
        return meeting_data['join_url']
    else:
        return None