"""
Nutrition Calculator - Simple Implementation (No External Dependencies)
Implements standard fitness calculation formulas for BMR, TDEE, and macronutrient targets.
"""

from typing import Dict, Literal
from dataclasses import dataclass


@dataclass
class UserProfile:
    """User profile data for nutritional calculations."""
    age: int
    weight: float  # kg
    height: float  # cm
    gender: Literal["male", "female"]
    activity_level: Literal[
        "sedentary", 
        "lightly_active", 
        "moderately_active", 
        "very_active", 
        "extra_active"
    ]
    goal: Literal[
        "maintain", 
        "mild_weight_loss", 
        "standard_weight_loss", 
        "mild_weight_gain", 
        "standard_weight_gain"
    ]
    diet_plan: Literal["balanced", "high_protein", "low_carb"] = "balanced"
    
    def __post_init__(self):
        """Validate inputs after initialization."""
        if self.age < 1 or self.age > 120:
            raise ValueError('Age must be between 1-120 years')
        if self.weight < 20 or self.weight > 300:
            raise ValueError('Weight must be between 20-300 kg')
        if self.height < 100 or self.height > 250:
            raise ValueError('Height must be between 100-250 cm')


@dataclass
class NutritionalTargets:
    """Calculated nutritional targets."""
    bmr: float  # Basal Metabolic Rate (calories/day)
    tdee: float  # Total Daily Energy Expenditure (calories/day)
    target_calories: float  # Target daily calorie intake
    
    # Macronutrient targets (in grams)
    protein_grams: float
    carbs_grams: float
    fat_grams: float
    
    # Macronutrient distribution (percentages)
    protein_percentage: float
    carbs_percentage: float
    fat_percentage: float


class NutritionCalculator:
    """Main calculator class implementing all nutritional formulas."""
    
    # Activity factors for TDEE calculation
    ACTIVITY_FACTORS = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    
    # Diet plan macronutrient distributions (protein, carbs, fat percentages)
    DIET_PLANS = {
        "balanced": (30, 40, 30),
        "high_protein": (40, 30, 30),
        "low_carb": (35, 20, 45)
    }
    
    # Goal-based calorie adjustments
    GOAL_ADJUSTMENTS = {
        "mild_weight_loss": -250,      # ~0.5 lb/week
        "standard_weight_loss": -500,  # ~1 lb/week
        "maintain": 0,
        "mild_weight_gain": 250,       # ~0.5 lb/week
        "standard_weight_gain": 500    # ~1 lb/week
    }
    
    @staticmethod
    def calculate_bmr(age: int, weight: float, height: float, gender: str) -> float:
        """
        Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.
        
        Args:
            age: Age in years
            weight: Weight in kg
            height: Height in cm
            gender: "male" or "female"
            
        Returns:
            BMR in calories per day
        """
        # Mifflin-St Jeor equation
        bmr = (10 * weight) + (6.25 * height) - (5 * age)
        
        # Add gender constant
        if gender == "male":
            bmr += 5
        else:  # female
            bmr -= 161
            
        return round(bmr, 2)
    
    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        """
        Calculate Total Daily Energy Expenditure.
        
        Args:
            bmr: Basal Metabolic Rate
            activity_level: Activity level string
            
        Returns:
            TDEE in calories per day
        """
        activity_factor = NutritionCalculator.ACTIVITY_FACTORS[activity_level]
        return round(bmr * activity_factor, 2)
    
    @staticmethod
    def calculate_target_calories(tdee: float, goal: str) -> float:
        """
        Calculate target daily calorie intake based on goal.
        
        Args:
            tdee: Total Daily Energy Expenditure
            goal: Fitness goal
            
        Returns:
            Target calories per day
        """
        adjustment = NutritionCalculator.GOAL_ADJUSTMENTS[goal]
        return round(tdee + adjustment, 2)
    
    @staticmethod
    def calculate_macronutrients(
        target_calories: float, 
        diet_plan: str = "balanced"
    ) -> Dict[str, float]:
        """
        Calculate macronutrient targets based on diet plan.
        
        Args:
            target_calories: Target daily calories
            diet_plan: Diet plan preference
            
        Returns:
            Dictionary with macronutrient targets in grams
        """
        protein_pct, carbs_pct, fat_pct = NutritionCalculator.DIET_PLANS[diet_plan]
        
        # Convert percentages to calories, then to grams
        protein_calories = target_calories * (protein_pct / 100)
        carbs_calories = target_calories * (carbs_pct / 100)
        fat_calories = target_calories * (fat_pct / 100)
        
        # Convert calories to grams (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
        protein_grams = round(protein_calories / 4, 2)
        carbs_grams = round(carbs_calories / 4, 2)
        fat_grams = round(fat_calories / 9, 2)
        
        return {
            "protein_grams": protein_grams,
            "carbs_grams": carbs_grams,
            "fat_grams": fat_grams,
            "protein_percentage": protein_pct,
            "carbs_percentage": carbs_pct,
            "fat_percentage": fat_pct
        }
    
    @classmethod
    def calculate_nutritional_targets(cls, profile: UserProfile) -> NutritionalTargets:
        """
        Calculate complete nutritional targets for a user profile.
        
        Args:
            profile: UserProfile object with user data
            
        Returns:
            NutritionalTargets object with all calculations
        """
        # Step 1: Calculate BMR
        bmr = cls.calculate_bmr(
            profile.age, 
            profile.weight, 
            profile.height, 
            profile.gender
        )
        
        # Step 2: Calculate TDEE
        tdee = cls.calculate_tdee(bmr, profile.activity_level)
        
        # Step 3: Calculate target calories based on goal
        target_calories = cls.calculate_target_calories(tdee, profile.goal)
        
        # Step 4: Calculate macronutrients
        macros = cls.calculate_macronutrients(target_calories, profile.diet_plan)
        
        return NutritionalTargets(
            bmr=bmr,
            tdee=tdee,
            target_calories=target_calories,
            **macros
        )


def example_calculation():
    """Example calculation to demonstrate the calculator."""
    # Example user profile
    profile = UserProfile(
        age=25,
        weight=70.0,  # kg
        height=175.0,  # cm
        gender="male",
        activity_level="moderately_active",
        goal="standard_weight_loss",
        diet_plan="balanced"
    )
    
    # Calculate targets
    calculator = NutritionCalculator()
    targets = calculator.calculate_nutritional_targets(profile)
    
    print("=== Nutritional Calculation Example ===")
    print(f"User Profile:")
    print(f"  Age: {profile.age} years")
    print(f"  Weight: {profile.weight} kg")
    print(f"  Height: {profile.height} cm")
    print(f"  Gender: {profile.gender}")
    print(f"  Activity Level: {profile.activity_level}")
    print(f"  Goal: {profile.goal}")
    print(f"  Diet Plan: {profile.diet_plan}")
    print()
    print(f"Calculated Targets:")
    print(f"  BMR: {targets.bmr} calories/day")
    print(f"  TDEE: {targets.tdee} calories/day")
    print(f"  Target Calories: {targets.target_calories} calories/day")
    print()
    print(f"Macronutrient Targets:")
    print(f"  Protein: {targets.protein_grams}g ({targets.protein_percentage}%)")
    print(f"  Carbohydrates: {targets.carbs_grams}g ({targets.carbs_percentage}%)")
    print(f"  Fat: {targets.fat_grams}g ({targets.fat_percentage}%)")
    
    # Calculate calories from each macro
    protein_calories = targets.protein_grams * 4
    carbs_calories = targets.carbs_grams * 4
    fat_calories = targets.fat_grams * 9
    
    print(f"\nCalorie Breakdown:")
    print(f"  Protein: {protein_calories} calories")
    print(f"  Carbohydrates: {carbs_calories} calories")
    print(f"  Fat: {fat_calories} calories")
    print(f"  Total: {protein_calories + carbs_calories + fat_calories} calories")
    
    return targets


if __name__ == "__main__":
    example_calculation()
