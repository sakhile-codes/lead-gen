from flask import Flask, request, render_template, send_file,jsonify
import time
import pandas as pd
from io import BytesIO
import googlemaps

# Initialize Flask app
app = Flask(__name__)

# Google Maps API client
api_key = 'YOUR_GMAPS_API_KEY_HERE'  # Replace with your actual Google API key
gmaps = googlemaps.Client(key=api_key)
