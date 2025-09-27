"""
Command-line interface for the Nutrition Calculator.
Provides an interactive way to calculate nutritional targets.
"""

import sys
from nutrition_calculator import UserProfile, NutritionCalculator


def get_user_input():
    """Get user input for nutritional calculations."""
    print("=== Nutrition Calculator CLI ===\n")
    
    try:
        # Get basic information
        age = int(input("Enter your age (years): "))
        weight = float(input("Enter your weight (kg): "))
        height = float(input("Enter your height (cm): "))
        
        # Get gender
        print("\nGender options:")
        print("1. male")
        print("2. female")
        gender_choice = input("Select gender (1 or 2): ").strip()
        gender = "male" if gender_choice == "1" else "female"
        
        # Get activity level
        print("\nActivity Level options:")
        print("1. Sedentary (little or no exercise)")
        print("2. Lightly Active (light exercise/sports 1-3 days/week)")
        print("3. Moderately Active (moderate exercise/sports 3-5 days/week)")
        print("4. Very Active (hard exercise/sports 6-7 days a week)")
        print("5. Extra Active (very hard exercise/physical job)")
        
        activity_map = {
            "1": "sedentary",
            "2": "lightly_active", 
            "3": "moderately_active",
            "4": "very_active",
            "5": "extra_active"
        }
        activity_choice = input("Select activity level (1-5): ").strip()
        activity_level = activity_map.get(activity_choice, "moderately_active")
        
        # Get goal
        print("\nGoal options:")
        print("1. Mild Weight Loss (~0.5 lb/week)")
        print("2. Standard Weight Loss (~1 lb/week)")
        print("3. Maintain Weight")
        print("4. Mild Weight Gain (~0.5 lb/week)")
        print("5. Standard Weight Gain (~1 lb/week)")
        
        goal_map = {
            "1": "mild_weight_loss",
            "2": "standard_weight_loss",
            "3": "maintain",
            "4": "mild_weight_gain", 
            "5": "standard_weight_gain"
        }
        goal_choice = input("Select goal (1-5): ").strip()
        goal = goal_map.get(goal_choice, "maintain")
        
        # Get diet plan
        print("\nDiet Plan options:")
        print("1. Balanced (40% Carbs, 30% Protein, 30% Fat)")
        print("2. High Protein (30% Carbs, 40% Protein, 30% Fat)")
        print("3. Low Carb (20% Carbs, 35% Protein, 45% Fat)")
        
        diet_map = {
            "1": "balanced",
            "2": "high_protein",
            "3": "low_carb"
        }
        diet_choice = input("Select diet plan (1-3): ").strip()
        diet_plan = diet_map.get(diet_choice, "balanced")
        
        return UserProfile(
            age=age,
            weight=weight,
            height=height,
            gender=gender,
            activity_level=activity_level,
            goal=goal,
            diet_plan=diet_plan
        )
        
    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


def display_results(profile: UserProfile, targets):
    """Display calculation results in a formatted way."""
    print("\n" + "="*50)
    print("NUTRITIONAL CALCULATION RESULTS")
    print("="*50)
    
    print(f"\n📊 USER PROFILE:")
    print(f"   Age: {profile.age} years")
    print(f"   Weight: {profile.weight} kg")
    print(f"   Height: {profile.height} cm")
    print(f"   Gender: {profile.gender.title()}")
    print(f"   Activity Level: {profile.activity_level.replace('_', ' ').title()}")
    print(f"   Goal: {profile.goal.replace('_', ' ').title()}")
    print(f"   Diet Plan: {profile.diet_plan.replace('_', ' ').title()}")
    
    print(f"\n🔥 METABOLIC CALCULATIONS:")
    print(f"   BMR (Basal Metabolic Rate): {targets.bmr:.1f} calories/day")
    print(f"   TDEE (Total Daily Energy Expenditure): {targets.tdee:.1f} calories/day")
    print(f"   Target Calorie Intake: {targets.target_calories:.1f} calories/day")
    
    print(f"\n🥗 MACRONUTRIENT TARGETS:")
    print(f"   Protein: {targets.protein_grams:.1f}g ({targets.protein_percentage}%)")
    print(f"   Carbohydrates: {targets.carbs_grams:.1f}g ({targets.carbs_percentage}%)")
    print(f"   Fat: {targets.fat_grams:.1f}g ({targets.fat_percentage}%)")
    
    # Calculate calories from each macro
    protein_calories = targets.protein_grams * 4
    carbs_calories = targets.carbs_grams * 4
    fat_calories = targets.fat_grams * 9
    
    print(f"\n📈 CALORIE BREAKDOWN:")
    print(f"   Protein: {protein_calories:.1f} calories")
    print(f"   Carbohydrates: {carbs_calories:.1f} calories")
    print(f"   Fat: {fat_calories:.1f} calories")
    print(f"   Total: {protein_calories + carbs_calories + fat_calories:.1f} calories")
    
    print(f"\n💡 TIPS:")
    print(f"   • Aim for {targets.protein_grams:.0f}g protein per day for muscle maintenance")
    print(f"   • Distribute your {targets.target_calories:.0f} calories across 3-4 meals")
    print(f"   • Stay hydrated with at least 8-10 glasses of water daily")
    
    if profile.goal in ["mild_weight_loss", "standard_weight_loss"]:
        print(f"   • Weight loss tip: Create a sustainable calorie deficit")
    elif profile.goal in ["mild_weight_gain", "standard_weight_gain"]:
        print(f"   • Weight gain tip: Focus on nutrient-dense, calorie-rich foods")
    else:
        print(f"   • Maintenance tip: Monitor your weight and adjust as needed")


def main():
    """Main CLI function."""
    try:
        # Get user input
        profile = get_user_input()
        
        # Calculate nutritional targets
        calculator = NutritionCalculator()
        targets = calculator.calculate_nutritional_targets(profile)
        
        # Display results
        display_results(profile, targets)
        
        # Ask if user wants to calculate again
        while True:
            again = input("\nCalculate for another profile? (y/n): ").strip().lower()
            if again in ['y', 'yes']:
                main()
                break
            elif again in ['n', 'no']:
                print("Thank you for using the Nutrition Calculator!")
                break
            else:
                print("Please enter 'y' or 'n'")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
