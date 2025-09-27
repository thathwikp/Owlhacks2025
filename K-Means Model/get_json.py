import requests
import json
import string
from time import sleep

# The base URL and the test API key '1'
BASE_URL = "https://www.themealdb.com/api/json/v1/1/"
# A set to store unique meal IDs to prevent duplicates
unique_meal_ids = set()
# A list to store the complete meal objects
all_meals = []

def fetch_data(endpoint):
    """Fetches data from a given API endpoint."""
    try:
        response = requests.get(endpoint)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return None

def process_meals(data):
    """Extracts meals from the API response and adds unique ones to the list."""
    meals = data.get('meals')
    if meals:
        for meal in meals:
            meal_id = meal.get('idMeal')
            if meal_id and meal_id not in unique_meal_ids:
                # The filter/search endpoints return summary data, 
                # but we'll store the object as-is.
                unique_meal_ids.add(meal_id)
                all_meals.append(meal)

def get_meals_by_first_letter():
    """Fetches meals by iterating through the alphabet (A-Z)."""
    print("--- Fetching meals by first letter (A-Z) ---")
    for letter in string.ascii_lowercase:
        print(f"  Fetching meals starting with: {letter.upper()}...")
        endpoint = f"{BASE_URL}search.php?f={letter}"
        data = fetch_data(endpoint)
        if data:
            process_meals(data)
        sleep(0.5) # Be kind to the API server

def get_meals_by_category_or_area(list_type, filter_param):
    """Fetches meals by iterating through all Categories or Areas."""
    list_url = f"{BASE_URL}list.php?{list_type}=list"
    list_data = fetch_data(list_url)
    
    if list_data and list_data.get('meals'):
        print(f"--- Fetching meals by {filter_param.capitalize()} ---")
        items = [item.get(f'str{filter_param.capitalize()}') for item in list_data['meals']]
        
        for item in items:
            if item:
                print(f"  Fetching meals in {item}...")
                endpoint = f"{BASE_URL}filter.php?{list_type}={item.replace(' ', '_')}"
                data = fetch_data(endpoint)
                if data:
                    process_meals(data)
                sleep(0.5) # Be kind to the API server

def main():
    """Main function to orchestrate the data fetching."""
    
    # 1. Fetch by first letter
    get_meals_by_first_letter()
    
    # 2. Fetch by Category (c)
    get_meals_by_category_or_area('c', 'category')

    # 3. Fetch by Area (a)
    get_meals_by_category_or_area('a', 'area')
    
    # Write the final list to a JSON file
    output_filename = "all_themealdb_meals.json"
    try:
        with open(output_filename, 'w') as f:
            json.dump({"meals": all_meals}, f, indent=4)
        
        print("\n--- Script Complete ---")
        print(f"Total unique meals collected: {len(all_meals)}")
        print(f"Data saved to: {output_filename}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    main()