import os
import time

from scripts.clustering.clustering_logic.embed import embed
from scripts.clustering.clustering_logic.reduce import reduce_dim
from scripts.clustering.clustering_logic.cluster import cluster_embeddings
from scripts.clustering.clustering_summary.clustering_descriptions import get_cluster_descriptions


def orchestrate_clustering(input_file, round_output_dir,previous_output_dir, num_keys, arguments, round,progress_callback=None, indeterminate_callback=None, step_callback=None):
    cluster_method = arguments["cluster_method"]
    cluster_metric =  arguments["cluster_metric"]
    min_cluster_size = int(arguments["min_cluster_size"])
    num_clusters = int(arguments["num_clusters"])
    embedding_model = arguments["embedding_model"]
    embedding_batch = int(arguments["embedding_batch"])
    topk = int(arguments["topk"])
    credentials = arguments["credentials"]
    reduction_batch = int(arguments["reduction_batch"])
    scaling = arguments["scaling"]
    reduction_model = arguments["reduction_model"]
    components = int(arguments["components"])
    neighbors = int(arguments["neighbors"])
    if round > 2:
        # Embed
        step_callback("Step 1/4: Embedding")
        embed(input_file=input_file, output_file='embeddings.csv', 
            output_dir=round_output_dir, previous_output_dir=previous_output_dir,
            model=embedding_model, batch=embedding_batch,
            topk=topk, progress_callback=progress_callback, credentials=credentials, indeterminate_callback=indeterminate_callback)
        embedding_filepath = os.path.join(round_output_dir, 'embeddings.csv')

        # Reduce
        step_callback("Step 2/4: Dimension Reduction")
        reduce_dim(input_file=embedding_filepath, output_file='reductions.csv', output_dir=round_output_dir,
                batch=reduction_batch, scaling=scaling,
                model=reduction_model, components=components,
                neighbors=neighbors, 
                progress_callback=progress_callback, indeterminate_callback=indeterminate_callback)
        reduction_filepath = os.path.join(round_output_dir, 'reductions.csv')

        # Cluster
        step_callback("Step 3/4: Clustering")
        cluster_embeddings(input_file=reduction_filepath, output_file='clusters.csv', output_dir=round_output_dir,
            method=cluster_method, metric=cluster_metric, 
            min_cluster_size=min_cluster_size, num_clusters=num_clusters,
            indeterminate_callback=indeterminate_callback)
        cluster_filepath = os.path.join(round_output_dir, 'clusters.csv')
    
        # Analyze
        step_callback("Step 4/4: Cluster Analysis")
        cluster_terms_filepath = get_cluster_descriptions(input_file=input_file, output_dir=round_output_dir,
                            embedding_file=reduction_filepath, clusters_file=cluster_filepath,
                            cluster_descriptions_file='cluster_descriptions.csv', cluster_division_file="cluster_division.csv",
                            cluster_2d_plot_file='cluster_visualization.png', cluster_centroid_hm_file='cluster_heatmap.png',
                            num_terms=num_keys, 
                            progress_callback=progress_callback, indeterminate_callback=indeterminate_callback)
    cluster_terms_filepath = os.path.join(round_output_dir, 'cluster_descriptions.csv')

    return cluster_terms_filepath
