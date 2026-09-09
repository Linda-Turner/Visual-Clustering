import csv, os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_samples
from collections import Counter


def store_clustering_results(
        input_file : str, 
        embedding_file : str, 
        clusters_file : str, 
        sel_keys_file : str, 
        cluster_terms_file : str, 
        key_terms_file : str, 
        output_dir: str,
        num_keys : int = 5, 
        progress_callback = None,
        indeterminate_callback = None
    ):
    print(f"\n{'='*60}")
    print("Clustering analysis started ...")

    if indeterminate_callback:
        indeterminate_callback("Preparing to get clusturing results ...")

    texts_df = read_text(input_file) #id, path, text
    embeddings_df = read_embeddings(embedding_file) # id, emb_....
    clusters_df,  cluster_counts = read_clusters(clusters_file) # id, cluster
    # sel_keys = read_selected_keys(sel_keys_file)
    cluster_seperation = cluster_silhouette_scores(embeddings_df, clusters_df)
    topics = {clusterid: '' for clusterid in cluster_counts if clusterid != -1}
    images = {clusterid: '' for clusterid in cluster_counts if clusterid != -1}
    num_topics = len(topics)

    # for cluster_id in clusters_df['cluster']:
    for row in clusters_df.itertuples():
        image_id, cluster_id = row.id, row.clusterId
        if cluster_id == -1: continue
        image_id_row = texts_df[texts_df['id'] == str(image_id)]
        text = image_id_row.iloc[0]['text']
        path = image_id_row.iloc[0]['path']
        topics[cluster_id] += ' ' + text
        images[cluster_id] += '|' + path

    cluster_ids = list(topics.keys())
    cluster_texts = list(topics.values())
    key_terms = Counter()
    vectorizer = TfidfVectorizer(stop_words="english")
    res = vectorizer.fit_transform(cluster_texts)
    features = vectorizer.get_feature_names_out()
    text_summary = dict()
    for i, cluster_id in enumerate(cluster_ids):
        if progress_callback:
            progress_callback(i, num_topics, "Getting cluster terms ...")
        doc = [(features[w], res[i, w]) for w in res[i, :].indices]
        doc.sort(key=lambda x: x[1], reverse=True)
        cluster_terms = []
        for term, _ in doc[:num_keys]:
            term = str(term)
            key_terms[term] += 1
            cluster_terms.append(term)
        text_summary[cluster_id] = ','.join(cluster_terms)

    print('Key terms (' + str(len(key_terms)) + ')')
    print('Number of clusters: ' + str(len(topics)))
    print('Number of outliers: ' + str(cluster_counts.get(-1, 0)))

    output_cluster_terms = os.path.join(output_dir, cluster_terms_file)
    write_cluster_terms(output_cluster_terms, text_summary, images, cluster_counts, cluster_seperation, num_keys)
    # output_cluster_keys = os.path.join(output_dir, key_terms_file)
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_cluster_keys)
    # write_key_terms(output_cluster_keys, key_terms, sel_keys)


def read_text(text_file):
    rows = []
    with open(text_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            text = row['Labels']
            if text.strip() == '':continue
            rows.append({
                'id': row['ID'],
                'path': os.path.join(row['Dir'].strip(),row['ImageID'].strip()),
                # 'path': row['Dir'].strip() + '/' + row['ImageID'],
                'text': text
            })
    return pd.DataFrame(rows)


def read_embeddings(embedding_file):
    df = pd.read_csv(embedding_file, header=None)
    df.columns = ['id'] + [f'emb_{i}' for i in range(df.shape[1] - 1)]
    return df


def read_clusters(clusters_file):
    df = pd.read_csv(clusters_file)
    df.columns = ['id', 'clusterId']
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
        images: dict,
        cluster_counts: dict,
        silhouette: dict,
        num_keys: int
    ):
    with open(cluster_terms, 'w', encoding='utf-8', newline='') as out:
        out.write('CID,Sil,Size')
        for k in range(num_keys):
            out.write(',Term ' + str(k))
        out.write(',Images')
        out.write('\n')
        for cluster_id, terms in text_summary.items():
            image_paths = images[cluster_id]
            cl_size = cluster_counts[cluster_id]
            out.write(str(cluster_id) + ',' + str(round(silhouette[cluster_id], 2)) + ',' + str(cl_size) + ',' + terms + ',' + image_paths + '\n')


def cluster_silhouette_scores(
        embeddings_df,
        clusters_df
    ):
    df = embeddings_df.merge(clusters_df,on='id',how='inner')
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


# store_clustering_results(input_file='data/input.csv', output_dir='results',
#                     embedding_file='results/round_0/embedding.csv', clusters_file='results/round_0/clusters.csv',
#                     sel_keys_file='sel_keys.csv', cluster_terms_file='cluster_terms.csv', key_terms_file='key_terms.csv',
#                     num_keys=5)
                