import json
import re
from improved_usda_matcher import ImprovedUSDAMatcher

# A simple dictionary for unit conversions to grams
unit_conversions = {
    "g": 1,
    "kg": 1000,
    "oz": 28.35,
    "lb": 453.6,
    "cup": 240,
    "tbsp": 15,
    "tsp": 5,
    "ml": 1,
    "clove": 5,
    "dash": 0.5,
    "pinch": 0.5,
    "whole": 100,
    "": 100,
}

# Minimal fallback for ingredients not found in USDA
MINIMAL_FALLBACK = {
    'extract': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sodium': 0},
    'baking powder': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sodium': 0},
    'salt': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sodium': 38758},
    'pepper': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sodium': 0},
    'spices': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sodium': 0},
}

def extract_quantity(ingredient_string):
    """Extracts quantity from ingredient string."""
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
    """Cleans an ingredient string to get a simple, searchable name."""
    # Remove all numbers and units first
    clean_name = re.sub(r'\d+(?:\.\d+)?(?:\/\d+)?', '', name_str)
    clean_name = re.sub(r'\b(?:g|kg|oz|lb|cup|tbsp|tsp|ml|clove|dash|pinch|whole)\b', '', clean_name, flags=re.IGNORECASE)
    
    # Remove unwanted descriptive words
    unwanted_words = [
        "finely chopped", "chopped", "diced", "crushed", "ground",
        "sliced", "julienned", "grated", "minced", "cubed", "mashed",
        "a dash of", "a pinch of", "to taste", "extra", "fresh",
        "powdered", "dried", "raw", "cooked", "canned", "sweetened",
        "unsweetened", "large", "small", "medium", "pitted", "frozen",
        "beaten", "free-range", "salted", "unsalted", "plain", "self-raising"
    ]
    
    for word in unwanted_words:
        clean_name = re.sub(r'\b' + re.escape(word) + r'\b', '', clean_name, flags=re.IGNORECASE).strip()

    # Clean up whitespace and special characters
    clean_name = re.sub(r'^\W+|\W+$', '', clean_name)
    clean_name = ' '.join(clean_name.split())

    # Handle special cases
    if 'beef' in clean_name and 'ground' not in name_str.lower():
        clean_name = clean_name.replace('beef', 'ground beef')
    if 'chicken' in clean_name and 'breast' not in name_str.lower():
        clean_name = clean_name.replace('chicken', 'chicken breast')
        
    return clean_name.lower() if clean_name else ""

def get_ingredient_nutrition(ingredient_name, usda_matcher):
    """Gets nutritional data for an ingredient using improved USDA matching."""
    # Try USDA database first
    usda_nutrition = usda_matcher.find_nutrition(ingredient_name)
    if usda_nutrition:
        return usda_nutrition, "USDA"
    
    # Try minimal fallback
    for key, nutrition in MINIMAL_FALLBACK.items():
        if key in ingredient_name or any(word in ingredient_name for word in key.split()):
            return nutrition, "Fallback"
    
    # If not found, return default values
    return {
        "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0
    }, "Unknown"

def parse_meal_from_completion(completion_text):
    """Parse meal data from the completion field."""
    lines = completion_text.split('\n')
    meal_data = {}
    
    for line in lines:
        if line.startswith('Meal:'):
            meal_data['strMeal'] = line.replace('Meal:', '').strip()
        elif line.startswith('Ingredients:'):
            ingredients_text = line.replace('Ingredients:', '').strip()
            ingredients = []
            
            for ingredient_str in ingredients_text.split(','):
                ingredient_str = ingredient_str.strip()
                if ingredient_str:
                    quantity = extract_quantity(ingredient_str)
                    unit_match = re.search(r'\b(cup|tbsp|tsp|g|kg|oz|lb|ml|clove|dash|pinch|whole)\b', ingredient_str, re.IGNORECASE)
                    unit = unit_match.group(1).lower() if unit_match else ""
                    
                    # Clean ingredient name
                    clean_name = clean_ingredient_name(ingredient_str)
                    
                    if clean_name and len(clean_name) > 2:
                        ingredients.append({
                            "name": clean_name,
                            "quantity": quantity,
                            "unit": unit
                        })
            
            meal_data['ingredients'] = ingredients
    
    return meal_data

def build_final_dataset(raw_meals_file, usda_file, output_file):
    """Build the final dataset using improved USDA matching."""
    print("🌱 Initializing Improved USDA Matcher...")
    usda_matcher = ImprovedUSDAMatcher(usda_file)
    
    print("Processing meal data and building final dataset...")
    clean_examples = []
    
    with open(raw_meals_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                
                # Parse meal data from completion field
                meal = parse_meal_from_completion(data['completion'])
                
                if not meal.get('strMeal') or not meal.get('ingredients'):
                    print(f"Skipping line {line_num}: Missing meal name or ingredients")
                    continue
                
                # Calculate total nutrition for the entire meal using improved USDA matching
                total_nutrition = {
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0,
                    "fiber": 0,
                    "sodium": 0
                }
                
                # Simple ingredient list (just names)
                ingredient_names = []
                usda_matches = 0
                fallback_matches = 0
                unknown_matches = 0
                
                for ingredient in meal['ingredients']:
                    # Add to ingredient list
                    ingredient_names.append(ingredient['name'])
                    
                    # Get nutrition data
                    nutrition, source = get_ingredient_nutrition(ingredient['name'], usda_matcher)
                    
                    # Count matches by source
                    if source == "USDA":
                        usda_matches += 1
                    elif source == "Fallback":
                        fallback_matches += 1
                    else:
                        unknown_matches += 1
                    
                    # Convert quantity to grams
                    grams = ingredient['quantity'] * unit_conversions.get(ingredient['unit'], 100)
                    if grams > 500:  # Cap at 500g
                        grams = 100
                    
                    # Add to total nutrition (nutrition is per 100g)
                    for nutrient, value in nutrition.items():
                        if nutrient in total_nutrition:
                            total_nutrition[nutrient] += (value / 100) * grams
                
                # Round all nutrition values
                for nutrient in total_nutrition:
                    total_nutrition[nutrient] = round(total_nutrition[nutrient], 2)
                
                # Create clean example
                example = {
                    "meal_name": meal['strMeal'],
                    "ingredients": ingredient_names,
                    "nutrition": total_nutrition,
                    "data_source": {
                        "usda_matches": usda_matches,
                        "fallback_matches": fallback_matches,
                        "unknown_matches": unknown_matches,
                        "total_ingredients": len(ingredient_names)
                    }
                }
                
                clean_examples.append(example)
                
                if line_num % 50 == 0:
                    print(f"Processed {line_num} meals...")
                
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue

    # Save the clean dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in clean_examples:
            f.write(json.dumps(example) + '\n')
    
    # Print summary statistics
    total_usda = sum(ex['data_source']['usda_matches'] for ex in clean_examples)
    total_fallback = sum(ex['data_source']['fallback_matches'] for ex in clean_examples)
    total_unknown = sum(ex['data_source']['unknown_matches'] for ex in clean_examples)
    total_ingredients = sum(ex['data_source']['total_ingredients'] for ex in clean_examples)
    
    print(f"\n✅ Successfully created final dataset with {len(clean_examples)} examples")
    print(f"📊 Nutrition Data Sources:")
    print(f"   USDA matches: {total_usda} ({total_usda/total_ingredients*100:.1f}%)")
    print(f"   Fallback matches: {total_fallback} ({total_fallback/total_ingredients*100:.1f}%)")
    print(f"   Unknown matches: {total_unknown} ({total_unknown/total_ingredients*100:.1f}%)")
    print(f"   Total ingredients processed: {total_ingredients}")

if __name__ == "__main__":
    build_final_dataset(
        raw_meals_file="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/themealdb_dataset.jsonl",
        usda_file="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/FoodData_Central_foundation_food_json_2025-04-24.json",
        output_file="themealdb_final_dataset.jsonl"
    )
