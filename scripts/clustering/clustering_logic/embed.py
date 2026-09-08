import os, csv, json
from tqdm import tqdm

from openai import OpenAI

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


def embed(
        input_file : str, 
        output_file : str, 
        output_dir : str,
        previous_output_dir : str,
        model : str = 'bert', 
        batch : int = 10,
        topk : int = 10, 
        progress_callback = None,
        credentials: str = None,
        indeterminate_callback=None
    ):
    """
    Generate embeddings for the texts in an input TSV file and save them to a CSV file.

    Already processed IDs are skipped when an existing output file is found, allowing the process to be resumed without recomputing previous embeddings.

    Three embedding methods are supported:

    Args:
        input_file (str): Path to the input TSV file. The file must contain at least the columns 'ID' and 'Labels'.
        output_file (str): Name of the output CSV file containing the embeddings.
        output_dir (str): Directory in which the output file will be saved.
        model (str, optional): Embedding method to use. Defaults to "bert". Available options include: "openai", "bert", or "tfidf".
            - "openai": OpenAI's text-embedding-3-small model.
            - "bert": SentenceTransformer's all-MiniLM-L6-v2 model.
            - "tfidf": TF-IDF representations using the top-k terms.
        batch (int, optional): Number of texts to process in one batch when using model "openai" or "bert". Defaults to 10.
        topk (int, optional): Number of highest-scoring TF-IDF terms to retain for each document when using the "tfidf" method. Defaults to 10.
        credentials (str, optional): Path to a file containing the OpenAI API key. Required when using the "openai" model. Defaults to None.
    """
    print(f"\n{'='*60}")
    print("Embedding started ...")
    if indeterminate_callback:
        indeterminate_callback("Preparing for Embedding ...")

    client = None
    model_emb = None
    if (model == 'openai'):
        file = open(credentials, "r")
        openai_api_key = file.readline().strip()
        client = OpenAI(api_key=openai_api_key)
        model_emb = "text-embedding-3-small"
    elif (model == 'bert'):
        model_emb = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    reused_ids = 0
    previous_output_exists = False
    embedding_file = os.path.join(output_dir, output_file)
    if previous_output_dir:
        previous_output_exists = True
        # Do not embed processed sentences again
        updated_ids_file = os.path.join(previous_output_dir, "updated_ids.json")
        with open(updated_ids_file, "r", encoding="utf-8") as f:
            updated_ID = set(str(x) for x in json.load(f))
        previous_embeddings = os.path.join(previous_output_dir, output_file)
        with open(previous_embeddings, newline="", encoding="utf-8") as csvfile, \
         open(embedding_file, "w", newline="", encoding="utf-8") as outres:
            reader, writer = csv.reader(csvfile), csv.writer(outres)
            for row in reader:
                if row[0] not in updated_ID:
                    writer.writerow(row)
                    reused_ids += 1
        outres = open(embedding_file, "a", newline="", encoding="utf-8")
    else:
        updated_ID = set()
        outres = open(embedding_file, "w", newline="", encoding="utf-8")
    
    with open(input_file, newline='', encoding="utf-8") as csvfile:
        total = sum(1 for _ in csvfile) - 1

    count = 0
    # Create batches to embed
    with open(input_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        ids, texts = [], []
        for row in tqdm(reader):
            # Build batch
            id = row['ID']
            count += 1
            if id not in updated_ID and previous_output_exists:
                continue
            text = row['Labels']
            texts.append(text)
            ids.append(id)
            
            if len(ids) >= batch and model != 'tfidf':
                embed_batch(model, model_emb, client,  topk, texts, ids, outres)
                ids, texts = [], []
                if progress_callback:
                    progress_callback(count, total, "Embedding image descriptions ...")
                
    if len(texts) > 0:
        embed_batch(model, model_emb, client,  topk, texts, ids, outres)
        if progress_callback:
            progress_callback(count, total, "Embedding image descriptions ...")
    
    outres.close()
    
    print("Embedding complete! ")
    print(str(len(updated_ID)) + " new texts embedded / " + str(reused_ids) + " old embedded texts")


def embed_batch(
        model="",
        model_emb=None,
        client=None,
        topk=None,
        texts=None,
        ids=None,
        outres=None
    ):
    """
    Generate embeddings for a batch of texts and write the results to an output CSV-file.
    """
    try:
        if (model == 'openai'):
            res = embed_openai(client, model_emb, texts)
        elif (model == 'bert'):
            res = embed_bert(model_emb, texts)
        elif (model == 'tfidf'):
            res = embed_tfidf(texts, topk)
        for i in range(len(ids)):
            id = ids[i]
            emb = ','.join(str(x) for x in res[i])
            outres.write(str(id) + ',' + emb + '\n')
        outres.flush()
    except Exception as e:
        print('cannot process batch: ' + str(e), flush=True)


def embed_openai(client, model, texts):
    """
    Generate text embeddings using an OpenAI embedding model.

    Args:
        client (OpenAI): Initialized OpenAI client used to send the embedding request.
        model (str): Name of the OpenAI embedding model to use. Here "text-embedding-3-small"
        texts (list[str]): List of texts to embed.

    Returns:
        list[list[float]]: A list of embedding vectors, with one vector corresponding to each input text.
    """
    response = client.embeddings.create(
        model=model,
        input=texts
    )
    embeddings = [emb.embedding for emb in response.data]
    return embeddings


def embed_bert(sentence_model, texts):
    """
    Generate text embeddings using a SentenceTransformer model.

    Args:
        sentence_model (SentenceTransformer): Initialized SentenceTransformer model used to generate the embeddings. Here "sentence-transformers/all-MiniLM-L6-v2"
        texts (list[str]): List of texts to embed.

    Returns:
        numpy.ndarray: Array containing one embedding vector for each input text.
    """
    embeddings = sentence_model.encode(texts, show_progress_bar=False)
    return embeddings


def embed_tfidf(texts, k):
    """
    Generate TF-IDF representations based on the highest-scoring terms in each document.

    Args:
        texts (list[str]): Texts from which the TF-IDF representations are generated.
        k (int): Number of highest-scoring terms to retain for each document.

    Returns:
        list[list[float]]: A list of TF-IDF vectors, one for each input text. The dimension of the representation is determined by the union of the selected top-k terms across the documents.
    """
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(texts)
    terms = vectorizer.get_feature_names_out()
    top_terms = set()
    docs = []
    for i in range(len(texts)):
        doc = [(terms[w], tfidf[i,w]) for w in tfidf[i,:].indices]
        doc.sort(key=lambda x: x[1])
        doc_top_terms = dict()
        for term_tfidf in doc[-k:]:
            top_terms.add(term_tfidf[0])
            doc_top_terms[term_tfidf[0]] = term_tfidf[1]
        docs.append(doc_top_terms)
    embeddings = list()
    for i in range(len(texts)):
        embedding = []
        for term in top_terms:
            if term in docs[i]:
                embedding.append(docs[i][term])
            else: embedding.append(0)
        embeddings.append(embedding)
    return embeddings