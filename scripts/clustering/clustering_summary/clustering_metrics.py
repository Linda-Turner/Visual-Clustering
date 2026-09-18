import numpy as np

from sklearn.metrics import silhouette_samples
from collections import Counter


def cluster_silhouette_scores(
        features,
        cluster_labels
    ):
    s_samples = silhouette_samples(features, cluster_labels)
    clusters = Counter(cluster_labels)

    num_samples = len(s_samples)
    res = dict()
    for sil in range(num_samples):
        c = cluster_labels[sil]
        if int(c) not in res:
            res[int(c)] = 0
        res[int(c)] = res[int(c)] + float(s_samples[sil].item()) / clusters[c]
    return res
