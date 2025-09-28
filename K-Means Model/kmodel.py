import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import euclidean_distances


# Load data
df = pd.read_json(r"C:\Users\thath\Desktop\OwlHacks\Meals Recipes\themealdb_calculated.jsonl", lines=True)

# Extract nutrition features from the nested structure
nutrition_df = pd.json_normalize(df['nutrition'].tolist())
df = pd.concat([df, nutrition_df], axis=1)

# Select features
features = ['Calories', 'Protein', 'Fat', 'Carbohydrates']
data_to_cluster = df[features]

#Scale data
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data_to_cluster)

# num of clusters
k = 20
kmeans_model = KMeans(n_clusters=k, random_state=42, n_init=10)

# train model
kmeans_model.fit(data_scaled)
df['cluster'] = kmeans_model.labels_

# calculate target vector
def get_per_meal_target(num_meal_preference, user_daily_macros):
    return np.array([
        user_daily_macros['Calories'] / num_meal_preference,
        user_daily_macros['Protein'] / num_meal_preference,
        user_daily_macros['Carbohydrates'] / num_meal_preference,
        user_daily_macros['Fat'] / num_meal_preference
    ]).reshape(1,-1)

def generate_recommendations(user_daily_macros, num_meal_preference=3, num_recommendations=16, exclude_meals=None):

    if exclude_meals and isinstance(exclude_meals, list):
        df = df[~df['Meal'].isin(exclude_meals)]
        # Handle case where too many meals are excluded
        if df.shape[0] < num_recommendations:
            print("Warning: Not enough unique meals available to generate a full new list.")

    scaled_per_meal_target = scaler.transform(get_per_meal_target(num_meal_preference, user_daily_macros))

    cluster_centers = kmeans_model.cluster_centers_
    distances = euclidean_distances(scaled_per_meal_target, cluster_centers)

    best_cluster_indices = np.argsort(distances[0])
    recommendation_dfs = []  # List to store DataFrames

    num_sample_clusters = 4  # Reduced number of clusters
    meals_per_cluster = num_recommendations / num_sample_clusters  # Round up
    print("Mealcount:" + str(meals_per_cluster))
    for cluster_idx in best_cluster_indices[:num_sample_clusters]:
        cluster_meals = df[df['cluster'] == cluster_idx].copy()  # Create a copy to avoid the warning
        if len(cluster_meals) == 0:  # Skip empty clusters
            continue
            
        cluster_meal_features = scaler.transform(cluster_meals[features])
        meal_distances = euclidean_distances(scaled_per_meal_target, cluster_meal_features)

        cluster_meals.loc[:, 'distance'] = meal_distances[0]  # Use .loc to avoid the warning
        
        # penalty for desserts
        dessert_penalty = 1.3
        cluster_meals.loc[cluster_meals['strCategory'] == 'Dessert', 'distance'] *= dessert_penalty

        top_meals = cluster_meals.nsmallest(int(meals_per_cluster), 'distance')
        recommendation_dfs.append(top_meals)  # Append DataFrame to list

    if recommendation_dfs:  # Check if we have any recommendations
        final_recommendations = pd.concat(recommendation_dfs, ignore_index=True)
        return final_recommendations.drop(columns=['distance'])
    else:
        return pd.DataFrame()  # Return empty DataFrame if no recommendations

if __name__ == "__main__":
    # Scenario 1: User wants to build muscle (High Protein, Moderate Carbs/Fat)
    muscle_gain_macros = {
        'Calories': 2200,
        'Protein': 180,
        'Carbohydrates': 200,
        'Fat': 75
    }
    print("--- Recommendations for Muscle Gain ---")
    muscle_gain_recs = generate_recommendations(muscle_gain_macros)
    print(muscle_gain_recs)
    print("\n" + "="*40 + "\n")

    # Scenario 2: User wants to lose weight (Moderate Protein, Low Carbs/Fat)
    weight_loss_macros = {
        'Calories': 1600,
        'Protein': 140,
        'Carbohydrates': 100,
        'Fat': 50
    }
    print("--- Recommendations for Weight Loss ---")
    weight_loss_recs = generate_recommendations(weight_loss_macros)
    print(weight_loss_recs)
    print(weight_loss_recs[['Calories','Protein', 'Carbohydrates', 'Fat']])

