import os
from tqdm import tqdm
import pandas as pd
from sklearn.preprocessing import StandardScaler, Normalizer, MinMaxScaler
from sklearn.decomposition import PCA
from umap import UMAP

def reduce_dim(
        input_file, 
        output_file, 
        output_dir, 
        batch : int = 10**10,
        scaling : str = 'normalize', 
        model : str = 'umap', 
        components : int = 10, 
        neighbors : int = 5, 
        decimals : int  = 30, 
        progress_callback = None, 
        indeterminate_callback = None
    ):
    """
    Reduce the dimensionality of embeddings using PCA or UMAP.

    Args:
        input_file (str): Path to the CSV file containing the embeddings. The first column must contain the IDs and all remaining columns must contain numerical embedding features.
        output_file (str): Name of the CSV file to which the reduced embeddings are written.
        output_dir (str): Directory in which the output file will be saved.
        batch (int, optional): Number of rows to process at a time. Defaults to 10**10.
        scaling (str, optional): Scaling method applied to the embeddings before dimensionality reduction. Defaults to 'normalize'. Supported options are:
                - 'normalize': Normalize each sample.
                - 'minmax': Scale each feature to a range between 0 and 1.
        model (str, optional): Dimensionality-reduction algorithm. Defaults to 'umap'. Supported options are:
                - 'umap': Uniform Manifold Approximation and Projection.
                - 'pca': Principal Component Analysis.
        components (int, optional): Number of dimensions in the reduced representation. Defaults to 10.
        neighbors (int, optional): Number of neighboring points used by UMAP when constructing the local manifold. Defaults to 5.
        decimals (int, optional): Number of decimal places used when writing the reduced embeddings to the output file. Defaults to 30.
    """
    print(f"\n{'='*60}")
    print("Dimensionality reduction started ...")

    output_file = os.path.join(output_dir, output_file)

    print(input_file)
    with pd.read_csv(input_file, header=None, chunksize=batch) as reader:
        total = sum(1 for _ in reader)

    with pd.read_csv(input_file, header=None, chunksize=batch) as reader:
        first_batch = True
        count = 0
        for df in tqdm(reader):
            ids = df.loc[:, df.columns[0:1]]
            features = df.loc[:, df.columns[1:]]
            count += 1

            if first_batch:
                scaler, model = fit_scaler_and_model(features, scaling, model, neighbors, components, indeterminate_callback)
                reduced_features = transform(scaler, model, features, ids,decimals)
                reduced_features.to_csv(output_file, mode='w', index=False)
                first_batch = False
            else:
                reduced_features = transform(scaler, model, features, ids,decimals)
                reduced_features.to_csv(output_file, mode='a', index=False, header=False)

            if progress_callback:
                progress_callback(count, total, "Reducing dimensions of image embeddings in batches...")

    return None


def transform(scaler, model, features, ids, decimals):
    """
    Transform a batch of embeddings using a fitted scaler and dimensionality-reduction model.

    Args:
        scaler: Fitted scaler used to preprocess the features. If None, no scaling is performed.
        model: Fitted dimensionality-reduction model, such as PCA or UMAP.
        features (pandas.DataFrame): DataFrame containing the embedding features to transform.
        ids (pandas.DataFrame): DataFrame containing the IDs corresponding to the embeddings.

    Returns:
        pandas.DataFrame: A DataFrame containing the original IDs followed by the reduced features.
    """
    if scaler is not None:
        features = scaler.transform(features)
    reduced_features = model.transform(features)
    reduced_features = reduced_features.round(decimals)
    reduced_features = pd.DataFrame(reduced_features,columns=[f"f{i}" for i in range(reduced_features.shape[1])])
    ids = ids.reset_index(drop=True)
    reduced_features = reduced_features.reset_index(drop=True)
    data = pd.concat([ids, reduced_features],axis="columns")
    data.columns = ["ID"] + [f"f{i}" for i in range(reduced_features.shape[1])]
    return data


def fit_scaler_and_model(features, scaling, model, neighbors, components, indeterminate_callback=None):
    """
    Fit the selected scaler and dimensionality-reduction model on a batch of embeddings.

    Args:
        features (pandas.DataFrame): DataFrame containing the embedding features to fit the scaler and reduction model.
        scaling (str): Scaling method. Available options are:
                - 'minmax': Min-max scaling.
                - 'normalize': Normalize each sample.
        model (str): Dimensionality-reduction algorithm. Available options are:
                - 'umap': Uniform Manifold Approximation and Projection.
                - 'pca': Principal Component Analysis.
        neighbors (int): Number of neighboring points used by UMAP. 
        components (int): Number of dimensions in the reduced representation.

    Returns:
        tuple: A tuple containing:
            - scaler: The fitted scaler, or None if scaling is disabled.
            - model: The fitted dimensionality-reduction model.
    """
    # Instances of scalers
    if indeterminate_callback:
        indeterminate_callback("Fitting scaling model on first batch ...")
    if scaling == "minmax":
        scaler = MinMaxScaler()
        scaler.fit(features)
        # To fit the reduction model on scaled data
        features = scaler.transform(features)
    elif scaling == "normalize":
        scaler = Normalizer()
        # To fit the reduction model on scaled data
        features = scaler.transform(features)
    elif scaling == "standard":
        scaler = StandardScaler()
        scaler.fit(features)
        # To fit the reduction model on scaled data
        features = scaler.transform(features)
    else:
        scaler = None
    print(f'Using {scaling} scaler:')

    if indeterminate_callback:
        indeterminate_callback("Fitting dimension reduction model on first batch ...")
    # Instances of model
    if model == "umap":
        model = UMAP(n_neighbors=neighbors, n_components=components, min_dist=0.0, metric='cosine')
    elif model == "pca":
        model = PCA(components)

    model.fit(features)

    print(f'Using {model} model:', model)
    return scaler, model
