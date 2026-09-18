import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import seaborn as sns

from sklearn.metrics import pairwise_distances
from scipy.cluster.hierarchy import linkage, leaves_list


def plot_cluster_distance_heatmap(
        X,
        labels,
        cluster_centroid_hm_path,
        metric="euclidean"
    ):
    """
    Plot distances between cluster centroids.
    """

    X = np.asarray(X)
    labels = np.asarray(labels)

    # Get centroids and keep their cluster IDs in the same order
    cluster_ids = np.sort(np.unique(labels))
    cluster_centroids = np.vstack([X[labels == cluster_id].mean(axis=0) for cluster_id in cluster_ids])

    # Calculate centroid distances
    distances = pairwise_distances(cluster_centroids, metric=metric)

    # Hierarchical ordering makes the heatmap easier to read
    if len(cluster_ids) > 2:
        linkage_matrix = linkage(distances[np.triu_indices_from(distances, k=1)], method="average")
        order = leaves_list(linkage_matrix)
        cluster_ids = cluster_ids[order]
        distances = distances[np.ix_(order, order)]

    distance_df = pd.DataFrame(distances, index=cluster_ids, columns=cluster_ids)

    fig, ax = plt.subplots(figsize=(max(7, len(cluster_ids) * 0.35), max(6, len(cluster_ids) * 0.35)))
    sns.heatmap(distance_df, ax=ax, cmap="viridis", square=True, annot=True, annot_kws={"fontsize": 7}, fmt=".2f", linewidths=0.3, cbar_kws={"label": f"{metric.capitalize()} distance"})
    ax.set_title("Distance Between Cluster Centroids")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Cluster")

    fig.tight_layout()
    fig.savefig(cluster_centroid_hm_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_clusters_2d(
        X,
        labels,
        cluster_visualization_path,
        method="pca"
    ):
    """
    Visualize clusters in 2D.
    """
    X = np.asarray(X)
    labels = np.asarray(labels)
    cluster_ids = np.sort(np.unique(labels))

    # Reduce to two dimensions
    if method.lower() == "pca":
        reducer = PCA(n_components=2)
        X_2d = reducer.fit_transform(X)
        explained = reducer.explained_variance_ratio_ * 100
        x_label = f"PC1 ({explained[0]:.1f}%)"
        y_label = f"PC2 ({explained[1]:.1f}%)"
        title = "Cluster Visualization — PCA"

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = plt.get_cmap("tab20")
    for i, cluster_id in enumerate(cluster_ids):
        mask = labels == cluster_id
        ax.scatter(X_2d[mask, 0], X_2d[mask, 1], s=20, alpha=0.6, color=cmap(i % 20), edgecolors="none")
        # Cluster centroid in the 2D visualization
        center_x = X_2d[mask, 0].mean()
        center_y = X_2d[mask, 1].mean()
        ax.text(center_x, center_y, str(cluster_id), fontsize=10, fontweight="bold", ha="center", va="center")
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle="--", alpha=0.2)
    fig.tight_layout()
    fig.savefig(cluster_visualization_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
