"""
Test examples demonstrating different nutritional calculation scenarios.
Shows various user profiles and their calculated nutritional targets.
"""

from nutrition_calculator_simple import UserProfile, NutritionCalculator


def test_scenario(name: str, profile: UserProfile):
    """Test a specific user scenario and display results."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"{'='*60}")
    
    calculator = NutritionCalculator()
    targets = calculator.calculate_nutritional_targets(profile)
    
    print(f"👤 Profile: {profile.age}yo {profile.gender}, {profile.weight}kg, {profile.height}cm")
    print(f"🏃 Activity: {profile.activity_level.replace('_', ' ').title()}")
    print(f"🎯 Goal: {profile.goal.replace('_', ' ').title()}")
    print(f"🥗 Diet: {profile.diet_plan.replace('_', ' ').title()}")
    
    print(f"\n📊 Results:")
    print(f"   BMR: {targets.bmr:.1f} cal/day")
    print(f"   TDEE: {targets.tdee:.1f} cal/day")
    print(f"   Target: {targets.target_calories:.1f} cal/day")
    
    print(f"\n🥗 Macros:")
    print(f"   Protein: {targets.protein_grams:.1f}g ({targets.protein_percentage}%)")
    print(f"   Carbs: {targets.carbs_grams:.1f}g ({targets.carbs_percentage}%)")
    print(f"   Fat: {targets.fat_grams:.1f}g ({targets.fat_percentage}%)")
    
    return targets


def run_all_examples():
    """Run all test scenarios."""
    print("NUTRITION CALCULATOR - TEST SCENARIOS")
    print("This demonstrates various user profiles and their nutritional targets.")
    
    # Scenario 1: Young male, moderate activity, weight loss
    scenario1 = UserProfile(
        age=25, weight=70.0, height=175.0, gender="male",
        activity_level="moderately_active", goal="standard_weight_loss",
        diet_plan="balanced"
    )
    test_scenario("Young Male - Weight Loss", scenario1)
    
    # Scenario 2: Middle-aged female, sedentary, maintenance
    scenario2 = UserProfile(
        age=45, weight=60.0, height=165.0, gender="female",
        activity_level="sedentary", goal="maintain",
        diet_plan="high_protein"
    )
    test_scenario("Middle-aged Female - Maintenance", scenario2)
    
    # Scenario 3: Young female athlete, very active, weight gain
    scenario3 = UserProfile(
        age=22, weight=55.0, height=170.0, gender="female",
        activity_level="very_active", goal="standard_weight_gain",
        diet_plan="high_protein"
    )
    test_scenario("Female Athlete - Weight Gain", scenario3)
    
    # Scenario 4: Older male, lightly active, mild weight loss
    scenario4 = UserProfile(
        age=60, weight=85.0, height=180.0, gender="male",
        activity_level="lightly_active", goal="mild_weight_loss",
        diet_plan="low_carb"
    )
    test_scenario("Older Male - Mild Weight Loss", scenario4)
    
    # Scenario 5: Young female, extra active, maintenance
    scenario5 = UserProfile(
        age=28, weight=65.0, height=168.0, gender="female",
        activity_level="extra_active", goal="maintain",
        diet_plan="balanced"
    )
    test_scenario("Active Female - Maintenance", scenario5)
    
    # Scenario 6: Male bodybuilder, extra active, weight gain
    scenario6 = UserProfile(
        age=30, weight=90.0, height=185.0, gender="male",
        activity_level="extra_active", goal="mild_weight_gain",
        diet_plan="high_protein"
    )
    test_scenario("Male Bodybuilder - Weight Gain", scenario6)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print("These examples show how the calculator adapts to different:")
    print("• Age groups (young adults to seniors)")
    print("• Gender differences (metabolic variations)")
    print("• Activity levels (sedentary to highly active)")
    print("• Fitness goals (weight loss, maintenance, weight gain)")
    print("• Diet preferences (balanced, high-protein, low-carb)")
    print("\nThe calculator uses scientifically validated formulas to provide")
    print("personalized nutritional targets for each individual.")


def compare_diet_plans():
    """Compare different diet plans for the same user profile."""
    print(f"\n{'='*60}")
    print("DIET PLAN COMPARISON")
    print(f"{'='*60}")
    
    # Base profile
    base_profile = UserProfile(
        age=30, weight=75.0, height=175.0, gender="male",
        activity_level="moderately_active", goal="maintain",
        diet_plan="balanced"  # Will be overridden
    )
    
    calculator = NutritionCalculator()
    
    print("Same user profile (30yo male, 75kg, 175cm, moderate activity, maintenance goal)")
    print("with different diet plans:\n")
    
    for diet_plan in ["balanced", "high_protein", "low_carb"]:
        profile = UserProfile(
            age=base_profile.age, weight=base_profile.weight, 
            height=base_profile.height, gender=base_profile.gender,
            activity_level=base_profile.activity_level, goal=base_profile.goal,
            diet_plan=diet_plan
        )
        
        targets = calculator.calculate_nutritional_targets(profile)
        
        print(f"🥗 {diet_plan.replace('_', ' ').title()} Diet:")
        print(f"   Protein: {targets.protein_grams:.1f}g ({targets.protein_percentage}%)")
        print(f"   Carbs: {targets.carbs_grams:.1f}g ({targets.carbs_percentage}%)")
        print(f"   Fat: {targets.fat_grams:.1f}g ({targets.fat_percentage}%)")
        print()


if __name__ == "__main__":
    run_all_examples()
    compare_diet_plans()
