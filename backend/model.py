import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import json
import pickle
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

class MealClusteringModel:
    def __init__(self, n_clusters=20):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.pca = PCA(n_components=2)
        self.cluster_descriptions = {}
        
    def load_and_prepare_data(self, data_file):
        """Load meal data from JSONL file and prepare features."""
        meals = []
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    meal = json.loads(line)
                    if 'nutrition' in meal:
                        nutrition = meal['nutrition']
                        meal_data = {
                            'strMeal': meal['strMeal'],
                            'strCategory': meal.get('strCategory', 'Unknown'),
                            'strArea': meal.get('strArea', 'Unknown'),
                            'Calories': nutrition.get('Calories', 0),
                            'Protein': nutrition.get('Protein', 0),
                            'Fat': nutrition.get('Fat', 0),
                            'Carbohydrates': nutrition.get('Carbohydrates', 0),
                            'Fiber': nutrition.get('Fiber', 0),
                            'Sodium': nutrition.get('Sodium', 0),
                            'ingredients': meal.get('ingredients', []),
                            'strInstructions': meal.get('strInstructions', '')
                        }
                        meals.append(meal_data)
                        
        except FileNotFoundError:
            print(f"Error: Data file '{data_file}' not found.")
            return None
            
        if not meals:
            print("No valid meals found in the data file.")
            return None
            
        self.df = pd.DataFrame(meals)
        
        # Filter out meals with zero calories
        self.df = self.df[self.df['Calories'] > 0]
        
        print(f"Loaded {len(self.df)} valid meals")
        return self.df
    
    def extract_features(self):
        """Extract numerical features for clustering."""
        # Primary nutritional features
        features = ['Calories', 'Protein', 'Fat', 'Carbohydrates', 'Fiber', 'Sodium']
        
        # Calculate derived features
        self.df['Protein_per_cal'] = self.df['Protein'] * 4 / (self.df['Calories'] + 1)  # +1 to avoid division by zero
        self.df['Fat_per_cal'] = self.df['Fat'] * 9 / (self.df['Calories'] + 1)
        self.df['Carb_per_cal'] = self.df['Carbohydrates'] * 4 / (self.df['Calories'] + 1)
        
        # Calorie density categories
        self.df['Calorie_density'] = self.df['Calories'] / 100  # Assuming 100g serving
        
        # Include derived features
        features.extend(['Protein_per_cal', 'Fat_per_cal', 'Carb_per_cal', 'Calorie_density'])
        
        self.features = features
        return self.df[features]
    
    def train_model(self, data_file):
        """Train the K-means clustering model."""
        # Load and prepare data
        if self.load_and_prepare_data(data_file) is None:
            return False
            
        # Extract features
        feature_data = self.extract_features()
        
        # Scale the features
        data_scaled = self.scaler.fit_transform(feature_data)
        
        # Train K-means model
        self.kmeans_model.fit(data_scaled)
        
        # Add cluster labels to dataframe
        self.df['cluster'] = self.kmeans_model.labels_
        
        # Generate cluster descriptions
        self._generate_cluster_descriptions()
        
        print(f"Model trained successfully with {self.n_clusters} clusters")
        return True
    
    def _generate_cluster_descriptions(self):
        """Generate descriptive names for each cluster based on nutritional profiles."""
        for cluster_id in range(self.n_clusters):
            cluster_data = self.df[self.df['cluster'] == cluster_id]
            
            if len(cluster_data) == 0:
                continue
                
            # Calculate average nutritional values
            avg_calories = cluster_data['Calories'].mean()
            avg_protein = cluster_data['Protein'].mean()
            avg_fat = cluster_data['Fat'].mean()
            avg_carbs = cluster_data['Carbohydrates'].mean()
            avg_fiber = cluster_data['Fiber'].mean()
            
            # Determine primary macronutrient
            protein_ratio = (avg_protein * 4) / avg_calories if avg_calories > 0 else 0
            fat_ratio = (avg_fat * 9) / avg_calories if avg_calories > 0 else 0
            carb_ratio = (avg_carbs * 4) / avg_calories if avg_calories > 0 else 0
            
            # Categorize based on dominant macronutrient and calorie content
            if avg_calories < 200:
                calorie_category = "Low-Calorie"
            elif avg_calories < 400:
                calorie_category = "Medium-Calorie"
            else:
                calorie_category = "High-Calorie"
            
            if protein_ratio > 0.3:
                macro_category = "High-Protein"
            elif fat_ratio > 0.35:
                macro_category = "High-Fat"
            elif carb_ratio > 0.5:
                macro_category = "High-Carb"
            else:
                macro_category = "Balanced"
            
            # Special categories
            if avg_fiber > 10:
                fiber_note = "High-Fiber"
            else:
                fiber_note = ""
            
            # Combine categories
            description_parts = [calorie_category, macro_category]
            if fiber_note:
                description_parts.append(fiber_note)
            
            description = " ".join(description_parts)
            
            # Get common categories and areas in this cluster
            common_categories = cluster_data['strCategory'].value_counts().head(3).index.tolist()
            common_areas = cluster_data['strArea'].value_counts().head(3).index.tolist()
            
            self.cluster_descriptions[cluster_id] = {
                'description': description,
                'avg_nutrition': {
                    'calories': round(avg_calories, 1),
                    'protein': round(avg_protein, 1),
                    'fat': round(avg_fat, 1),
                    'carbohydrates': round(avg_carbs, 1),
                    'fiber': round(avg_fiber, 1)
                },
                'common_categories': common_categories,
                'common_areas': common_areas,
                'meal_count': len(cluster_data),
                'sample_meals': cluster_data['strMeal'].head(5).tolist()
            }
    
    def predict_cluster(self, nutrition_values):
        """Predict which cluster a meal belongs to based on its nutrition."""
        # Create feature vector matching training data
        feature_vector = np.array([
            nutrition_values.get('Calories', 0),
            nutrition_values.get('Protein', 0),
            nutrition_values.get('Fat', 0),
            nutrition_values.get('Carbohydrates', 0),
            nutrition_values.get('Fiber', 0),
            nutrition_values.get('Sodium', 0),
            # Calculate derived features
            nutrition_values.get('Protein', 0) * 4 / (nutrition_values.get('Calories', 1)),
            nutrition_values.get('Fat', 0) * 9 / (nutrition_values.get('Calories', 1)),
            nutrition_values.get('Carbohydrates', 0) * 4 / (nutrition_values.get('Calories', 1)),
            nutrition_values.get('Calories', 0) / 100
        ]).reshape(1, -1)
        
        # Scale the features
        feature_scaled = self.scaler.transform(feature_vector)
        
        # Predict cluster
        cluster = self.kmeans_model.predict(feature_scaled)[0]
        return cluster
    
    def get_meal_recommendations(self, user_profile, top_n=10):
        """Get meal recommendations based on user profile and nutritional targets."""
        # Calculate user's nutritional targets (you can integrate with your nutrition calculator)
        from nutrition_calculator_simple import UserProfile, NutritionCalculator
        
        profile = UserProfile(
            age=user_profile['age'],
            weight=user_profile['weight'],
            height=user_profile['height'],
            gender=user_profile['gender'],
            activity_level=user_profile['activity_level'],
            goal=user_profile['goal'],
            diet_plan=user_profile.get('diet_plan', 'balanced')
        )
        
        calculator = NutritionCalculator()
        targets = calculator.calculate_nutritional_targets(profile)
        
        # Calculate target nutrition per meal (assuming 3 meals per day)
        target_per_meal = {
            'Calories': targets.target_calories / 3,
            'Protein': targets.protein_grams / 3,
            'Fat': targets.fat_grams / 3,
            'Carbohydrates': targets.carbs_grams / 3,
            'Fiber': 8,  # Approximate daily fiber target / 3
            'Sodium': 800  # Approximate daily sodium limit / 3
        }
        
        # Find the best matching cluster
        target_cluster = self.predict_cluster(target_per_meal)
        
        # Get meals from the target cluster and nearby clusters
        recommended_meals = []
        
        # Primary cluster meals
        cluster_meals = self.df[self.df['cluster'] == target_cluster].copy()
        
        # Calculate similarity scores based on nutritional distance
        for idx, meal in cluster_meals.iterrows():
            nutrition_distance = 0
            for nutrient in ['Calories', 'Protein', 'Fat', 'Carbohydrates']:
                target_val = target_per_meal[nutrient]
                meal_val = meal[nutrient]
                # Normalized distance
                nutrition_distance += abs(target_val - meal_val) / (target_val + 1)
            
            meal_dict = meal.to_dict()
            meal_dict['similarity_score'] = 1 / (1 + nutrition_distance)
            recommended_meals.append(meal_dict)
        
        # Sort by similarity score
        recommended_meals.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return {
            'target_cluster': target_cluster,
            'cluster_description': self.cluster_descriptions.get(target_cluster, {}),
            'recommended_meals': recommended_meals[:top_n],
            'nutritional_targets': {
                'per_meal': target_per_meal,
                'daily': {
                    'calories': targets.target_calories,
                    'protein': targets.protein_grams,
                    'fat': targets.fat_grams,
                    'carbohydrates': targets.carbs_grams
                }
            }
        }
    
    def save_model(self, model_path="meal_clustering_model.pkl"):
        """Save the trained model to disk."""
        model_data = {
            'kmeans_model': self.kmeans_model,
            'scaler': self.scaler,
            'cluster_descriptions': self.cluster_descriptions,
            'features': self.features,
            'n_clusters': self.n_clusters
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {model_path}")
    
    def load_model(self, model_path="meal_clustering_model.pkl"):
        """Load a trained model from disk."""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.kmeans_model = model_data['kmeans_model']
            self.scaler = model_data['scaler']
            self.cluster_descriptions = model_data['cluster_descriptions']
            self.features = model_data['features']
            self.n_clusters = model_data['n_clusters']
            
            print(f"Model loaded from {model_path}")
            return True
        except FileNotFoundError:
            print(f"Model file {model_path} not found.")
            return False
    
    def visualize_clusters(self, save_path="cluster_visualization.png"):
        """Visualize clusters using PCA."""
        if not hasattr(self, 'df') or self.df is None:
            print("No data loaded. Train the model first.")
            return
        
        # Prepare data for visualization
        feature_data = self.df[self.features]
        data_scaled = self.scaler.transform(feature_data)
        
        # Apply PCA for 2D visualization
        pca_data = self.pca.fit_transform(data_scaled)
        
        # Create scatter plot
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(pca_data[:, 0], pca_data[:, 1], 
                            c=self.df['cluster'], cmap='tab20', alpha=0.6)
        plt.colorbar(scatter)
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        plt.title('Meal Clusters Visualization (PCA)')
        
        # Add cluster centers
        centers_scaled = self.scaler.transform(self.kmeans_model.cluster_centers_)
        centers_pca = self.pca.transform(centers_scaled)
        plt.scatter(centers_pca[:, 0], centers_pca[:, 1], 
                   c='red', marker='x', s=200, linewidths=3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Visualization saved to {save_path}")
    
    def get_cluster_summary(self):
        """Get a summary of all clusters."""
        return self.cluster_descriptions

# Usage example
if __name__ == "__main__":
    # Initialize the model
    model = MealClusteringModel(n_clusters=20)
    
    # Train the model (replace with your data file path)
    data_file = "themealdb_calculated_data.jsonl"  # Output from nutrition_finder.py
    
    if model.train_model(data_file):
        # Save the trained model
        model.save_model("meal_clustering_model.pkl")
        
        # Visualize clusters
        model.visualize_clusters()
        
        # Print cluster summary
        print("\n=== CLUSTER SUMMARY ===")
        summary = model.get_cluster_summary()
        for cluster_id, info in summary.items():
            print(f"\nCluster {cluster_id}: {info['description']}")
            print(f"  Average Nutrition: {info['avg_nutrition']}")
            print(f"  Common Categories: {', '.join(info['common_categories'][:3])}")
            print(f"  Meal Count: {info['meal_count']}")
            print(f"  Sample Meals: {', '.join(info['sample_meals'][:3])}")
        
        # Example user profile for recommendations
        user_profile = {
            'age': 25,
            'weight': 70.0,
            'height': 175.0,
            'gender': 'male',
            'activity_level': 'moderately_active',
            'goal': 'maintain'
        }
        
        # Get meal recommendations
        recommendations = model.get_meal_recommendations(user_profile, top_n=5)
        
        print(f"\n=== MEAL RECOMMENDATIONS ===")
        print(f"Target Cluster: {recommendations['target_cluster']}")
        print(f"Cluster Description: {recommendations['cluster_description']['description']}")
        print(f"\nTop 5 Recommended Meals:")
        for i, meal in enumerate(recommendations['recommended_meals'], 1):
            print(f"{i}. {meal['strMeal']} (Score: {meal['similarity_score']:.3f})")
            print(f"   Nutrition: {meal['Calories']:.0f} cal, {meal['Protein']:.1f}g protein")