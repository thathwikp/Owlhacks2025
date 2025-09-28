import pandas as pd
import numpy as np
import os


# Optional sklearn imports with graceful fallback
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import euclidean_distances
    _SKLEARN_AVAILABLE = True
except Exception:
    _SKLEARN_AVAILABLE = False


# Load data (repository-relative if possible)
def _resolve_dataset_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(current_dir), "Meals Recipes", "themealdb_calculated.jsonl"),
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), "Meals Recipes", "themealdb_calculated.jsonl"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # Fallback to original path if it happens to exist on the machine
    fallback = r"C:\Users\thath\Desktop\OwlHacks\Meals Recipes\themealdb_calculated.jsonl"
    if os.path.exists(fallback):
        return fallback
    raise FileNotFoundError(
        "themealdb_calculated.jsonl not found. Place it under 'Meals Recipes/themealdb_calculated.jsonl' in the repo."
    )


df = pd.read_json(_resolve_dataset_path(), lines=True)

# Extract nutrition features from the nested structure
nutrition_df = pd.json_normalize(df['nutrition'].tolist())
df = pd.concat([df, nutrition_df], axis=1)

# Select features
features = ['Calories', 'Protein', 'Fat', 'Carbohydrates']
data_to_cluster = df[features]

# Prepare scaling and (optional) clustering
if _SKLEARN_AVAILABLE:
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data_to_cluster)
    # num of clusters
    k = 20
    kmeans_model = KMeans(n_clusters=k, random_state=42, n_init=10)
    # train model
    kmeans_model.fit(data_scaled)
    df['cluster'] = kmeans_model.labels_
else:
    # Manual standardization (mean/std) for distance computations
    _means = data_to_cluster.mean()
    _stds = data_to_cluster.std().replace(0, 1)
    def _manual_scale(X: pd.DataFrame) -> np.ndarray:
        return ((X - _means) / _stds).to_numpy()
    # No clustering labels in fallback mode
    df['cluster'] = -1

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

    per_meal_target = get_per_meal_target(num_meal_preference, user_daily_macros)

    if _SKLEARN_AVAILABLE:
        # Use trained scaler/cluster centers
        scaled_per_meal_target = scaler.transform(per_meal_target)
        cluster_centers = kmeans_model.cluster_centers_
        distances = euclidean_distances(scaled_per_meal_target, cluster_centers)

        best_cluster_indices = np.argsort(distances[0])
        recommendation_dfs = []  # List to store DataFrames

        num_sample_clusters = 4  # Reduced number of clusters
        meals_per_cluster = max(1, int(np.ceil(num_recommendations / num_sample_clusters)))
        for cluster_idx in best_cluster_indices[:num_sample_clusters]:
            cluster_meals = df[df['cluster'] == cluster_idx].copy()
            if len(cluster_meals) == 0:
                continue
            cluster_meal_features = scaler.transform(cluster_meals[features])
            meal_distances = euclidean_distances(scaled_per_meal_target, cluster_meal_features)
            cluster_meals.loc[:, 'distance'] = meal_distances[0]
            # penalty for desserts
            dessert_penalty = 1.3
            cluster_meals.loc[cluster_meals['strCategory'] == 'Dessert', 'distance'] *= dessert_penalty
            top_meals = cluster_meals.nsmallest(meals_per_cluster, 'distance')
            recommendation_dfs.append(top_meals)

        if recommendation_dfs:
            final_recommendations = pd.concat(recommendation_dfs, ignore_index=True)
            return final_recommendations.drop(columns=['distance'])
        else:
            return pd.DataFrame()
    else:
        # Fallback: no sklearn. Compute standardized distance directly over entire dataset.
        # Manually standardize both dataset and target using dataset stats.
        X_scaled = _manual_scale(df[features])
        target_scaled = ((per_meal_target - _means[features].to_numpy()) / _stds[features].to_numpy()).reshape(1, -1)
        # Euclidean distances
        dists = np.linalg.norm(X_scaled - target_scaled, axis=1)
        recs = df.copy()
        recs.loc[:, 'distance'] = dists
        # penalty for desserts
        dessert_penalty = 1.3
        recs.loc[recs['strCategory'] == 'Dessert', 'distance'] *= dessert_penalty
        top_meals = recs.nsmallest(int(num_recommendations), 'distance')
        return top_meals.drop(columns=['distance'])

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

