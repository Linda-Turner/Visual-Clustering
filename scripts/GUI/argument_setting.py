import tkinter as tk
from tkinter import ttk


def create_argument_settings(parent):
    columns_frame = tk.Frame(parent)
    columns_frame.pack(fill="both", expand=True, padx=20)

    # Embedding
    embedding_frame = tk.LabelFrame(columns_frame,text="Embedding",padx=15,pady=15)
    embedding_frame.pack(side="left",fill="both",expand=True,padx=10)

    tk.Label(embedding_frame, text="Embedding model").pack(anchor="w")
    embedding_model = ttk.Combobox(
        embedding_frame,
        state="readonly",
        values=["openai", "bert", "tfidf"]
    )
    embedding_model.set("bert")
    embedding_model.pack(fill="x", pady=(2, 10))

    credentials_label = tk.Label(embedding_frame,text="OpenAI credentials file")
    credentials_label.pack(anchor="w")
    credentials = ttk.Entry(embedding_frame)
    credentials.insert(0, "openai_api.txt")
    credentials.pack(fill="x", pady=(2, 10))

    topk_label = tk.Label(embedding_frame, text="Number of top terms")
    topk_label.pack(anchor="w")
    topk = ttk.Entry(embedding_frame)
    topk.insert(0, "10")
    topk.pack(fill="x", pady=(2, 10))

    tk.Label(embedding_frame, text="Batch size").pack(anchor="w")
    embedding_batch = ttk.Entry(embedding_frame)
    embedding_batch.insert(0, "500")
    embedding_batch.pack(fill="x", pady=(2, 10))

    def update_embedding_options(event=None):
        if embedding_model.get() == "openai":
            credentials.config(state="normal")
            credentials_label.config(text="OpenAI credentials file")
        else:
            credentials.config(state="disabled")
            # credentials_label.config(text="No credentials file needed")
            credentials_label.config(text="Not needed with bert or tfidf")
        if embedding_model.get() == 'tfidf':
            topk.config(state='normal')
            topk_label.config(text="Number of top terms")
        else:
            topk.config(state='disabled')
            # topk_label.config(text="No number of top terms needed")
            topk_label.config(text="not needed with bert or openai")
    embedding_model.bind("<<ComboboxSelected>>", update_embedding_options)
    update_embedding_options()

    # Reduction
    reduction_frame = tk.LabelFrame(columns_frame,text="Dimension Reduction",padx=15,pady=15)
    reduction_frame.pack(side="left",fill="both",expand=True,padx=10)

    tk.Label(reduction_frame, text="Reduction model").pack(anchor="w")
    reduction_model = ttk.Combobox(
        reduction_frame,
        state="readonly",
        values=["umap", "pca"]
    )
    reduction_model.set("umap")
    reduction_model.pack(fill="x", pady=(2, 10))

    tk.Label(reduction_frame, text="Scaling method").pack(anchor="w")
    scaling = ttk.Combobox(
        reduction_frame,
        state="readonly",
        values=["normalize", "minmax", "standard", "none"]
    )
    scaling.set("normalize")
    scaling.pack(fill="x", pady=(2, 10))

    tk.Label(reduction_frame, text="Number of dimension").pack(anchor="w")
    components = ttk.Entry(reduction_frame)
    components.insert(0, "10")
    components.pack(fill="x", pady=(2, 10))

    neighbors_label = tk.Label(reduction_frame,text="Number of neighbours")
    neighbors_label.pack(anchor="w")
    neighbors = ttk.Entry(reduction_frame)
    neighbors.insert(0, "5")
    neighbors.pack(fill="x", pady=(2, 10))

    tk.Label(reduction_frame, text="Batch size").pack(anchor="w")
    reduction_batch = ttk.Entry(reduction_frame)
    reduction_batch.insert(0, "100000")
    reduction_batch.pack(fill="x", pady=(2, 10))

    def update_reduction_options(event=None):
        if reduction_model.get() == "pca":
            neighbors.config(state="disabled")
            # neighbors_label.config(text="No number of neighbors needed")
            neighbors_label.config(text="Not needed with pca")
        else:
            neighbors.config(state="normal")
            neighbors_label.config(text="Number of neighbours")
    reduction_model.bind("<<ComboboxSelected>>",update_reduction_options)
    update_reduction_options()

    # Cluster
    cluster_frame = tk.LabelFrame(columns_frame,text="Clustering",padx=15,pady=15)
    cluster_frame.pack(side="left",fill="both",expand=True,padx=10)

    tk.Label(cluster_frame, text="Clustering method").pack(anchor="w")
    cluster_method = ttk.Combobox(
        cluster_frame,
        state="readonly",
        values=["hdbscan", "kmeans"]
    )
    cluster_method.set("hdbscan")
    cluster_method.pack(fill="x", pady=(2, 10))

    cluster_metric_label = tk.Label(cluster_frame, text="Clustering metric")
    cluster_metric_label.pack(anchor="w")
    cluster_metric = ttk.Combobox(
        cluster_frame,
        state="readonly",
        values=["euclidean", "cosine", "manhattan"]
    )
    cluster_metric.set("euclidean")
    cluster_metric.pack(fill="x", pady=(2, 10))

    clust_size_label = tk.Label(cluster_frame, text="Minimum cluster size")
    clust_size_label.pack(anchor="w")
    min_cluster_size = ttk.Entry(cluster_frame)
    min_cluster_size.insert(0, "50")
    min_cluster_size.pack(fill="x", pady=(2, 10))

    num_clust_label = tk.Label(cluster_frame, text="Minimum number of clusters")
    num_clust_label.pack(anchor="w")
    num_clusters = ttk.Entry(cluster_frame)
    num_clusters.insert(0, "100")
    num_clusters.pack(fill="x", pady=(2, 10))

    def update_clustering_options(event=None):
        if cluster_method.get() == "kmeans":
            min_cluster_size.config(state="disabled")
            cluster_metric.config(state='disabled')
            num_clusters.config(state="normal")
            num_clust_label.config(text="Minimum number of clusters")
            # clust_size_label.config(text="No minimum cluster size needed")
            # cluster_metric_label.config(text="No cluster metric needed")
            clust_size_label.config(text="Not needed with kmeans")
            cluster_metric_label.config(text="Not needed with kmeans")
        elif cluster_method.get() == "hdbscan":
            min_cluster_size.config(state="normal")
            cluster_metric.config(state='normal')
            num_clusters.config(state="disabled")
            # num_clust_label.config(text="No minimum number of clusters needed")
            num_clust_label.config(text="Not needed with hdbscan")
            clust_size_label.config(text="Minimum cluster size")
            cluster_metric_label.config(text="Cluster metric")
    cluster_method.bind("<<ComboboxSelected>>",update_clustering_options)
    update_clustering_options()

    argument_widgets = {
        "cluster_method": cluster_method,
        "cluster_metric": cluster_metric,
        "min_cluster_size": min_cluster_size,
        "num_clusters": num_clusters,
        "embedding_model": embedding_model,
        "embedding_batch": embedding_batch,
        "topk": topk,
        "credentials": credentials,
        "reduction_batch": reduction_batch,
        "scaling": scaling,
        "reduction_model": reduction_model,
        "components": components,
        "neighbors": neighbors,
    }
    return argument_widgets

