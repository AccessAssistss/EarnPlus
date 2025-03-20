import jwt
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
#################--------------------Create Zoom Token-----------##########
def create_zoom_token():
    """Create a Zoom Token"""
    api_secret=os.environ.get('ZOOM_API_SECRET')
    payload={
        'iss':os.environ.get('ZOOM_API_KEY'),
        'exp': datetime.now() + datetime.timedelta(seconds=5000)
    }
    token=jwt.encode(payload,api_secret,algorithm='HS256')
    return token

######################-----------------Create Zoom Link Function------------############