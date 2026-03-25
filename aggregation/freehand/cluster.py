import json

import numpy as np
import pandas as pd
import tqdm
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances

from .freehandline import ClusterFreehandLine, ExtractFreehandLine


def metric(a: ExtractFreehandLine, b: ExtractFreehandLine) -> float:
    """Compute a distance between two freehand lines for DBSCAN clustering.

    Returns 1e6 (effectively infinite) in two cases:

    - ``a`` and ``b`` came from the same classification, so they can never
      be clustered together regardless of spatial proximity.
    - All per-point distances are zero, which indicates an exact duplicate
      that would distort the mean.

    Otherwise, the lines are aligned by comparing start-to-start vs
    start-to-end distances and reversing ``b`` if that yields better
    alignment. The distance is then the mean of each point in ``a``'s
    minimum distance to any point in ``b`` (ignoring zero-distance pairs).

    :param a: First freehand line.
    :type a: ExtractFreehandLine
    :param b: Second freehand line.
    :type b: ExtractFreehandLine
    :return: A non-negative scalar distance. Values near 1e6 indicate the
        lines should not be clustered together.
    :rtype: float
    """
    if a.classification_id == b.classification_id:
        return 1e6

    if np.linalg.norm(a.points[0] - b.points[0]) > np.linalg.norm(
        a.points[0] - b.points[-1]
    ):
        distances = pairwise_distances(a.points[:, :2], b.points[::-1, :2]).min(1)
    else:
        distances = pairwise_distances(a.points[:, :2], b.points[:, :2]).min(1)

    if np.max(distances) == 0:
        # print(distances)
        return 1e6

    distance = distances[distances > 0].mean()
    return distance


class Aggregator:
    """Clusters freehand line extractions into consensus lines per subject.

    Usage::

        agg = Aggregator("FreehandLine/polygon_extractor_extractions.csv")
        agg.cluster_lines(eps=10, min_samples=2)
        # results available in agg.clustered_lines
    """

    def __init__(self, extract_path: str):
        """Load and parse freehand line extractions from a CSV file.

        Reads the panoptes_aggregation polygon extractor output, parses the
        JSON path columns (``data.frame0.T0_tool0_pathX`` /
        ``data.frame0.T0_tool0_pathY``), and builds a flat list of
        :class:`ExtractFreehandLine` objects stored in ``self.extract_lines``.
        Rows where path data is missing or unparseable are silently skipped.

        :param extract_path: Path to the ``*_extractions.csv`` file produced
            by ``panoptes_aggregation extract``.
        :type extract_path: str
        """
        self.extract_data = pd.read_csv(extract_path)

        self.subject_ids = np.unique(self.extract_data['subject_id'])

        self.extract_lines = []

        for subject_id in tqdm.tqdm(
            self.subject_ids,
            dynamic_ncols=True,
            desc="Loading extract data",
            ascii=True,
        ):
            classifications = self.extract_data[
                self.extract_data['subject_id'] == subject_id
            ]
            for idx, classification in classifications.iterrows():
                # get the list of lines first
                try:
                    pathX = json.loads(classification['data.frame0.T0_tool0_pathX'])
                    pathY = json.loads(classification['data.frame0.T0_tool0_pathY'])
                except Exception:
                    continue

                for (xx, yy) in zip(pathX, pathY):
                    extract_line = ExtractFreehandLine(
                        subject_id,
                        np.stack([xx, yy], axis=1),
                        classification['classification_id'],
                    )

                    self.extract_lines.append(extract_line)

        self.extract_lines = np.asarray(self.extract_lines)

    def cluster_lines(self, eps: float = 10, min_samples: int = 2):
        """Cluster extracted lines per subject using DBSCAN.

        For each subject, computes a pairwise distance matrix using
        :func:`metric` and runs DBSCAN with a precomputed metric. Outlier
        lines (DBSCAN label ``-1``) are discarded. Within each cluster, all
        lines are reoriented to match the direction of the first line so that
        downstream averaging is meaningful. Results are stored in
        ``self.clustered_lines``.

        :param eps: Maximum distance between two lines to be considered
            neighbours in DBSCAN (pixels).
        :type eps: float
        :param min_samples: Minimum number of lines required to form a cluster.
        :type min_samples: int
        """
        self.clustered_lines = []
        extract_subject_ids = [e.subject_id for e in self.extract_lines]
        for subject in tqdm.tqdm(
            self.subject_ids, desc="Clustering lines", dynamic_ncols=True, ascii=True
        ):
            extract_lines = self.extract_lines[
                np.where(extract_subject_ids == subject)[0]
            ]

            if len(extract_lines) < 2:
                continue

            distances = np.zeros((len(extract_lines), len(extract_lines)))
            for i in range(len(extract_lines)):
                for j in range(len(extract_lines)):
                    distances[i, j] = metric(extract_lines[i], extract_lines[j])

            clusterer = DBSCAN(
                eps=eps, min_samples=min_samples, metric='precomputed'
            ).fit(distances)

            labels = clusterer.labels_

            for label in np.unique(labels):
                # skip the outlier labels
                if label < 0:
                    continue
                cluster_lines = extract_lines[np.where(labels == label)[0]]

                points_0 = cluster_lines[0].points[0]
                for i, line in enumerate(cluster_lines):
                    if i == 0:
                        continue

                    if np.linalg.norm(line.points[0] - points_0) > np.linalg.norm(line.points[-1] - points_0):
                        cluster_lines[i].points = line.points[::-1]

                self.clustered_lines.append(
                    ClusterFreehandLine(subject, cluster_lines[0], cluster_lines)
                )
