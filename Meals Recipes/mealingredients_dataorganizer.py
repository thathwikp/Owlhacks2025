import json
import re

# A simple dictionary for unit conversions to grams
# This is a basic conversion table for a hackathon.
unit_conversions = {
    "g": 1,
    "kg": 1000,
    "oz": 28.35,
    "lb": 453.6,
    "cup": 240,  # Average for liquids and powders
    "tbsp": 15,
    "tsp": 5,
    "ml": 1,
    "clove": 5,  # Estimate for an average clove of garlic
    "dash": 0.5,
    "pinch": 0.5,
    "whole": 100,  # A very rough estimate
    "": 100,      # Default to 100g if no unit is specified
}

def extract_quantity(ingredient_string):
    """
    Extracts quantity from ingredient string.
    """
    # Look for numbers (including fractions and decimals)
    quantity_match = re.search(r'(\d+(?:\.\d+)?(?:\/\d+)?)', ingredient_string)
    if quantity_match:
        quantity_str = quantity_match.group(1)
        if '/' in quantity_str:
            parts = quantity_str.split('/')
            return float(parts[0]) / float(parts[1])
        else:
            return float(quantity_str)
    return 1.0

def clean_ingredient_name(name_str):
    """
    Cleans an ingredient string to get a simple, searchable name.
    This function has been expanded to better handle various descriptions.
    """
    unwanted_words = [
        "finely chopped", "chopped", "diced", "crushed", "ground",
        "sliced", "julienned", "grated", "minced", "cubed", "mashed",
        "a dash of", "a pinch of", "to taste", "extra", "fresh",
        "powdered", "dried", "raw", "cooked", "canned", "sweetened",
        "unsweetened", "large", "small", "medium", "pitted", "frozen"
    ]
    
    cleaned_name = name_str
    for word in unwanted_words:
        cleaned_name = re.sub(r'\b' + re.escape(word) + r'\b', '', cleaned_name, flags=re.IGNORECASE).strip()

    # Remove non-alphanumeric characters, numbers, and trim whitespace
    cleaned_name = re.sub(r'^\W+|\W+$', '', cleaned_name)
    cleaned_name = ' '.join(cleaned_name.split())

    # Handle special cases where removing 'ground' is a mistake
    if 'beef' in cleaned_name and 'ground' not in name_str.lower():
      cleaned_name = cleaned_name.replace('beef', 'ground beef')
      
    return cleaned_name.lower() if cleaned_name else ""

def get_ingredient_nutrition(ingredient_name, usda_data):
    """
    Searches for an ingredient in the USDA data and returns its key nutrients.
    Returns default values if not found.
    """
    # Use a flexible keyword search for the most reliable match
    search_keywords = re.findall(r'\w+', ingredient_name.lower())
    
    for food_item in usda_data.get('FoundationFoods', []):
        description = food_item.get('description', '').lower()
        if all(keyword in description for keyword in search_keywords):
            nutrients = {}
            nutrient_map = {
                "Energy": "kcal",
                "Protein": "g",
                "Total lipid (fat)": "g",
                "Carbohydrate, by difference": "g",
                "Fiber, total dietary": "g",
                "Sodium, Na": "mg"
            }
            
            for nutrient in food_item.get('foodNutrients', []):
                nutrient_name = nutrient.get('nutrient', {}).get('name')
                if nutrient_name in nutrient_map:
                    amount = nutrient.get('amount')
                    if amount is not None:
                        unit_type = nutrient_map[nutrient_name]
                        if unit_type not in nutrients:
                            nutrients[unit_type] = {}
                        nutrients[unit_type][nutrient_name] = amount
            
            # Return a cleaned dictionary of nutrients
            return {
                "Calories": nutrients.get("kcal", {}).get("Energy", 0),
                "Protein": nutrients.get("g", {}).get("Protein", 0),
                "Fat": nutrients.get("g", {}).get("Total lipid (fat)", 0),
                "Carbohydrates": nutrients.get("g", {}).get("Carbohydrate, by difference", 0),
                "Fiber": nutrients.get("g", {}).get("Fiber, total dietary", 0),
                "Sodium": nutrients.get("mg", {}).get("Sodium, Na", 0)
            }
    
    # Return default nutritional values if no match is found
    return {
        "Calories": 0, "Protein": 0, "Fat": 0,
        "Carbohydrates": 0, "Fiber": 0, "Sodium": 0
    }

def get_total_nutrition(meal_data, usda_data):
    """
    Calculates the total nutritional value for a meal based on its ingredients.
    """
    total_nutrition = {
        "Calories": 0, "Protein": 0, "Fat": 0,
        "Carbohydrates": 0, "Fiber": 0, "Sodium": 0
    }
    
    for ingredient in meal_data['ingredients']:
        # Get nutrition for 100g of the ingredient
        nutrition_per_100g = get_ingredient_nutrition(ingredient['name'], usda_data)
        
        # Get the quantity and unit from the parsed data
        quantity = float(ingredient.get('quantity', 1))
        unit = ingredient.get('unit', '').lower()
        
        # Convert the quantity to grams
        grams = quantity * unit_conversions.get(unit, 1)
        
        # Apply reasonable limits to prevent extreme values
        # If grams is too high, assume it's a mistake and cap it
        if grams > 1000:  # More than 1kg seems unreasonable for a single ingredient
            original_grams = grams
            grams = 100  # Default to 100g
            print(f"Warning: Capped {ingredient['name']} quantity from {original_grams}g to 100g")

        # Calculate and add to the total
        for nutrient, value in nutrition_per_100g.items():
            if nutrient in total_nutrition and value is not None:
                total_nutrition[nutrient] += (value / 100) * grams

    # Round the numbers for clean output
    for nutrient in total_nutrition:
        total_nutrition[nutrient] = round(total_nutrition[nutrient], 2)
        
    return total_nutrition

def parse_meal_from_completion(completion_text):
    """
    Parse meal data from the completion field.
    """
    lines = completion_text.split('\n')
    meal_data = {}
    
    for line in lines:
        if line.startswith('Meal:'):
            meal_data['strMeal'] = line.replace('Meal:', '').strip()
        elif line.startswith('Category:'):
            meal_data['strCategory'] = line.replace('Category:', '').strip()
        elif line.startswith('Area:'):
            meal_data['strArea'] = line.replace('Area:', '').strip()
        elif line.startswith('Ingredients:'):
            ingredients_text = line.replace('Ingredients:', '').strip()
            # Split ingredients and parse them
            ingredients = []
            for ingredient_str in ingredients_text.split(','):
                ingredient_str = ingredient_str.strip()
                if ingredient_str:
                    quantity = extract_quantity(ingredient_str)
                    unit_match = re.search(r'\b(cup|tbsp|tsp|g|kg|oz|lb|ml|clove|dash|pinch|whole)\b', ingredient_str, re.IGNORECASE)
                    unit = unit_match.group(1).lower() if unit_match else ""
                    
                    # Extract ingredient name (remove quantity and unit)
                    clean_name = re.sub(r'^\d+(?:\.\d+)?(?:\/\d+)?\s*(?:g|kg|oz|lb|cup|tbsp|tsp|ml|clove|dash|pinch|whole)\s*', '', ingredient_str, flags=re.IGNORECASE)
                    clean_name = clean_ingredient_name(clean_name)
                    
                    # Skip if ingredient name is too short or empty
                    if clean_name and len(clean_name) > 2:
                        ingredients.append({
                            "name": clean_name,
                            "quantity": quantity,
                            "unit": unit
                        })
            meal_data['ingredients'] = ingredients
        elif line.startswith('Instructions:'):
            meal_data['strInstructions'] = line.replace('Instructions:', '').strip()
        elif line.startswith('Source:'):
            meal_data['strSource'] = line.replace('Source:', '').strip()
        elif line.startswith('Tags:'):
            meal_data['strTags'] = line.replace('Tags:', '').strip()
    
    return meal_data

def build_finetune_dataset(raw_meals_file, usda_file, output_file):
    """
    Main function to orchestrate the data processing pipeline.
    """
    # 1. Load USDA nutritional data
    print("Loading USDA nutritional data...")
    with open(usda_file, 'r', encoding='utf-8') as f:
        usda_data = json.load(f)

    # 2. Process raw meal data
    print("Processing raw meal data and building final dataset...")
    finetune_examples = []
    
    with open(raw_meals_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                
                # Parse meal data from completion field
                meal = parse_meal_from_completion(data['completion'])
                
                if not meal.get('strMeal') or not meal.get('ingredients'):
                    print(f"Skipping line {line_num}: Missing meal name or ingredients")
                    continue
                
                # Get total nutrition for the meal
                total_nutrition = get_total_nutrition(meal, usda_data)
                
                # Create a simple grocery list
                grocery_list = ', '.join([ing['name'] for ing in meal['ingredients']])
                
                # Final fine-tuning prompt/completion pair
                prompt_text = f"User info: 180 lbs, muscle gain, no dairy allergy. Goal: High-protein dinner. Generate a detailed recipe plan from the following meal: {meal['strMeal']}."
                completion_text = (
                    f"Meal: {meal['strMeal']}.\n"
                    f"Nutrition (per serving): Calories: {total_nutrition['Calories']} kcal, Protein: {total_nutrition['Protein']}g, Fat: {total_nutrition['Fat']}g, Carbs: {total_nutrition['Carbohydrates']}g.\n"
                    f"Ingredients: {grocery_list}.\n"
                    f"Instructions: {meal['strInstructions']}"
                )
                
                finetune_examples.append({
                    "prompt": prompt_text,
                    "completion": completion_text
                })
                
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue

    # 3. Save the final dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in finetune_examples:
            f.write(json.dumps(example) + '\n')
            
    print(f"✅ Successfully created final dataset with {len(finetune_examples)} examples in '{output_file}'.")

if __name__ == "__main__":
    # You will need to have 'themealdb_raw_data.jsonl' from the previous step
    # and 'FoodData_Central_foundation_food_json_2025-04-24.json' in the same directory.
    build_finetune_dataset(
        raw_meals_file="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/themealdb_dataset.jsonl", 
        usda_file="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/FoodData_Central_foundation_food_json_2025-04-24.json",
        output_file="themealdb_finetune_dataset.jsonl"
    )