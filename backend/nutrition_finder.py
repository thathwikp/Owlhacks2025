import json
import re
import math

# --- 1. CONFIGURATION AND DATA ---

# Global file paths (Ensure these files are in the same directory!)
ORG_DATA_FILE = "/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/themealdb_organized.jsonl"
USDA_DATA_FILE = "/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/FoodData_Central_foundation_food_json_2025-04-24.json"
OUTPUT_FILE = "/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/themealdb_calculated.jsonl" # Renamed output file for clarity

# Fallback list for common ingredients not easily found in the USDA file (per 100g)
# This list is prioritized for staples and hard-to-match items.
FALLBACK_NUTRITION = {
    "pepper": {"Calories": 251, "Protein": 11, "Fat": 3.3, "Carbohydrates": 64.8, "Fiber": 26.5, "Sodium": 20},
    "water": {"Calories": 0, "Protein": 0, "Fat": 0, "Carbohydrates": 0, "Fiber": 0, "Sodium": 0},
    "baking powder": {"Calories": 53, "Protein": 0.1, "Fat": 0.2, "Carbohydrates": 40.5, "Fiber": 0, "Sodium": 10565},
    "garlic": {"Calories": 149, "Protein": 6.4, "Fat": 0.5, "Carbohydrates": 33.1, "Fiber": 2.1, "Sodium": 15},
    "sugar": {"Calories": 387, "Protein": 0, "Fat": 0, "Carbohydrates": 100, "Fiber": 0, "Sodium": 1},
    "vinegar": {"Calories": 18, "Protein": 0.04, "Fat": 0, "Carbohydrates": 0.9, "Fiber": 0, "Sodium": 5},
    "milk": {"Calories": 42, "Protein": 3.4, "Fat": 1, "Carbohydrates": 5, "Fiber": 0, "Sodium": 43},
    "egg": {"Calories": 155, "Protein": 12.6, "Fat": 10.6, "Carbohydrates": 1.1, "Fiber": 0, "Sodium": 124},
    "salt": {"Calories": 0, "Protein": 0, "Fat": 0, "Carbohydrates": 0, "Fiber": 0, "Sodium": 38758},
    "chicken": {"Calories": 165, "Protein": 31.0, "Fat": 3.6, "Carbohydrates": 0.0, "Fiber": 0.0, "Sodium": 74 },
    "beef": {"Calories": 250, "Protein": 26.0, "Fat": 15.0, "Carbohydrates": 0.0, "Fiber": 0.0, "Sodium": 72 },
    "apple": {"Calories": 52, "Protein": 0.3, "Fat": 0.2, "Carbohydrates": 14.0, "Fiber": 2.4, "Sodium": 1 },
    "banana": {"Calories": 89, "Protein": 1.1, "Fat": 0.3, "Carbohydrates": 23.0, "Fiber": 2.6, "Sodium": 1 },
    "broccoli": {"Calories": 34, "Protein": 2.8, "Fat": 0.4, "Carbohydrates": 7.0, "Fiber": 2.6, "Sodium": 33 },
    "oats": {"Calories": 389, "Protein": 17.0, "Fat": 7.0, "Carbohydrates": 66.0, "Fiber": 10.6, "Sodium": 2 },
    "flour": {"Calories": 364, "Protein": 10.3, "Fat": 1.0, "Carbohydrates": 76.3, "Fiber": 2.7, "Sodium": 2 },
    "butter": {"Calories": 717, "Protein": 0.9, "Fat": 81.1, "Carbohydrates": 0.1, "Fiber": 0.0, "Sodium": 643 },
    "olive oil": {"Calories": 884, "Protein": 0.0, "Fat": 100.0, "Carbohydrates": 0.0, "Fiber": 0.0, "Sodium": 2 },
    "pork": {"Calories": 242, "Protein": 27.3, "Fat": 13.9, "Carbohydrates": 0.0, "Fiber": 0.0, "Sodium": 75}, 
    "fish": {"Calories": 134, "Protein": 20.0, "Fat": 5.0, "Carbohydrates": 0.0, "Fiber": 0.0, "Sodium": 50}, # Generic white fish/cod
    "cream cheese": {"Calories": 342, "Protein": 6.1, "Fat": 34.0, "Carbohydrates": 4.1, "Fiber": 0.0, "Sodium": 335},
    "almonds": {"Calories": 579, "Protein": 21.2, "Fat": 49.9, "Carbohydrates": 21.6, "Fiber": 12.5, "Sodium": 1},
    "yogurt": {"Calories": 59, "Protein": 10.0, "Fat": 0.4, "Carbohydrates": 3.9, "Fiber": 0.0, "Sodium": 36}, # Plain, nonfat Greek yogurt
    "sausage": {"Calories": 328, "Protein": 16.5, "Fat": 28.6, "Carbohydrates": 1.9, "Fiber": 0.0, "Sodium": 776}
}

def load_json_file(file_path):
    """Loads a JSON file, handling errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"FATAL ERROR: Required file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"FATAL ERROR: Could not decode JSON from {file_path}. File may be corrupt.")
        return None

def get_ingredient_nutrition(ingredient_name, usda_data):
    """
    Searches for an ingredient in the USDA data first. If not found, falls back 
    to the hardcoded list. Returns key nutrients (per 100g).
    """
    # 1. Fallback Check (Top Priority 1 for Staples)
    # Check the dedicated fallback list for generic items like 'oil' or 'sugar' 
    # that may have been aggressively cleaned by DataOrganizer.py.
    if ingredient_name in FALLBACK_NUTRITION:
        return FALLBACK_NUTRITION[ingredient_name]

    # 2. USDA Data Search (Primary Source - PRIORITY 2)
    search_keywords = re.findall(r'\w+', ingredient_name.lower())
    
    for food_item in usda_data.get('FoundationFoods', []):
        description = food_item.get('description', '').lower()
        
        # Check if all keywords are present in the description
        if all(keyword in description for keyword in search_keywords):
            nutrients = {}
            nutrient_map = {
                "Energy": "Calories",
                "Protein": "Protein",
                "Total lipid (fat)": "Fat",
                "Carbohydrate, by difference": "Carbohydrates",
                "Fiber, total dietary": "Fiber",
                "Sodium, Na": "Sodium"
            }

            for nutrient in food_item.get('foodNutrients', []):
                nutrient_name = nutrient.get('nutrient', {}).get('name')
                mapped_name = nutrient_map.get(nutrient_name)
                
                if mapped_name:
                    amount = nutrient.get('amount')
                    if amount is not None:
                        # Convert all units to standard grams (g) or milligrams (mg)
                        unit = nutrient.get('nutrient', {}).get('unitName')
                        if unit == 'MG':
                            nutrients[mapped_name] = amount 
                        elif unit == 'KCAL':
                            nutrients[mapped_name] = amount
                        elif unit == 'G':
                            nutrients[mapped_name] = amount
            
            # If USDA finds a match, return it immediately.
            return {
                "Calories": nutrients.get("Calories", 0),
                "Protein": nutrients.get("Protein", 0),
                "Fat": nutrients.get("Fat", 0),
                "Carbohydrates": nutrients.get("Carbohydrates", 0),
                "Fiber": nutrients.get("Fiber", 0),
                "Sodium": nutrients.get("Sodium", 0),
            }

    # 3. Final Fallback (If not found anywhere)
    return {"Calories": 0, "Protein": 0, "Fat": 0, "Carbohydrates": 0, "Fiber": 0, "Sodium": 0}

def get_total_nutrition(meal_data, usda_data):
    """
    Calculates the total nutritional value for a meal based on its organized ingredients.
    This version relies on 'quantity_g' being pre-calculated.
    """
    total_nutrition = {
        "Calories": 0, "Protein": 0, "Fat": 0,
        "Carbohydrates": 0, "Fiber": 0, "Sodium": 0
    }
    
    for ingredient in meal_data['ingredients']:
        # Get nutrition for 100g of the ingredient
        nutrition_per_100g = get_ingredient_nutrition(ingredient['name'], usda_data)
        
        # Get the standardized quantity in grams
        # NOTE: This value now comes directly from the organized file (DataOrganizer.py output)
        quantity_g = ingredient.get('quantity_g', 0)
        
        # Calculate and add to the total
        for nutrient, value_per_100g in nutrition_per_100g.items():
            if value_per_100g is not None:
                # Calculation: (Value_per_100g / 100) * total grams
                total_nutrition[nutrient] += (value_per_100g / 100) * quantity_g

    # Round the numbers for clean output
    for nutrient in total_nutrition:
        total_nutrition[nutrient] = round(total_nutrition[nutrient], 2)
        
    return total_nutrition

def build_calculated_dataset(organized_meals_file, usda_file, output_file):
    """
    Orchestrates the data pipeline: loads organized meals, calculates nutrition,
    and saves the final Meal JSONL structure, skipping meals with zero calories.
    """
    # 1. Load data sources
    print("Loading USDA nutritional data...")
    usda_data = load_json_file(usda_file)
    if not usda_data: return

    calculated_meals = []
    skipped_count = 0
    
    # 2. Process organized meal data line by line
    try:
        with open(organized_meals_file, 'r', encoding='utf-8') as f:
            for line in f:
                meal = json.loads(line)
            
                # Calculate total nutrition for the meal
                total_nutrition = get_total_nutrition(meal, usda_data)
                
                # --- NEW VALIDATION: SKIP IF ZERO CALORIES ---
                if total_nutrition['Calories'] == 0:
                    skipped_count += 1
                    continue # Skip this meal and go to the next line
                
                # --- 3. Create the Final Meal Data Structure ---
                
                # Add the calculated nutrition to the meal object
                meal['nutrition'] = total_nutrition
                
                # We will categorize the meal in the next step, after this script runs!
                
                calculated_meals.append(meal)

    except FileNotFoundError:
        print(f"FATAL ERROR: Organized meal file '{organized_meals_file}' not found. Did you run the DataOrganizer.py script?")
        return
    
    # 4. Save the final dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        for meal in calculated_meals:
            f.write(json.dumps(meal) + '\n')
            
    print(f"✅ Successfully created calculated meal data with {len(calculated_meals)} examples in '{output_file}'.")
    if skipped_count > 0:
        print(f"⚠️ Note: Skipped {skipped_count} meals that calculated to 0 Calories.")

if __name__ == "__main__":
    print("--- Starting Nutritional Data Processor ---")
    
    # NOTE: You MUST run the DataOrganizer.py script first to create the organized file.
    # The organized data file path (created in the last step)
    organized_data_path = ORG_DATA_FILE
    
    # The USDA file path (the file you uploaded)
    usda_data_path = USDA_DATA_FILE

    # The final output file path
    final_output_path = OUTPUT_FILE
    
    build_calculated_dataset(organized_data_path, usda_data_path, final_output_path)
