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

# Function to get nearby businesses using text search
def get_nearby_businesses_text(lat, lon, query, radius=50000):
    location = f"{lat},{lon}"
    places_result = gmaps.places(query=query, location=location, radius=radius)
    businesses = []

    # Add the first page of results
    businesses.extend(extract_businesses(places_result))

    # Check if more pages of results exist and fetch them
    while 'next_page_token' in places_result:
        next_page_token = places_result['next_page_token']
        # Google API requires a short delay before fetching the next page
        time.sleep(2)
        places_result = gmaps.places(query=query, location=location, radius=radius, page_token=next_page_token)
        businesses.extend(extract_businesses(places_result))

    return businesses