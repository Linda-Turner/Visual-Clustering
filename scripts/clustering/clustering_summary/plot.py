import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import pairwise_distances
from scipy.cluster.hierarchy import linkage, leaves_list
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def plot_cluster_distance_heatmap(
    X,
    labels,
    metric: str = "euclidean",
    standardize: bool = True,
    order: str = "hierarchical",     # {'identity', 'size', 'hierarchical'}
    method: str = "average",         # linkage method if order='hierarchical'
    cmap: str = "mako",              # try also 'viridis', 'rocket', 'coolwarm'
    annotate: bool = True,
    fmt: str = ".2f",
    figsize=(7, 6),
    title: str | None = None,
):
    """
    Plot a heatmap of pairwise distances between cluster centroids.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature matrix (original feature space).
    labels : array-like of shape (n_samples,)
        Cluster IDs (ints or strings).
    metric : str, default='euclidean'
        Distance metric for centroids. Examples: 'euclidean', 'cosine', 'cityblock'.
        See sklearn.metrics.pairwise_distances for options.
    standardize : bool, default=True
        If True, standardize features (z-score) before computing centroids.
        Recommended when features are on different scales.
    order : {'identity', 'size', 'hierarchical'}, default='hierarchical'
        How to order clusters in the heatmap.
        - 'identity': as they appear in sorted(unique(labels))
        - 'size': descending cluster size
        - 'hierarchical': order by hierarchical clustering of centroid distances
    method : str, default='average'
        Linkage method for hierarchical ordering ('single','complete','average','ward' [euclidean only], etc.).
    cmap : str, default='mako'
        Seaborn colormap.
    annotate : bool, default=True
        Annotate each cell with the distance value.
    fmt : str, default='.2f'
        Format string for annotations.
    figsize : tuple, default=(7,6)
        Figure size.
    title : str or None
        Figure title.

    Returns
    -------
    fig, ax, dist_df : (matplotlib.figure.Figure, matplotlib.axes.Axes, pandas.DataFrame)
        The figure/axis and the distance matrix as a DataFrame (ordered as plotted).
    """

    X = np.asarray(X)
    labels = np.asarray(labels)

    # Choose label order base set
    unique_labels, counts = np.unique(labels, return_counts=True)

    # Optional standardization (recommended if features are on different scales)
    X_proc = StandardScaler().fit_transform(X) if standardize else X

    # Compute centroids in processed space
    centroids = []
    label_order_identity = []
    for lab in sorted(unique_labels, key=lambda x: str(x)):
        idx = labels == lab
        centroids.append(X_proc[idx].mean(axis=0))
        label_order_identity.append(lab)
    centroids = np.vstack(centroids)
    label_order_identity = np.array(label_order_identity)

    # Pairwise distances between centroids
    D = pairwise_distances(centroids, metric=metric)

    # Determine display order
    if order == "identity":
        order_idx = np.arange(len(label_order_identity))
    elif order == "size":
        # order by cluster size (desc)
        size_map = {lab: cnt for lab, cnt in zip(unique_labels, counts)}
        order_idx = np.argsort([-size_map[lab] for lab in label_order_identity])
    elif order == "hierarchical":
        # Hierarchical clustering of centroids using the same distance metric.
        # Note: 'ward' linkage requires Euclidean distances; otherwise use average/complete, etc.
        # Convert square distance matrix to condensed form if needed
        # but scipy.linkage expects raw vectors; we pass centroids and set metric in linkage if euclidean/ward.
        if method == "ward" and metric != "euclidean":
            raise ValueError("Ward linkage requires metric='euclidean'.")
        # For general metrics, cluster on the distance matrix by converting to condensed vector
        if metric == "euclidean":
            Z = linkage(centroids, method=method, metric="euclidean")
            order_idx = leaves_list(Z)
        else:
            # Build condensed distance vector from square D
            # SciPy's linkage with a precomputed distance matrix requires condensed form.
            triu_idx = np.triu_indices_from(D, k=1)
            dvec = D[triu_idx]
            Z = linkage(dvec, method=method)
            order_idx = leaves_list(Z)
    else:
        raise ValueError("order must be one of {'identity', 'size', 'hierarchical'}")

    # Reorder matrix and labels
    ordered_labels = label_order_identity[order_idx]
    D_ordered = D[np.ix_(order_idx, order_idx)]

    # Build DataFrame for pretty labeling
    dist_df = pd.DataFrame(D_ordered, index=ordered_labels, columns=ordered_labels)

    # Plot heatmap
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        dist_df,
        cmap=cmap,
        annot=annotate,
        fmt=fmt,
        square=True,
        cbar_kws={"label": f"{metric.capitalize()} distance"},
        linewidths=0.5,
        linecolor="white"
    )

    ax.set_title(title or f"Inter-cluster {metric} distances")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Cluster")
    fig.tight_layout()

    return fig, ax, dist_df


def plot_clusters_2d(
    X,
    labels,
    method: str = "pca",
    random_state: int = 42,
    figsize=(8, 6),
    palette=None,
    alpha=0.65,
    annotate=True,
    title=None
):
    """
    Visualize high-dimensional clusters in 2D with colors and centroid annotations.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature matrix.
    labels : array-like of shape (n_samples,)
        Cluster assignments (ints or strings).
    method : {'pca', 'tsne'}, default='pca'
        2D reduction method to use for visualization only.
    random_state : int, default=42
        Random state for reproducibility with t-SNE.
    figsize : tuple, default=(8, 6)
        Figure size in inches.
    palette : dict or list, optional
        Mapping from label -> color, or list of colors (cycled).
    alpha : float in [0, 1], default=0.65
        Point transparency.
    annotate : bool, default=True
        Whether to place cluster ID text at the centroid (in 2D space).
    title : str, optional
        Figure title.

    Returns
    -------
    fig, ax
    """

    # Convert to numpy arrays
    X = np.asarray(X)
    labels = np.asarray(labels)
    unique_labels = np.unique(labels)

    # 2D projection for visualization
    if method.lower() == "pca":
        reducer = PCA(n_components=2, random_state=random_state)
        X2 = reducer.fit_transform(X)
        subtitle = "PCA (2D)"
    elif method.lower() == "tsne":
        reducer = TSNE(n_components=2, random_state=random_state, init="pca", learning_rate="auto")
        X2 = reducer.fit_transform(X)
        subtitle = "t-SNE (2D)"
    else:
        raise ValueError("method must be 'pca' or 'tsne'")

    # Build color map
    import itertools
    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]
    color_cycle = itertools.cycle(default_colors)

    if palette is None:
        colors = {lab: next(color_cycle) for lab in unique_labels}
    elif isinstance(palette, dict):
        colors = {lab: palette.get(lab, next(color_cycle)) for lab in unique_labels}
    else:
        # list-like palette; cycle if not enough
        color_cycle = itertools.cycle(palette)
        colors = {lab: next(color_cycle) for lab in unique_labels}

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    for lab in unique_labels:
        idx = labels == lab
        ax.scatter(
            X2[idx, 0],
            X2[idx, 1],
            s=18,
            c=colors[lab],
            alpha=alpha,
            #label=str(lab),
            edgecolor="none"
        )

    # Compute and annotate centroids (in 2D visualization space)
    if annotate:
        for lab in unique_labels:
            idx = labels == lab
            cx, cy = X2[idx, 0].mean(), X2[idx, 1].mean()
            #ax.scatter([cx], [cy], c=colors[lab], s=180, marker=None, edgecolor="black", linewidths=1.0, zorder=3)
            ax.text(cx, cy, f"  {lab}", fontsize=11, weight="bold", va="center", ha="left",
                    color="black")
                    #, bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=1.5))

    # Styling
    ttl = title or "Clustering Visualization"
    ax.set_title(f"{ttl} — {subtitle}")
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    ax.legend(title="Cluster", frameon=True, fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.25)
    fig.tight_layout()
    return fig, ax


print("plotting the clusters")
fig, ax = plot_clusters_2d(embeddings, labels)
fig.savefig('cl-vis.png')
plt.close(fig)
#plt.show()

#print("heat map")
#fig, ax, dist_df = plot_cluster_distance_heatmap(
#    embeddings, labels,
#    metric="euclidean",     # try "cosine" if direction matters more than magnitude
#    standardize=False,       # set False if your features are already on the same scale
#    order="hierarchical",   # 'identity', 'size', or 'hierarchical'
#    method="average",       # 'ward' (euclidean only), 'complete', 'single', 'average'
#    cmap="mako",
#    annotate=True,
#    fmt=".2f",
#    title="Centroid Distance Heatmap"
#)
#
## The DataFrame 'dist_df' contains the numeric distance matrix in the plotted order
#print(dist_df)
#
