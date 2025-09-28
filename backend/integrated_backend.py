"""
Integrated Meal Recommendation Backend API
Combines nutrition calculation with meal clustering and recommendations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn
import os
import sys

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your modules
from nutrition_calculator_simple import (
    UserProfile, 
    NutritionalTargets, 
    NutritionCalculator
)

# Try to import the clustering model
try:
    from model import MealClusteringModel
    CLUSTERING_AVAILABLE = True
except ImportError:
    print("Warning: Clustering model not available. Some features will be disabled.")
    CLUSTERING_AVAILABLE = False

app = FastAPI(
    title="Meal Recommendation API",
    description="Integrated nutrition calculation and meal recommendation system",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
meal_model = None

if CLUSTERING_AVAILABLE:
    try:
        meal_model = MealClusteringModel()
        # Try to load pre-trained model
        if not meal_model.load_model("meal_clustering_model.pkl"):
            print("No pre-trained model found. Training new model...")
            # Try to train with available data
            if os.path.exists("themealdb_calculated_data.jsonl"):
                meal_model.train_model("themealdb_calculated_data.jsonl")
                meal_model.save_model("meal_clustering_model.pkl")
            else:
                print("Warning: No meal data found. Meal recommendations will be limited.")
                meal_model = None
    except Exception as e:
        print(f"Error initializing clustering model: {e}")
        meal_model = None

# Pydantic models
class UserProfileRequest(BaseModel):
    age: int = Field(..., ge=1, le=120, description="Age in years")
    weight: float = Field(..., ge=20, le=300, description="Weight in kg")
    height: float = Field(..., ge=100, le=250, description="Height in cm")
    gender: str = Field(..., pattern="^(male|female)$", description="Gender")
    activity_level: str = Field(
        ..., 
        pattern="^(sedentary|lightly_active|moderately_active|very_active|extra_active)$",
        description="Activity level"
    )
    goal: str = Field(
        ..., 
        pattern="^(maintain|mild_weight_loss|standard_weight_loss|mild_weight_gain|standard_weight_gain)$",
        description="Fitness goal"
    )
    diet_plan: str = Field(
        "balanced", 
        pattern="^(balanced|high_protein|low_carb)$",
        description="Diet plan preference"
    )
    
    # Additional preferences for meal recommendations
    dietary_restrictions: Optional[List[str]] = Field(
        default_factory=list,
        description="List of dietary restrictions (vegetarian, vegan, etc.)"
    )
    cuisine_preferences: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred cuisines"
    )
    exclude_ingredients: Optional[List[str]] = Field(
        default_factory=list,
        description="Ingredients to exclude"
    )

class NutritionResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str = ""

class MealRecommendationRequest(BaseModel):
    user_profile: UserProfileRequest
    meal_type: str = Field("any", pattern="^(breakfast|lunch|dinner|snack|any)$")
    max_calories: Optional[int] = Field(None, description="Maximum calories per meal")
    min_protein: Optional[int] = Field(None, description="Minimum protein per meal")
    count: int = Field(5, ge=1, le=20, description="Number of recommendations")

class MealItem(BaseModel):
    name: str
    category: str
    area: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    fiber: float
    sodium: float
    ingredients: List[Dict[str, Any]]
    instructions: str
    similarity_score: float
    cluster: int

class MealRecommendationResponse(BaseModel):
    success: bool
    user_targets: Dict[str, Any]
    recommended_meals: List[MealItem]
    cluster_info: Dict[str, Any]
    message: str = ""

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Meal Recommendation API",
        "version": "2.0.0",
        "features": {
            "nutrition_calculation": True,
            "meal_clustering": CLUSTERING_AVAILABLE and meal_model is not None,
            "meal_recommendations": CLUSTERING_AVAILABLE and meal_model is not None
        },
        "endpoints": {
            "/calculate-nutrition": "POST - Calculate nutritional targets",
            "/recommend-meals": "POST - Get personalized meal recommendations", 
            "/meal-clusters": "GET - Get information about meal clusters",
            "/activity-factors": "GET - Get available activity factors",
            "/diet-plans": "GET - Get available diet plans",
            "/goals": "GET - Get available goals",
            "/docs": "GET - API documentation"
        }
    }

@app.post("/calculate-nutrition", response_model=NutritionResponse)
async def calculate_nutrition(request: UserProfileRequest):
    """Calculate nutritional targets based on user profile."""
    try:
        # Create user profile
        profile = UserProfile(
            age=request.age,
            weight=request.weight,
            height=request.height,
            gender=request.gender,
            activity_level=request.activity_level,
            goal=request.goal,
            diet_plan=request.diet_plan
        )
        
        # Calculate nutritional targets
        calculator = NutritionCalculator()
        targets = calculator.calculate_nutritional_targets(profile)
        
        # Prepare response data
        response_data = {
            "user_profile": {
                "age": profile.age,
                "weight_kg": profile.weight,
                "height_cm": profile.height,
                "gender": profile.gender,
                "activity_level": profile.activity_level,
                "goal": profile.goal,
                "diet_plan": profile.diet_plan
            },
            "calculations": {
                "bmr": targets.bmr,
                "tdee": targets.tdee,
                "target_calories": targets.target_calories
            },
            "macronutrients": {
                "protein": {
                    "grams": targets.protein_grams,
                    "percentage": targets.protein_percentage,
                    "calories": round(targets.protein_grams * 4, 2)
                },
                "carbohydrates": {
                    "grams": targets.carbs_grams,
                    "percentage": targets.carbs_percentage,
                    "calories": round(targets.carbs_grams * 4, 2)
                },
                "fat": {
                    "grams": targets.fat_grams,
                    "percentage": targets.fat_percentage,
                    "calories": round(targets.fat_grams * 9, 2)
                }
            },
            "daily_breakdown": {
                "meals_per_day": 3,
                "calories_per_meal": round(targets.target_calories / 3, 1),
                "protein_per_meal": round(targets.protein_grams / 3, 1),
                "carbs_per_meal": round(targets.carbs_grams / 3, 1),
                "fat_per_meal": round(targets.fat_grams / 3, 1)
            }
        }
        
        return NutritionResponse(
            success=True,
            data=response_data,
            message="Nutritional targets calculated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/recommend-meals", response_model=MealRecommendationResponse)
async def recommend_meals(request: MealRecommendationRequest):
    """Get personalized meal recommendations based on user profile and clustering."""
    if not CLUSTERING_AVAILABLE or meal_model is None:
        raise HTTPException(
            status_code=503,
            detail="Meal recommendation service is not available. Clustering model not loaded."
        )
    
    try:
        # Convert request to dictionary for the clustering model
        user_profile = {
            'age': request.user_profile.age,
            'weight': request.user_profile.weight,
            'height': request.user_profile.height,
            'gender': request.user_profile.gender,
            'activity_level': request.user_profile.activity_level,
            'goal': request.user_profile.goal,
            'diet_plan': request.user_profile.diet_plan
        }
        
        # Get meal recommendations from clustering model
        recommendations = meal_model.get_meal_recommendations(
            user_profile, 
            top_n=request.count
        )
        
        # Filter based on additional criteria
        filtered_meals = []
        for meal in recommendations['recommended_meals']:
            # Apply calorie filter
            if request.max_calories and meal['Calories'] > request.max_calories:
                continue
                
            # Apply protein filter
            if request.min_protein and meal['Protein'] < request.min_protein:
                continue
                
            # Apply dietary restrictions (basic filtering)
            if request.user_profile.dietary_restrictions:
                meal_ingredients = [ing['name'].lower() for ing in meal.get('ingredients', [])]
                skip_meal = False
                
                for restriction in request.user_profile.dietary_restrictions:
                    if restriction.lower() == 'vegetarian':
                        meat_keywords = ['beef', 'pork', 'chicken', 'turkey', 'fish', 'lamb', 'bacon']
                        if any(keyword in ' '.join(meal_ingredients) for keyword in meat_keywords):
                            skip_meal = True
                            break
                    elif restriction.lower() == 'vegan':
                        animal_keywords = ['beef', 'pork', 'chicken', 'turkey', 'fish', 'lamb', 'bacon', 
                                         'milk', 'cheese', 'butter', 'egg', 'honey']
                        if any(keyword in ' '.join(meal_ingredients) for keyword in animal_keywords):
                            skip_meal = True
                            break
                
                if skip_meal:
                    continue
            
            # Apply ingredient exclusions
            if request.user_profile.exclude_ingredients:
                meal_ingredients_str = ' '.join([ing['name'].lower() for ing in meal.get('ingredients', [])])
                if any(excluded.lower() in meal_ingredients_str 
                      for excluded in request.user_profile.exclude_ingredients):
                    continue
            
            # Convert to response format
            meal_item = MealItem(
                name=meal['strMeal'],
                category=meal['strCategory'],
                area=meal['strArea'],
                calories=round(meal['Calories'], 1),
                protein=round(meal['Protein'], 1),
                fat=round(meal['Fat'], 1),
                carbohydrates=round(meal['Carbohydrates'], 1),
                fiber=round(meal['Fiber'], 1),
                sodium=round(meal['Sodium'], 1),
                ingredients=meal.get('ingredients', []),
                instructions=meal['strInstructions'],
                similarity_score=round(meal['similarity_score'], 3),
                cluster=meal['cluster']
            )
            filtered_meals.append(meal_item)
            
            if len(filtered_meals) >= request.count:
                break
        
        return MealRecommendationResponse(
            success=True,
            user_targets=recommendations['nutritional_targets'],
            recommended_meals=filtered_meals,
            cluster_info={
                "target_cluster": recommendations['target_cluster'],
                "description": recommendations['cluster_description']
            },
            message=f"Found {len(filtered_meals)} personalized meal recommendations"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/meal-clusters")
async def get_meal_clusters():
    """Get information about all meal clusters."""
    if not CLUSTERING_AVAILABLE or meal_model is None:
        raise HTTPException(
            status_code=503,
            detail="Clustering service is not available"
        )
    
    try:
        cluster_summary = meal_model.get_cluster_summary()
        return {
            "success": True,
            "clusters": cluster_summary,
            "total_clusters": len(cluster_summary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cluster information: {str(e)}")

@app.get("/activity-factors")
async def get_activity_factors():
    """Get available activity factors and their multipliers."""
    return {
        "activity_factors": {
            "sedentary": {
                "name": "Sedentary",
                "description": "Little or no exercise",
                "multiplier": 1.2
            },
            "lightly_active": {
                "name": "Lightly Active",
                "description": "Light exercise/sports 1-3 days/week",
                "multiplier": 1.375
            },
            "moderately_active": {
                "name": "Moderately Active",
                "description": "Moderate exercise/sports 3-5 days/week",
                "multiplier": 1.55
            },
            "very_active": {
                "name": "Very Active",
                "description": "Hard exercise/sports 6-7 days a week",
                "multiplier": 1.725
            },
            "extra_active": {
                "name": "Extra Active",
                "description": "Very hard exercise/physical job",
                "multiplier": 1.9
            }
        }
    }


@app.get("/diet-plans")
async def get_diet_plans():
    """Get available diet plans and their macronutrient distributions."""
    return {
        "diet_plans": {
            "balanced": {
                "name": "Balanced",
                "description": "40% Carbs, 30% Protein, 30% Fat",
                "distribution": {"protein": 30, "carbs": 40, "fat": 30}
            },
            "high_protein": {
                "name": "High Protein",
                "description": "30% Carbs, 40% Protein, 30% Fat",
                "distribution": {"protein": 40, "carbs": 30, "fat": 30}
            },
            "low_carb": {
                "name": "Low Carb",
                "description": "20% Carbs, 35% Protein, 45% Fat",
                "distribution": {"protein": 35, "carbs": 20, "fat": 45}
            }
        }
    }


@app.get("/goals")
async def get_goals():
    """Get available fitness goals and their calorie adjustments."""
    return {
        "goals": {
            "mild_weight_loss": {
                "name": "Mild Weight Loss",
                "description": "~0.5 lb/week loss",
                "calorie_adjustment": -250
            },
            "standard_weight_loss": {
                "name": "Standard Weight Loss",
                "description": "~1 lb/week loss",
                "calorie_adjustment": -500
            },
            "maintain": {
                "name": "Maintain Weight",
                "description": "Maintain current weight",
                "calorie_adjustment": 0
            },
            "mild_weight_gain": {
                "name": "Mild Weight Gain",
                "description": "~0.5 lb/week gain",
                "calorie_adjustment": 250
            },
            "standard_weight_gain": {
                "name": "Standard Weight Gain",
                "description": "~1 lb/week gain",
                "calorie_adjustment": 500
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "message": "Meal Recommendation API is running",
        "clustering_available": CLUSTERING_AVAILABLE and meal_model is not None
    }


if __name__ == "__main__":
    print("Starting Meal Recommendation API...")
    print("=" * 50)
    print("Features:")
    print(f"  - Nutrition Calculation: ✅ Available")
    print(f"  - Meal Clustering: {'✅ Available' if CLUSTERING_AVAILABLE and meal_model else '❌ Not Available'}")
    print(f"  - Meal Recommendations: {'✅ Available' if CLUSTERING_AVAILABLE and meal_model else '❌ Not Available'}")
    print("=" * 50)
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)