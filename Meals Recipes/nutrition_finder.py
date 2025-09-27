import json

def get_nutrition_info(food_name, file_path="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/FoodData_Central_foundation_food_json_2025-04-24.json"):
    """
    Searches for a food in the USDA JSON file and returns its key nutritional information.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return "Error: JSON file not found. Please make sure the file is in the same directory as the script."

    # Search for the food by its description
    for food_item in data.get('FoundationFoods', []):
        if food_name.lower() in food_item.get('description', '').lower():
            nutrition = {
                "description": food_item['description'],
                "nutrients_per_100g": {}
            }
           
            # The API output uses specific IDs for nutrients. We'll map the common ones.
            nutrient_map = {
                "Energy": "Calories (kcal)",
                "Protein": "Protein (g)",
                "Total lipid (fat)": "Total Fat (g)",
                "Carbohydrate, by difference": "Carbohydrates (g)",
                "Fiber, total dietary": "Fiber (g)",
                "Sodium, Na": "Sodium (mg)",
                "Iron, Fe": "Iron (mg)"
            }

            for nutrient in food_item.get('foodNutrients', []):
                nutrient_name = nutrient.get('nutrient', {}).get('name')
                if nutrient_name in nutrient_map:
                    mapped_name = nutrient_map[nutrient_name]
                    amount = nutrient.get('amount')
                    unit = nutrient.get('nutrient', {}).get('unitName')
                    if amount is not None:
                         # Use a simple "per 100g" format since the data is normalized
                        nutrition["nutrients_per_100g"][mapped_name] = f"{amount} {unit}"
           
            return nutrition

    return f"No nutritional information found for '{food_name}'."

if __name__ == "__main__":
    # Example usage:
    search_term = "Beef, ground, 90% lean meat / 10% fat, raw"
    info = get_nutrition_info(search_term)
   
    print(f"Nutritional information for '{search_term}':")
    print(json.dumps(info, indent=4))