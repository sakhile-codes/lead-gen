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

# Function to convert location name to coordinates
def get_coordinates(location_name):
    geocode_result = gmaps.geocode(location_name)
    if geocode_result:
        lat = geocode_result[0]['geometry']['location']['lat']
        lon = geocode_result[0]['geometry']['location']['lng']
        return lat, lon
    return None, None

# Helper function to extract business data from API results
def extract_businesses(places_result):
    business_list = []
    for place in places_result['results']:
        business = {
            'name': place['name'],
            'address': place.get('vicinity', 'N/A'),
            'rating': place.get('rating', 'N/A'),
            'place_id': place['place_id']
        }
        
        # Get additional business details like phone number and website
        details = get_business_details(place['place_id'])
        business['phone_number'] = details['phone_number']
        business['website'] = details['website']
        business_list.append(business)
    return business_list

# Function to get detailed business information using place_id
def get_business_details(place_id):
    place_details = gmaps.place(place_id=place_id, fields=['name', 'formatted_phone_number', 'website'])
    details = {
        'phone_number': place_details['result'].get('formatted_phone_number', 'N/A'),
        'website': place_details['result'].get('website', 'N/A')
    }
    return details