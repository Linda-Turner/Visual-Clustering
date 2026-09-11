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


