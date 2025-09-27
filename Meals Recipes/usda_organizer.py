import json
import re

# A dictionary to convert various units to a standard value (grams).
# These are approximate values and a good starting point for a hackathon.
UNIT_CONVERSIONS = {
    "cup": 240,    # Average weight of 1 cup in grams (for general liquids/powders)
    "tbsp": 15,    # 1 tablespoon = 15g
    "tsp": 5,      # 1 teaspoon = 5g
    "g": 1,        # Grams
    "kg": 1000,    # Kilograms
    "oz": 28.35,   # Ounces
    "lb": 453.6,   # Pounds
    "ml": 1,       # Milliliters
    "dash": 0.5,   # A dash is a small amount
    "pinch": 0.5,  # A pinch is a small amount
    "clove": 5,    # Average weight of a garlic clove
    "whole": 100,  # A very rough default for a single "whole" item
}

# A list of unwanted, descriptive words to be removed from ingredient names.
UNWANTED_WORDS = [
    "finely chopped", "chopped", "diced", "crushed", "ground",
    "sliced", "julienned", "grated", "minced", "cubed", "mashed",
    "a dash of", "a pinch of", "to taste", "extra", "fresh",
    "powdered", "dried", "raw", "cooked", "canned", "sweetened",
    "unsweetened", "large", "small", "medium", "pitted", "frozen"
]

def clean_ingredient_name(name_str):
    """Removes unwanted descriptive words to get a clean ingredient name."""
    cleaned_name = name_str
    for word in UNWANTED_WORDS:
        # Use regex with word boundaries to avoid partial matches
        cleaned_name = re.sub(r'\b' + re.escape(word) + r'\b', '', cleaned_name, flags=re.IGNORECASE).strip()

    # Handle special cases where removing a word is a mistake (e.g., "ground beef")
    if 'ground' not in name_str.lower() and 'beef' in cleaned_name.lower():
        cleaned_name = cleaned_name.replace('beef', 'ground beef')
    
    # Remove any extra spaces and non-alphabetic characters at the start/end
    cleaned_name = re.sub(r'^\W+|\W+$', '', cleaned_name)
    cleaned_name = ' '.join(cleaned_name.split())

    return cleaned_name.lower() if cleaned_name else ""

def parse_quantity(quantity_string):
    """
    Parses a quantity string including fractions and mixed numbers.
    e.g., "1 1/2" -> 1.5, "1/4" -> 0.25, "2" -> 2.0
    """
    quantity = 0.0
    
    # Regular expression to match whole numbers, fractions, and mixed numbers
    match = re.match(r'(\d+)?\s*(\d+/\d+)?', quantity_string)
    if match:
        whole_number_str = match.group(1)
        fraction_str = match.group(2)
        
        if whole_number_str:
            quantity += int(whole_number_str)
        
        if fraction_str:
            num, den = map(int, fraction_str.split('/'))
            quantity += num / den
            
    return quantity if quantity > 0 else 0.0 # Return 0.0 if no quantity found

def parse_ingredient_string(ingredient_string):
    """
    Parses a string to extract quantity, unit, and the clean ingredient name.
    """
    # Find numbers and fractions at the beginning of the string
    quantity_match = re.match(r'(\d+(?:/\d+)?|\d+\s+\d+/\d*|\d*\.\d*)\s*(.*)', ingredient_string)
    
    if quantity_match:
        quantity_str = quantity_match.group(1).strip()
        remaining_string = quantity_match.group(2).strip()
        
        quantity = parse_quantity(quantity_str)
        
        # Look for a known unit immediately following the quantity
        unit = None
        for key in UNIT_CONVERSIONS.keys():
            # Use a word boundary to match whole words like "cup" not "cups"
            unit_match = re.search(r'\b' + re.escape(key) + r'\b', remaining_string, flags=re.IGNORECASE)
            if unit_match:
                unit = unit_match.group(0).lower()
                # Remove the unit and surrounding whitespace from the string
                remaining_string = re.sub(r'\b' + re.escape(unit) + r'\b', '', remaining_string, flags=re.IGNORECASE).strip()
                break
                
        # The rest of the string is the ingredient name
        clean_name = clean_ingredient_name(remaining_string)

        return {
            "name": clean_name,
            "quantity_g": quantity * UNIT_CONVERSIONS.get(unit, 100)
        }

    # Fallback if no quantity or unit is found
    clean_name = clean_ingredient_name(ingredient_string)
    return {
        "name": clean_name,
        "quantity_g": 0.0, # Default to 0g if nothing is found
    }

def organize_meal_data(raw_file="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025Owlhacks2025/Meals Recipes/themealdb_dataset.jsonl/", new_file="/Users/Ariuk/Desktop/OwlHacks2025/Owlhacks2025/Owlhacks2025/Meals Recipes/themealdb_organized.jsonl/"):
    """
    Reads the raw meal data, cleans and organizes it, and saves to a new file.
    """
    organized_meals = []

    try:
        with open(raw_file, 'r', encoding='utf-8') as f:
            for line in f:
                meal = json.loads(line)
                
                cleaned_ingredients = []
                # Flag to check if the recipe should be kept
                keep_recipe = True 
                
                for ingredient_data in meal['ingredients']:
                    full_string = f"{ingredient_data['measure']} {ingredient_data['ingredient']}".strip()
                    if full_string:
                        parsed = parse_ingredient_string(full_string)

                        # New validation: if name is missing OR quantity is 0, skip the entire recipe
                        if not parsed['name'] or parsed['quantity_g'] == 0.0:
                            print(f"Skipping recipe '{meal.get('strMeal')}' due to missing data for ingredient: '{full_string}'")
                            keep_recipe = False
                            break # Exit the inner loop
                        
                        cleaned_ingredients.append(parsed)
                
                # Only add the meal to the organized list if it passed the validation
                if keep_recipe:
                    organized_meal = {
                        "idMeal": meal.get('idMeal'),
                        "strMeal": meal.get('strMeal'),
                        "strCategory": meal.get('strCategory'),
                        "strArea": meal.get('strArea'),
                        "strInstructions": meal.get('strInstructions'),
                        "ingredients": cleaned_ingredients
                    }
                    organized_meals.append(organized_meal)

    except FileNotFoundError:
        return f"Error: Raw data file '{raw_file}' not found."

    with open(new_file, 'w', encoding='utf-8') as f:
        for meal in organized_meals:
            f.write(json.dumps(meal) + '\n')
            
    return f"✅ Successfully organized {len(organized_meals)} meals into '{new_file}'."

if __name__ == "__main__":
    result = organize_meal_data()
    print(result)