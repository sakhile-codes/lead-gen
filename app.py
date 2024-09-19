from flask import Flask, request, render_template, send_file, jsonify
import time
import pandas as pd
from io import BytesIO
import googlemaps
import requests

# Initialize Flask app
app = Flask(__name__)

# Google Maps API client
maps_api_key = ''  # Replace with your actual Google API key
gmaps = googlemaps.Client(key=maps_api_key)

# Google Custom Search API key and Custom Search Engine ID
CSE_API_KEY = ''  # Replace with your Custom Search API key
CX = ''  # Replace with your Custom Search Engine ID

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


# Route to save businesses into Excel
@app.route('/save', methods=['POST'])
def save():
    businesses = request.json.get('businesses')
    
    # Convert the list of businesses to a DataFrame
    df = pd.DataFrame(businesses)

    # Save the DataFrame to an Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    
    output.seek(0)  # Move cursor to the beginning of the file
    
    # Send the file as a download response
    return send_file(output, as_attachment=True, download_name='leads.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Main route to display the input form and results
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        location_name = request.form['location']
        business_type = request.form['business_type']

        # Get coordinates from location name
        lat, lon = get_coordinates(location_name)
        
        businesses = []

        if lat and lon:
            # Get nearby businesses with the user-specified business type using text search
            businesses = get_nearby_businesses_text(lat, lon, query=business_type)
            return render_template('index.html', businesses=businesses, location=location_name, business_type=business_type)
        else:
            return render_template('index.html', error="Could not find location.")
    return render_template('index.html')


def fetch_seo_results(location, business_type, start_index=1):
    # Construct the query using the provided location and business type
    query = f"{business_type} in {location} contact details"
    
    # Construct the API URL
    url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={CSE_API_KEY}&cx={CX}&start={start_index}'
    
    # Make the request to the Google Custom Search API
    response = requests.get(url)
    
    # Return the JSON response
    return response.json()

# SEO results route
@app.route('/seo-results', methods=['POST'])
def seo_results():
    # Get the location and business type from the form data
    location_name = request.form['location']
    business_type = request.form['business_type']
    
    # Fetch SEO results related to the business type and location
    seo_results_data = fetch_seo_results(location_name, business_type)
    seo_results = []
    
    # Check if items exist in the result and populate the list
    if 'items' in seo_results_data:
        for item in seo_results_data['items']:
            seo_results.append({
                'title': item['title'],
                'link': item['link'],
                'snippet': item.get('snippet', '')
            })
    
    # Render the SEO results template
    return render_template('seo_results.html', seo_results=seo_results, location=location_name, business_type=business_type)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
