"""
FastAPI web interface for the Nutrition Calculator.
Provides REST API endpoints for nutritional calculations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

from nutrition_calculator import (
    UserProfile, 
    NutritionalTargets, 
    NutritionCalculator
)


app = FastAPI(
    title="Nutrition Calculator API",
    description="Calculate BMR, TDEE, and macronutrient targets using standard fitness formulas",
    version="1.0.0"
)

# Add CORS middleware for web frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CalculationRequest(BaseModel):
    """Request model for nutritional calculations."""
    age: int
    weight: float
    height: float
    gender: str
    activity_level: str
    goal: str
    diet_plan: str = "balanced"


class CalculationResponse(BaseModel):
    """Response model for nutritional calculations."""
    success: bool
    data: Dict[str, Any]
    message: str = ""


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Nutrition Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "/calculate": "POST - Calculate nutritional targets",
            "/activity-factors": "GET - Get available activity factors",
            "/diet-plans": "GET - Get available diet plans",
            "/goals": "GET - Get available goals",
            "/docs": "GET - API documentation"
        }
    }


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


@app.post("/calculate", response_model=CalculationResponse)
async def calculate_nutritional_targets(request: CalculationRequest):
    """
    Calculate nutritional targets based on user profile.
    
    Args:
        request: User profile data for calculations
        
    Returns:
        Calculated nutritional targets including BMR, TDEE, and macronutrients
    """
    try:
        # Create user profile from request
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
            "formula_info": {
                "bmr_formula": "Mifflin-St Jeor Equation",
                "tdee_formula": "BMR × Activity Factor",
                "activity_factor": NutritionCalculator.ACTIVITY_FACTORS[profile.activity_level],
                "calorie_adjustment": NutritionCalculator.GOAL_ADJUSTMENTS[profile.goal]
            }
        }
        
        return CalculationResponse(
            success=True,
            data=response_data,
            message="Nutritional targets calculated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Nutrition Calculator API is running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
