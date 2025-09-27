import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Load data
df = pd.read_json("C:/Users/thath/Desktop/OwlHacks/K-Means Model/all_themealdb_meals.json")

# Select features
features = ['Calories', 'Protein_g', 'Fat_g', 'Carbs_g']
data_to_cluster = df[features]

#Scale data
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data_to_cluster)

# num of clusters
k = 20
kmeans_model = KMeans(n_clusters=k, random_state=42, n_init=10)

# train model
kmeans_model.fit(data_scaled)

# add cluster label to original dataframe
df['cluster'] = kmeans_model.labels_

