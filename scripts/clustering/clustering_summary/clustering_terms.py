import csv, os, re, json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_samples
from collections import Counter


def store_clustering_terms(
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
        indeterminate_callback("Preparing clusturing results ...")
    texts, paths = read_text(input_file)
    embeddings = read_embeddings(embedding_file)
    cluster_ids,  cluster_counts = read_clusters(clusters_file)
    sel_keys = read_selected_keys(sel_keys_file)
    cluster_seperation = cluster_silhouette_scores(embeddings, cluster_ids)

    topics = []
    num_topics = len(cluster_counts)
    if '-1' in cluster_counts:
        num_topics -= 1
    for _ in range(num_topics):
        topics.append('')

    # images = dict()
    for row in range(len(cluster_ids)):
        cluster_id = int(cluster_ids[row])
        if cluster_id == -1: continue
        topics[cluster_id] += ' '
        topics[cluster_id] += texts[row]
        # if cluster_id not in images:
        #     images[cluster_id] = []
        # images[cluster_id].append(paths[row])

    key_terms = Counter()
    vectorizer = TfidfVectorizer(stop_words="english")
    res = vectorizer.fit_transform(topics)
    features = vectorizer.get_feature_names_out()
    text_summary = dict()
    for i in range(num_topics):
        if progress_callback:
            progress_callback(i, num_topics, "Getting cluster terms ...")
        doc = [(features[w], res[i,w]) for w in res[i,:].indices]
        doc.sort(key=lambda x: x[1])
        idx = len(doc)-1
        cluster_terms = []
        while len(cluster_terms) < num_keys:
            t = doc[idx][0]
            idx -= 1
            term = str(t)
            key_terms[term] += 1
            if term in sel_keys:
                term = '*' + term + '*'
            cluster_terms.append(term)
        text_summary[i] = ','.join(cluster_terms)

    print('Key terms (' + str(len(key_terms)) + ')')
    print('Number of clusters: ' + str(len(topics)))
    print('Number of outliers: ' + str(cluster_counts['-1']))

    output_cluster_terms = os.path.join(output_dir, cluster_terms_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_cluster_terms)
    write_cluster_terms(output_cluster_terms, text_summary, cluster_counts, cluster_seperation, num_keys)
    output_cluster_keys = os.path.join(output_dir, key_terms_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_cluster_keys)
    write_key_terms(output_cluster_keys, key_terms, sel_keys)


def update_clustering_terms(input_file, next_output_dir, round_output_dir, progress_callback):
    """
    Update the terms for a specific cluster.
    """
    clusters = os.path.join(round_output_dir, "clusters.csv")  # ID, ClusterID
    cluster_updates = os.path.join(round_output_dir, "cluster_updates.csv")  # cluster_id, term, delete, merged_terms
    updated_input_file = os.path.join(next_output_dir, "updated_input_file.csv")
    updated_ids_file = os.path.join(round_output_dir, "updated_ids.json")
    clusters_df = pd.read_csv(clusters)
    cluster_updates_df = pd.read_csv(cluster_updates).fillna("")

    updated_ids = []

    out = open(updated_input_file, 'w', encoding='utf-8')
    out.write('ID' + '\t' + 'Dir' + '\t' + 'ImageID' + '\t' + 'Labels' + '\n')
    with open(input_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for i, row in enumerate(reader):
        # for row in reader:
            if progress_callback:
                progress_callback(i, len(clusters_df), "Updating image descriptions ...")
            id = row['ID']
            dir = row['Dir']
            img = row['ImageID']
            text = row['Labels']
            altered = False
            # replace text
            # find cluster on id in clusters_df
            cluster_id = clusters_df[clusters_df['ID'] == int(id)]['ClusterID'].iloc[0]
            # change text based on cluster_updates
            if cluster_id > -1:
                # at cluster_id -> delete term with True 
                text_updates = cluster_updates_df[cluster_updates_df['cluster_id'] == int(cluster_id)]
                deletions = text_updates[text_updates['delete'] == True]['term'].tolist()
                for term in deletions:
                    new_text = re.sub(re.escape(term), '', text, flags=re.IGNORECASE)
                    if new_text != text:
                        text=new_text
                        altered = True
                # at cluster_id -> replace merged_terms with term
                merges = text_updates[text_updates['delete'] == False][['term', 'merged_terms']].to_dict('records')
                for merge in merges:
                    merged_terms = merge['merged_terms'].split("|")
                    if len(merged_terms) > 1:
                        for merged_term in merged_terms:
                            new_text = re.sub(re.escape(merged_term), merge["term"], text, flags=re.IGNORECASE)
                            if new_text != text:
                                text=new_text
                                altered=True
            if altered:
                updated_ids += [id]
            out.write(id + '\t' + dir + '\t' + img + '\t' + text + '\n')
    out.close()
    with open(updated_ids_file, "w", encoding="utf-8") as f:
        json.dump(list(updated_ids), f)
    return updated_input_file, len(updated_ids)


def read_text(text_file):
    texts = []
    paths = []
    with open(text_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            text = row['Labels']
            if text.strip() == '': continue
            texts.append(text)
            paths.append(os.path.join(row['Dir'], row['ImageID']))
    return texts, paths


def read_embeddings(embedding_file):
    df = pd.read_csv(embedding_file, header=None)
    embeddings = df.iloc[:, 1:].values
    return embeddings


def read_clusters(clusters_file):
    cluster_ids = []
    with open(clusters_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            clus = row['ClusterID']
            cluster_ids.append(clus)
    cluster_counts = Counter(cluster_ids)
    return cluster_ids, cluster_counts


def read_selected_keys(sel_keys_file):
    sel_keys = set()
    with open(sel_keys_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            key = row[0]
            sel_keys.add(key)
    return sel_keys


def write_cluster_terms(
        cluster_terms : str, 
        text_summary: list,
        cluster_counts: list, 
        silhouette, 
        num_keys: int
    ):
    with open(cluster_terms, 'w', encoding='utf-8', newline='') as out:
        out.write('CID,Sil,Size')
        for k in range(num_keys):
            out.write(',Term ' + str(k))
        out.write('\n')
        for i in text_summary:
            cl_size = str(cluster_counts[str(i)])
            out.write(str(i) + ',' + str(round(silhouette[i], 2)) + ',' + cl_size + ',' + text_summary[i] + '\n')


def write_key_terms(        
        cluster_keys : str, 
        key_terms: list, 
        sel_keys: list
    ):
    out = open(cluster_keys, 'w')
    for t in sorted(key_terms):
        if t in sel_keys: continue
        out.write(t + ',' + t + ',' + str(key_terms[t]) + '\n')
    out.close()


def cluster_silhouette_scores(
        X,
        labels
    ):
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

