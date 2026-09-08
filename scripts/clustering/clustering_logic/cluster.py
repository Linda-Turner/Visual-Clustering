import os
import pandas as pd

import hdbscan
from sklearn.cluster import KMeans
from collections import Counter

def cluster_embeddings(
        input_file: str, 
        output_file: str, 
        output_dir: str, 
        method: str = "hdbscan", 
        metric: str = 'euclidean', 
        min_cluster_size: int = 50, 
        num_clusters: int = 100,
        indeterminate_callback = None
    ):
    """
    Cluster embedded image descriptions using HDBSCAN or KMeans.

    Args:
        input_file (str): Path to the input TSV file containing the image IDs and their corresponding embeddings. The first column must contain the IDs;
            all remaining columns are treated as embedding features.
        output_file (str): Name of the CSV file in which the cluster assignments will be saved.
        output_dir (str): Directory in which the output file will be saved.
        method (str, optional): Clustering algorithm to use. Defaults to "hdbscan". Supported methods are:
            - "hdbscan": Density-based clustering using HDBSCAN.
            - "kmeans": KMeans clustering with a predefined number of clusters.
        metric (str, optional): Distance metric used by HDBSCAN to measure the distance between embedding vectors. Defaults to "euclidean". 
        min_cluster_size (int, optional): Minimum number of samples required to form a cluster when using HDBSCAN. Defaults to 50. 
        num_clusters (int, optional): Number of clusters to create when using KMeans. Defaults to 100.
    """
    print(f"\n{'='*60}")
    print("Clustering started ...")

    if indeterminate_callback:
        indeterminate_callback("Clustering description embeddings ...")
    output_file = os.path.join(output_dir, output_file)
    if method == 'hdbscan':
        cluster_model = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric=metric, prediction_data=True)
    elif method == 'kmeans':
        cluster_model = KMeans(init = "k-means++", n_clusters = num_clusters, n_init = 10, max_iter=500)

    print(f"Using {cluster_model} clustering model:", cluster_model)
    df = pd.read_csv(input_file, header=0)

    ids = df.loc[:, df.columns[0:1]]
    features = df.loc[:, df.columns[1:]]

    cluster_model.fit(features)

    clus_stats = Counter(cluster_model.labels_)
    print('Number of embedded texts clustered: ' + str(len(cluster_model.labels_)))
    print('Number of clusters created: ' + str(len(clus_stats)))
    print('Number of outliers: ' + str(clus_stats[-1]))
    
    data = pd.concat([ids, pd.DataFrame({"ClusterID":cluster_model.labels_})], axis="columns")
    data.to_csv(output_file, header=True, index=False)
    return None
