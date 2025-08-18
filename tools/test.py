import cudf
import cupy as cp
from cuml.cluster import KMeans

# Create synthetic data
X = cp.random.rand(1000, 2)

# Convert to cuDF for cuML
gdf = cudf.DataFrame.from_records(X)

# Fit KMeans
kmeans = KMeans(n_clusters=3)
kmeans.fit(gdf)

# Predict cluster labels
labels = kmeans.predict(gdf)
print(labels)
