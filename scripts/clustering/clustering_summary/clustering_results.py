import csv, os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_samples
from collections import Counter

# import spacy


def store_clustering_results(
        input_file : str, 
        embedding_file : str, 
        clusters_file : str, 
        cluster_terms_file : str, 
        output_dir: str,
        num_keys : int = 7, 
        progress_callback = None,
        indeterminate_callback = None
    ):
    print(f"\n{'='*60}")
    print("Clustering analysis started ...")

    if indeterminate_callback:
        indeterminate_callback("Preparing to get clusturing results ...")

    texts_df = read_text(input_file) #ID, path, text
    texts_df['ID'] = texts_df['ID'].astype(str)
    clusters_df,  cluster_counts = read_clusters(clusters_file) # ID, clusterid
    clusters_df['ID'] = clusters_df['ID'].astype(str)
    embeddings_df = read_embeddings(embedding_file) # ID, emb_..
    embeddings_df['ID'] = embeddings_df['ID'].astype(str)
    cluster_seperation = cluster_silhouette_scores(embeddings_df, clusters_df)

    cluster_img_desc = clusters_df.merge(texts_df, on='ID', how='inner') # ID, clusterid, path, text
    output_cluster_img_desc = os.path.join(output_dir, 'clusters_img_desc.csv')
    cluster_img_desc.to_csv(output_cluster_img_desc, index=False)

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
    text_summary = dict()
    for i, cluster_id in enumerate(cluster_ids):
        if progress_callback:
            progress_callback(i, num_topics, "Getting cluster terms ...")
        doc = [(features[w], res[i, w]) for w in res[i, :].indices]
        doc.sort(key=lambda x: x[1], reverse=True)
        top_doc = doc[:num_keys]
        ngrams = [str(term).split() for term, _ in top_doc if len(str(term).split()) > 1]
        cluster_terms = []
        i = 0
        while len(cluster_terms) < num_keys and i < len(doc):
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
        text_summary[cluster_id] = ','.join(cluster_terms)

    print('Number of clusters: ' + str(len(topics)))
    print('Number of outliers: ' + str(cluster_counts.get(-1, 0)))

    output_cluster_terms = os.path.join(output_dir, cluster_terms_file)
    write_cluster_terms(output_cluster_terms, text_summary, cluster_counts, cluster_seperation, num_keys)


def read_text(text_file):
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


def read_embeddings(embedding_file):
    df = pd.read_csv(embedding_file, header=None)
    df.columns = ['ID'] + [f'emb_{i}' for i in range(df.shape[1] - 1)]
    return df


def read_clusters(clusters_file):
    df = pd.read_csv(clusters_file)
    df.columns = ['ID', 'clusterId']
    cluster_counts = df['clusterId'].value_counts().to_dict()
    return df, cluster_counts


def read_selected_keys(sel_keys_file):
    sel_keys = set()
    with open(sel_keys_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            key = row[0]
            sel_keys.add(key)
    return sel_keys


def write_cluster_terms(
        cluster_terms: str,
        text_summary: dict,
        cluster_counts: dict,
        silhouette: dict,
        num_keys: int
    ):
    with open(cluster_terms, 'w', encoding='utf-8', newline='') as out:
        out.write('CID,Sil,Size')
        for k in range(num_keys):
            out.write(',Term ' + str(k))
        out.write('\n')
        for cluster_id, terms in text_summary.items():
            cl_size = cluster_counts[cluster_id]
            out.write(str(cluster_id) + ',' + str(round(silhouette[cluster_id], 2)) + ',' + str(cl_size) + ',' + terms + '\n')


def cluster_silhouette_scores(
        embeddings_df,
        clusters_df
    ):
    df = embeddings_df.merge(clusters_df,on='ID',how='inner')
    df = df[df['clusterId']!=-1]
    X = df.filter(like='emb_').values
    labels = df['clusterId'].values
    # Compute per-sample and overall silhouette scores
    s_samples = silhouette_samples(X, labels)
    # Aggregate per cluster
    clusters = Counter(labels)
    num_samples = len(s_samples)
    res = dict()
    for sil in range(num_samples):
        c = labels[sil]
        if int(c) not in res:
            res[int(c)] = 0
        res[int(c)] = res[int(c)] + float(s_samples[sil].item()) / clusters[c]
    return res

# stemmer = EnglishStemmer()
# nltk.download('wordnet')
# nltk.download('stopwords')
# lemmatizer = WordNetLemmatizer()
# analyzer = CountVectorizer().build_analyzer()

# def stemmed_words(doc):
#     return (stemmer.stem(w) for w in analyzer(doc))

# sw = stopwords.words('english')

# def lemmatized_words(doc):
#     terms = []
#     for w in analyzer(doc):
#         if w not in sw:
#             terms.append(lemmatizer.lemmatize(w))
#     return terms


# store_clustering_results(input_file='results/round_1/updated_input_file.csv', output_dir='results',
#                     embedding_file='results/round_1/embedding.csv', clusters_file='results/round_1/clusters.csv',
#                     sel_keys_file='sel_keys.csv', cluster_terms_file='cluster_terms.csv', key_terms_file='key_terms.csv',
#                     num_keys=5)
                