# Nutrition Calculator - Do-It-Yourself Implementation

A comprehensive nutritional calculator that implements standard fitness calculation formulas for BMR, TDEE, and macronutrient targets. This project provides both a simple Python implementation and a full-featured FastAPI web service.

## 🎯 Features

- **BMR Calculation**: Uses the scientifically validated Mifflin-St Jeor equation
- **TDEE Calculation**: Accounts for various activity levels with standard multipliers
- **Goal-Based Adjustments**: Supports weight loss, maintenance, and weight gain goals
- **Multiple Diet Plans**: Balanced, High-Protein, and Low-Carb macronutrient distributions
- **Multiple Interfaces**: Command-line, Python API, and REST API
- **Input Validation**: Comprehensive error handling and data validation
- **No External Dependencies**: Core calculator works with just Python standard library

## 🚀 Quick Start

### Simple Version (No Dependencies)

```bash
python nutrition_calculator_simple.py
```

### Full API Version

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web API
python api.py

# Or run the CLI
python cli.py
```

## 📊 How It Works

### Step 1: Basal Metabolic Rate (BMR)
Uses the **Mifflin-St Jeor equation**:
```
BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age_years) + gender_constant
```
- **Male**: +5 calories
- **Female**: -161 calories

### Step 2: Total Daily Energy Expenditure (TDEE)
```
TDEE = BMR × Activity Factor
```

**Activity Factors:**
- Sedentary: 1.2
- Lightly Active: 1.375
- Moderately Active: 1.55
- Very Active: 1.725
- Extra Active: 1.9

### Step 3: Goal-Based Calorie Adjustment
```
Target Calories = TDEE + Goal Adjustment
```

**Goal Adjustments:**
- Mild Weight Loss (~0.5 lb/week): -250 calories
- Standard Weight Loss (~1 lb/week): -500 calories
- Maintain Weight: 0 calories
- Mild Weight Gain (~0.5 lb/week): +250 calories
- Standard Weight Gain (~1 lb/week): +500 calories

### Step 4: Macronutrient Distribution
Based on selected diet plan:

**Balanced (30% Protein, 40% Carbs, 30% Fat):**
- Protein: (Target Calories × 0.30) ÷ 4 grams
- Carbs: (Target Calories × 0.40) ÷ 4 grams
- Fat: (Target Calories × 0.30) ÷ 9 grams

**High Protein (40% Protein, 30% Carbs, 30% Fat):**
- Protein: (Target Calories × 0.40) ÷ 4 grams
- Carbs: (Target Calories × 0.30) ÷ 4 grams
- Fat: (Target Calories × 0.30) ÷ 9 grams

**Low Carb (35% Protein, 20% Carbs, 45% Fat):**
- Protein: (Target Calories × 0.35) ÷ 4 grams
- Carbs: (Target Calories × 0.20) ÷ 4 grams
- Fat: (Target Calories × 0.45) ÷ 9 grams

## 💻 Usage Examples

### Python API Usage

```python
from nutrition_calculator_simple import UserProfile, NutritionCalculator

# Create user profile
profile = UserProfile(
    age=25,
    weight=70.0,  # kg
    height=175.0,  # cm
    gender="male",
    activity_level="moderately_active",
    goal="standard_weight_loss",
    diet_plan="balanced"
)

# Calculate nutritional targets
calculator = NutritionCalculator()
targets = calculator.calculate_nutritional_targets(profile)

print(f"BMR: {targets.bmr} calories/day")
print(f"TDEE: {targets.tdee} calories/day")
print(f"Target Calories: {targets.target_calories} calories/day")
print(f"Protein: {targets.protein_grams}g")
print(f"Carbs: {targets.carbs_grams}g")
print(f"Fat: {targets.fat_grams}g")
```

### REST API Usage

Start the API server:
```bash
python api.py
```

Make a POST request to `/calculate`:
```bash
curl -X POST "http://localhost:8000/calculate" \
     -H "Content-Type: application/json" \
     -d '{
       "age": 25,
       "weight": 70.0,
       "height": 175.0,
       "gender": "male",
       "activity_level": "moderately_active",
       "goal": "standard_weight_loss",
       "diet_plan": "balanced"
     }'
```

### CLI Usage

Run the interactive command-line interface:
```bash
python cli.py
```

Follow the prompts to enter your information and get personalized nutritional targets.

## 📁 Project Structure

```
├── nutrition_calculator_simple.py    # Core calculator (no dependencies)
├── nutrition_calculator.py           # Full-featured version with Pydantic
├── api.py                           # FastAPI web service
├── cli.py                           # Command-line interface
├── requirements.txt                 # Python dependencies
└── README.md                        # This documentation
```

## 🔧 API Endpoints

When running the FastAPI server (`python api.py`):

- `GET /` - API information and available endpoints
- `POST /calculate` - Calculate nutritional targets
- `GET /activity-factors` - Get available activity levels
- `GET /diet-plans` - Get available diet plans
- `GET /goals` - Get available fitness goals
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## 📋 Input Parameters

### Required Parameters
- **age**: Integer (1-120 years)
- **weight**: Float (20-300 kg)
- **height**: Float (100-250 cm)
- **gender**: String ("male" or "female")
- **activity_level**: String (see activity factors above)
- **goal**: String (see goal adjustments above)

### Optional Parameters
- **diet_plan**: String ("balanced", "high_protein", "low_carb") - Default: "balanced"

## 📈 Example Output

```json
{
  "success": true,
  "data": {
    "user_profile": {
      "age": 25,
      "weight_kg": 70.0,
      "height_cm": 175.0,
      "gender": "male",
      "activity_level": "moderately_active",
      "goal": "standard_weight_loss",
      "diet_plan": "balanced"
    },
    "calculations": {
      "bmr": 1673.75,
      "tdee": 2594.31,
      "target_calories": 2094.31
    },
    "macronutrients": {
      "protein": {
        "grams": 157.07,
        "percentage": 30,
        "calories": 628.28
      },
      "carbohydrates": {
        "grams": 209.43,
        "percentage": 40,
        "calories": 837.72
      },
      "fat": {
        "grams": 69.81,
        "percentage": 30,
        "calories": 628.29
      }
    }
  },
  "message": "Nutritional targets calculated successfully"
}
```

## 🎓 Scientific Background

This implementation is based on established scientific formulas:

1. **Mifflin-St Jeor Equation**: The most accurate BMR formula currently available, validated in multiple studies
2. **Activity Factors**: Based on the Harris-Benedict and WHO recommendations for physical activity levels
3. **Macronutrient Ratios**: Follow standard dietary guidelines and popular diet approaches

## 🔒 Validation & Error Handling

- Input validation for all parameters (age, weight, height ranges)
- Gender and activity level validation
- Comprehensive error messages
- Graceful handling of edge cases

## 🚀 Deployment Options

### Local Development
```bash
python api.py  # Runs on http://localhost:8000
```

### Production Deployment
The FastAPI application can be deployed to:
- Heroku
- AWS Lambda
- Google Cloud Run
- DigitalOcean App Platform
- Any containerized environment

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📞 Support

For questions or issues, please open a GitHub issue or contact the development team.

---

**Note**: This calculator provides general guidance and should not replace professional medical or nutritional advice. Always consult with healthcare professionals for personalized recommendations.