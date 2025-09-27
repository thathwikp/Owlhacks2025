import requests
import json
import string
import time

# Use the test API key '1' for free access
API_KEY = "1"
BASE_URL = f"https://www.themealdb.com/api/json/v1/{API_KEY}/"

def get_meals_by_letter(letter):
    """Fetches a list of meals that start with a given letter."""
    response = requests.get(f"{BASE_URL}search.php?f={letter}")
    if response.status_code == 200:
        return response.json().get('meals', [])
    return []

def get_meal_details(meal_id):
    """Fetches the full details of a meal by its ID."""
    response = requests.get(f"{BASE_URL}lookup.php?i={meal_id}")
    if response.status_code == 200:
        return response.json().get('meals', [])
    return []

def collect_all_recipes():
    """Collects all recipes by iterating through the alphabet."""
    all_meals = []
    # Loop through all letters of the alphabet
    for letter in string.ascii_lowercase:
        print(f"Fetching meals starting with letter: {letter.upper()}...")
        meals_by_letter = get_meals_by_letter(letter)
        if meals_by_letter:
            for meal in meals_by_letter:
                meal_details = get_meal_details(meal['idMeal'])
                if meal_details:
                    all_meals.append(meal_details[0]) # meal_details[0] is the dictionary with all meal info
            # Add a small delay to avoid hitting rate limits
            time.sleep(1) # Be mindful of API rate limits
    return all_meals

if __name__ == "__main__":
    # This will run the data collection process
    collected_recipes = collect_all_recipes()

    # Save the collected data to a JSON Lines file
    # We will now save the 'meal' dictionary directly, without the 'prompt'/'completion' wrapping
    with open("themealdb_raw_dataset1.jsonl", "w") as f: # Changed filename for clarity
        for meal in collected_recipes:
            f.write(json.dumps(meal) + '\n') # Save the raw meal dictionary

    print(f"Successfully collected and saved {len(collected_recipes)} raw recipes to mealdb_raw_dataset1.jsonl")