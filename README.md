# Visual-Clustering

# Visual Data Transformations

This tool allows you to iteratively cluster images into groups based on their visual descriptions. After each iteration you can manually inspect the clusters and alter the visual descriptions to improve the clustering result.

### Usage

**1. Create virtual environment with Python 3.12**

python3.12 -m venv .venv

**2. Activate it**

source .venv/bin/activate

**3. Install all packages with pip in the same env**

python -m pip install -r requirements.txt

**4. Run code**

python -m scripts.GUI.clustering_tool


### Input data

The input data should be provided as a .tsv file and contain at least the following columns:

| Column    | Description                        |
| --------- | ---------------------------------- |
| `ID`      | unique ID of the image             |
| `Dir`     | Directory containing the image     |
| `ImageID` | Image filename                     |
| `Labels`  | Generated description of the image |

### Output files

The output files are ordered per clustering round. 


| File | Columns | Description |
|---|---|---|
| `embeddings.csv` | `ID`, `embeddings` | Contains the image description embeddings. |
| `reductions.csv` | `ID`, `f0`, `f1`, `f2`, `f3`, `f4`, `f5`, `f6`, `f7`, `f8`, `f9` | Contains the dimensionality-reduced image description embeddings. |
| `clusters.csv` | `ID`, `ClusterID` | Maps each image to its assigned cluster. |
| `cluster_descriptions.csv` | `CID`, `Sil`, `Size`, `Term 0`, `Term 1`, `Term 2`, `Term 3`, `Term 4`, `Term 5`, `Term 6` | Contains cluster information, including cluster IDs, silhouette scores, sizes, and representative terms. |
| `cluster_texts.csv` | `ID`, `clusterId`, `path`, `text` | Contains the text and corresponding image information for all clusters. |
| `cluster_updates.csv` | `cluster_id`, `term`, `delete`, `new_term` | Contains the updates to be applied to image descriptions. |
| `updates_ids.json` | — | Contains the IDs of descriptions that have been updated. |
| `cluster_assessments.csv` | `cluster_id`, `coherence`, `meaningfulness` | Contains the coherence and meaningfulness assessments for each cluster. |
| `updated_input_file.csv` | `ID`, `Dir`, `ImageID`, `Labels` | Contains the updated image descriptions (available from round 2 onward). |



