import csv, os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from scripts.clustering.clustering_summary.clustering_metrics import cluster_silhouette_scores
from scripts.clustering.clustering_summary.clustering_visualization_plots import plot_clusters_2d, plot_cluster_distance_heatmap 

def get_cluster_descriptions(
        input_file : str, 
        embedding_file : str, 
        clusters_file : str, 
        cluster_descriptions_file : str, 
        cluster_division_file : str, 
        cluster_2d_plot_file : str, 
        cluster_centroid_hm_file: str, 
        output_dir: str,
        num_terms : int = 7, 
        progress_callback = None,
        indeterminate_callback = None
    ):
    print(f"\n{'='*60}")
    print("Clustering analysis started ...")

    if indeterminate_callback:
        indeterminate_callback("Preparing to get clusturing results ...")

    # Read csv files as pandas
    texts_df = read_input(input_file) #ID, path, text
    texts_df['ID'] = texts_df['ID'].astype(str)
    clusters_df,  cluster_counts = read_clusters(clusters_file) # ID, clusterid
    clusters_df['ID'] = clusters_df['ID'].astype(str)
    embeddings_df = read_reduced_embeddings(embedding_file) # ID, emb_..
    embeddings_df['ID'] = embeddings_df['ID'].astype(str)

    clusters_embeddings_df = embeddings_df.merge(clusters_df,on='ID',how='inner')
    clusters_embeddings_df = clusters_embeddings_df[clusters_embeddings_df['clusterId']!=-1]
    features = clusters_embeddings_df.filter(like='f').values
    cluster_labels = clusters_embeddings_df['clusterId'].values

    # Which image and description in which cluster
    cluster_img_desc = clusters_df.merge(texts_df, on='ID', how='inner') # ID, clusterid, path, text
    output_cluster_img_desc = os.path.join(output_dir, cluster_division_file)
    cluster_img_desc.to_csv(output_cluster_img_desc, index=False)

    # Which terms in which cluster
    top_cluster_terms = cluster_terms(cluster_counts, cluster_img_desc, progress_callback, num_terms)

    print('Number of clusters: ' + str(len(cluster_counts)-1))
    print('Number of outliers: ' + str(cluster_counts.get(-1, 0)))

    # Calculate metrics
    cluster_silhouette = cluster_silhouette_scores(features, cluster_labels)

    # Save cluster descriptions
    cluster_description_path = os.path.join(output_dir, cluster_descriptions_file)
    write_cluster_terms(cluster_description_path, cluster_counts, cluster_silhouette, top_cluster_terms, num_terms)

    cluster_2d_plot_path = os.path.join(output_dir, cluster_2d_plot_file)
    plot_clusters_2d(features, cluster_labels, cluster_2d_plot_path)
    cluster_centroid_hm_path = os.path.join(output_dir, cluster_centroid_hm_file)
    plot_cluster_distance_heatmap(features, cluster_labels, cluster_centroid_hm_path)


def cluster_terms(cluster_counts, cluster_img_desc, progress_callback, num_terms):
    topics = {clusterid: '' for clusterid in cluster_counts if clusterid != -1}
    for row in cluster_img_desc.itertuples():
        cluster_id, text = row.clusterId, row.text
        if cluster_id == -1: continue
        topics[cluster_id] += ' ' + text

    cluster_ids = list(topics.keys())
    cluster_texts = list(topics.values())
    num_topics = len(cluster_ids)

    vectorizer = TfidfVectorizer(stop_words="english",ngram_range=(1, 2))
    res = vectorizer.fit_transform(cluster_texts)
    features = vectorizer.get_feature_names_out()
    top_cluster_terms = dict()
    for i, cluster_id in enumerate(cluster_ids):
        if progress_callback:
            progress_callback(i, num_topics, "Getting cluster terms ...")
        doc = [(features[w], res[i, w]) for w in res[i, :].indices]
        doc.sort(key=lambda x: x[1], reverse=True)
        top_doc = doc[:num_terms]
        ngrams = [str(term).split() for term, _ in top_doc if len(str(term).split()) > 1]
        cluster_terms = []
        i = 0
        while len(cluster_terms) < num_terms and i < len(doc):
            term, _ = doc[i]
            term = str(term)
            if len(term.split()) == 1:
                if any(term in ngram for ngram in ngrams):
                    i += 1
                    continue
            if len(term.split()) > 1:
                ngrams.append(str(term).split())
                cluster_terms = [cluster_term for cluster_term in cluster_terms 
                                 if not (cluster_term in term.split())]
            cluster_terms.append(term)
            i += 1
        top_cluster_terms[cluster_id] = ','.join(cluster_terms)
    return top_cluster_terms


# Functions to read the csv files
def read_input(text_file):
    rows = []
    with open(text_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            text = row['Labels']
            if text.strip() == '':continue
            rows.append({
                'ID': row['ID'],
                'path': os.path.join(row['Dir'].strip(),row['ImageID'].strip()),
                'text': text
            })
    return pd.DataFrame(rows)

def read_reduced_embeddings(embedding_file):
    df = pd.read_csv(embedding_file)
    return df

def read_clusters(clusters_file):
    df = pd.read_csv(clusters_file)
    df.columns = ['ID', 'clusterId']
    cluster_counts = df['clusterId'].value_counts().to_dict()
    return df, cluster_counts


def write_cluster_terms(
        cluster_description_path: str,
        cluster_counts: dict,
        cluster_silhouettes: dict,
        top_cluster_terms: dict,
        num_terms: int
    ):
    with open(cluster_description_path, 'w', encoding='utf-8', newline='') as out:
        out.write('CID,Sil,Size')
        for k in range(num_terms):
            out.write(',Term ' + str(k))
        out.write('\n')
        for cluster_id, terms in top_cluster_terms.items():
            cl_size = cluster_counts[cluster_id]
            out.write(str(cluster_id) + ',' + str(round(cluster_silhouettes[cluster_id], 2)) + ',' + str(cl_size) + ',' + terms + '\n')


# get_cluster_descriptions(input_file='data/input.csv', output_dir='clustering_results_ngram/round_0',
#                     embedding_file='clustering_results_ngram/round_0/reduction.csv', clusters_file='clustering_results_ngram/round_0/clusters.csv',
#                     cluster_descriptions_file='cluster_descriptions.csv', cluster_division_file="cluster_division.csv",
#                     cluster_2d_plot_file='cluster_visualization.png', cluster_centroid_hm_file='cluster_heatmap.png',
#                     num_terms=7)
