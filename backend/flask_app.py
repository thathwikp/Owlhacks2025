"""
Central Flask backend that exposes nutrition calculation and (optionally) meal recommendations.
It mirrors the existing FastAPI endpoints so the current frontend (frontend/script.js)
continues to work without any changes.

Run:
    python backend/flask_app.py

The API will be available at: http://localhost:8000
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

# Ensure we can import local modules when running from project root or backend/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from nutrition_calculator_simple import (
    UserProfile,
    NutritionCalculator,
)

# Dynamically import the K-Means recommender (kmodel.py) from "K-Means Model/"
import importlib
import importlib.util

KMODEL_AVAILABLE = False
KMODEL_MODULE = None
KMODEL_DIR = None  # for diagnostics
KMODEL_LOAD_ERROR: Optional[str] = None


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"*": {"origins": "*"}})

    # Initialize KNN/KMeans recommendations module (kmodel.py) by absolute path
    global KMODEL_AVAILABLE, KMODEL_MODULE, KMODEL_DIR, KMODEL_LOAD_ERROR
    candidate_dir = os.path.join(os.path.dirname(CURRENT_DIR), "K-Means Model")
    kmodel_path = os.path.join(candidate_dir, "kmodel.py")
    if os.path.exists(kmodel_path):
        try:
            spec = importlib.util.spec_from_file_location("kmodel", kmodel_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[attr-defined]
                KMODEL_MODULE = module
                KMODEL_AVAILABLE = hasattr(module, "generate_recommendations")
                KMODEL_DIR = candidate_dir
                if not KMODEL_AVAILABLE:
                    KMODEL_LOAD_ERROR = "kmodel.py does not define generate_recommendations"
            else:
                KMODEL_AVAILABLE = False
                KMODEL_LOAD_ERROR = "Could not create import spec for kmodel.py"
        except Exception as e:
            app.logger.error(f"Failed to load kmodel.py: {e}")
            KMODEL_AVAILABLE = False
            KMODEL_LOAD_ERROR = str(e)
    else:
        app.logger.warning("kmodel.py not found. Meal recommendations will be unavailable.")
        KMODEL_AVAILABLE = False
        KMODEL_DIR = None
        KMODEL_LOAD_ERROR = "kmodel.py not found in 'K-Means Model' directory"

    @app.route("/", methods=["GET"])
    def root():
        meal_model_loaded = KMODEL_AVAILABLE
        return jsonify(
            {
                "message": "Meal Recommendation API (Flask)",
                "version": "1.0.0",
                "features": {
                    "nutrition_calculation": True,
                    "meal_clustering": meal_model_loaded,
                    "meal_recommendations": meal_model_loaded,
                },
                "endpoints": {
                    "/calculate-nutrition": "POST - Calculate nutritional targets",
                    "/recommend-meals": "POST - Get personalized meal recommendations",
                    "/meal-clusters": "GET - Get information about meal clusters",
                    "/activity-factors": "GET - Get available activity factors",
                    "/diet-plans": "GET - Get available diet plans",
                    "/goals": "GET - Get available goals",
                    "/health": "GET - Health check",
                },
            }
        )

    @app.route("/activity-factors", methods=["GET"])
    def get_activity_factors():
        return jsonify(
            {
                "activity_factors": {
                    "sedentary": {
                        "name": "Sedentary",
                        "description": "Little or no exercise",
                        "multiplier": 1.2,
                    },
                    "lightly_active": {
                        "name": "Lightly Active",
                        "description": "Light exercise/sports 1-3 days/week",
                        "multiplier": 1.375,
                    },
                    "moderately_active": {
                        "name": "Moderately Active",
                        "description": "Moderate exercise/sports 3-5 days/week",
                        "multiplier": 1.55,
                    },
                    "very_active": {
                        "name": "Very Active",
                        "description": "Hard exercise/sports 6-7 days a week",
                        "multiplier": 1.725,
                    },
                    "extra_active": {
                        "name": "Extra Active",
                        "description": "Very hard exercise/physical job",
                        "multiplier": 1.9,
                    },
                }
            }
        )

    @app.route("/diet-plans", methods=["GET"])
    def get_diet_plans():
        return jsonify(
            {
                "diet_plans": {
                    "balanced": {
                        "name": "Balanced",
                        "description": "40% Carbs, 30% Protein, 30% Fat",
                        "distribution": {"protein": 30, "carbs": 40, "fat": 30},
                    },
                    "high_protein": {
                        "name": "High Protein",
                        "description": "30% Carbs, 40% Protein, 30% Fat",
                        "distribution": {"protein": 40, "carbs": 30, "fat": 30},
                    },
                    "low_carb": {
                        "name": "Low Carb",
                        "description": "20% Carbs, 35% Protein, 45% Fat",
                        "distribution": {"protein": 35, "carbs": 20, "fat": 45},
                    },
                }
            }
        )

    @app.route("/goals", methods=["GET"])
    def get_goals():
        return jsonify(
            {
                "goals": {
                    "mild_weight_loss": {
                        "name": "Mild Weight Loss",
                        "description": "~0.5 lb/week loss",
                        "calorie_adjustment": -250,
                    },
                    "standard_weight_loss": {
                        "name": "Standard Weight Loss",
                        "description": "~1 lb/week loss",
                        "calorie_adjustment": -500,
                    },
                    "maintain": {
                        "name": "Maintain Weight",
                        "description": "Maintain current weight",
                        "calorie_adjustment": 0,
                    },
                    "mild_weight_gain": {
                        "name": "Mild Weight Gain",
                        "description": "~0.5 lb/week gain",
                        "calorie_adjustment": 250,
                    },
                    "standard_weight_gain": {
                        "name": "Standard Weight Gain",
                        "description": "~1 lb/week gain",
                        "calorie_adjustment": 500,
                    },
                }
            }
        )

    @app.route("/calculate-nutrition", methods=["POST"])
    def calculate_nutrition():
        try:
            body = request.get_json(force=True) or {}
            profile = UserProfile(
                age=int(body.get("age")),
                weight=float(body.get("weight")),
                height=float(body.get("height")),
                gender=str(body.get("gender")),
                activity_level=str(body.get("activity_level")),
                goal=str(body.get("goal")),
                diet_plan=str(body.get("diet_plan", "balanced")),
            )

            calculator = NutritionCalculator()
            targets = calculator.calculate_nutritional_targets(profile)

            response_data = {
                "user_profile": {
                    "age": profile.age,
                    "weight_kg": profile.weight,
                    "height_cm": profile.height,
                    "gender": profile.gender,
                    "activity_level": profile.activity_level,
                    "goal": profile.goal,
                    "diet_plan": profile.diet_plan,
                },
                "calculations": {
                    "bmr": targets.bmr,
                    "tdee": targets.tdee,
                    "target_calories": targets.target_calories,
                },
                "macronutrients": {
                    "protein": {
                        "grams": targets.protein_grams,
                        "percentage": targets.protein_percentage,
                        "calories": round(targets.protein_grams * 4, 2),
                    },
                    "carbohydrates": {
                        "grams": targets.carbs_grams,
                        "percentage": targets.carbs_percentage,
                        "calories": round(targets.carbs_grams * 4, 2),
                    },
                    "fat": {
                        "grams": targets.fat_grams,
                        "percentage": targets.fat_percentage,
                        "calories": round(targets.fat_grams * 9, 2),
                    },
                },
                "daily_breakdown": {
                    "meals_per_day": 3,
                    "calories_per_meal": round(targets.target_calories / 3, 1),
                    "protein_per_meal": round(targets.protein_grams / 3, 1),
                    "carbs_per_meal": round(targets.carbs_grams / 3, 1),
                    "fat_per_meal": round(targets.fat_grams / 3, 1),
                },
            }

            return jsonify({
                "success": True,
                "data": response_data,
                "message": "Nutritional targets calculated successfully",
            })
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"Internal server error: {e}"}), 500

    @app.route("/recommend-meals", methods=["POST"])
    def recommend_meals():
        if not KMODEL_AVAILABLE or KMODEL_MODULE is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Meal recommendation service is not available. kmodel.py not loaded.",
                    }
                ),
                503,
            )
        try:
            body = request.get_json(force=True) or {}
            user_profile = body.get("user_profile", {})
            meal_type = body.get("meal_type", "any")  # Unused but accepted
            count = int(body.get("count", 5))
            max_calories = body.get("max_calories")
            min_protein = body.get("min_protein")

            # Convert to expected dict for model
            # Also compute user's daily macro targets to feed kmodel
            profile = UserProfile(
                age=int(user_profile.get("age")),
                weight=float(user_profile.get("weight")),
                height=float(user_profile.get("height")),
                gender=str(user_profile.get("gender")),
                activity_level=str(user_profile.get("activity_level")),
                goal=str(user_profile.get("goal")),
                diet_plan=str(user_profile.get("diet_plan", "balanced")),
            )
            calc = NutritionCalculator()
            targets = calc.calculate_nutritional_targets(profile)

            user_daily_macros = {
                "Calories": float(targets.target_calories),
                "Protein": float(targets.protein_grams),
                "Carbohydrates": float(targets.carbs_grams),
                "Fat": float(targets.fat_grams),
            }

            # Call kmodel's recommender. It returns a DataFrame of meals.
            rec_df = KMODEL_MODULE.generate_recommendations(user_daily_macros, num_meal_preference=3, num_recommendations=max(count, 8))

            # Map to response format
            filtered_meals: List[Dict[str, Any]] = []
            for _, meal in rec_df.iterrows():
                # Apply optional filters
                if max_calories and meal.get("Calories", 0) > max_calories:
                    continue
                if min_protein and meal.get("Protein", 0) < min_protein:
                    continue

                meal_item = {
                    "name": meal.get("strMeal", "Meal"),
                    "category": meal.get("strCategory", "Unknown"),
                    "area": meal.get("strArea", "Unknown"),
                    "calories": round(float(meal.get("Calories", 0)), 1),
                    "protein": round(float(meal.get("Protein", 0)), 1),
                    "fat": round(float(meal.get("Fat", 0)), 1),
                    "carbohydrates": round(float(meal.get("Carbohydrates", 0)), 1),
                    "fiber": round(float(meal.get("Fiber", 0.0)), 1) if not pd.isna(meal.get("Fiber", 0.0)) else 0.0,
                    "sodium": round(float(meal.get("Sodium", 0.0)), 1) if not pd.isna(meal.get("Sodium", 0.0)) else 0.0,
                    "ingredients": meal.get("ingredients", []),
                    "instructions": meal.get("strInstructions", ""),
                    "similarity_score": float(meal.get("similarity_score", 0.0)) if "similarity_score" in meal else 0.0,
                    "cluster": int(meal.get("cluster", -1)) if "cluster" in meal else -1,
                }
                filtered_meals.append(meal_item)
                if len(filtered_meals) >= count:
                    break

            return jsonify(
                {
                    "success": True,
                    "user_targets": {"daily": user_daily_macros},
                    "recommended_meals": filtered_meals,
                    "cluster_info": {},
                    "message": f"Found {len(filtered_meals)} personalized meal recommendations",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": f"Error generating recommendations: {e}"}), 500

    @app.route("/meal-clusters", methods=["GET"])
    def meal_clusters():
        if not KMODEL_AVAILABLE:
            return jsonify({"success": False, "message": "Clustering service is not available"}), 503
        try:
            # kmodel.py does not provide clusters; return not implemented
            return jsonify({"success": False, "message": "Cluster summary not available with kmodel"}), 501
        except Exception as e:
            return jsonify({"success": False, "message": f"Error getting cluster information: {e}"}), 500

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "status": "healthy",
                "message": "Meal Recommendation API (Flask) is running",
                "clustering_available": KMODEL_AVAILABLE,
                "kmodel_dir": KMODEL_DIR,
                "kmodel_loaded": bool(KMODEL_MODULE),
                "kmodel_load_error": KMODEL_LOAD_ERROR,
            }
        )

    return app


app = create_app()

if __name__ == "__main__":
    # Run Flask development server on port 8000 to match frontend expectations
    app.run(host="0.0.0.0", port=8000, debug=True)
