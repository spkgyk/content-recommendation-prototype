from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np
import pickle
import os

DATA_DIR = Path(os.path.dirname(__file__)).resolve().parents[0] / "data"


def load_data(verbose: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    article_metadata = pd.read_csv(DATA_DIR / "articles_metadata.csv")
    if verbose:
        print("[INFO] Article Metadata loaded into memory.")

    with open(DATA_DIR / "articles_embeddings.pickle", "rb") as f:
        article_embeddings = pickle.load(f)
    if verbose:
        print("[INFO] Article Embeddings loaded into memory.")

    clicks_folder_path = DATA_DIR / "clicks"
    clicks = []

    for filename in os.listdir(clicks_folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(clicks_folder_path, filename)
            clicks.append(pd.read_csv(file_path))

    clicks_data = pd.concat(clicks, ignore_index=True)
    if verbose:
        print("[INFO] User Clicks data loaded into memory.")

    clicks_data = clicks_data.merge(article_metadata, left_on="click_article_id", right_on="article_id").drop(columns=["article_id"])
    if verbose:
        print("[INFO] User Clicks and Article Metadata merged.")

    article_metadata["embedding"] = list(article_embeddings)

    return article_metadata, clicks_data


def get_svd_matrix(
    item_user_matrix: csr_matrix,
    n_components: int = 400,
    eps: float = 1e-8,
    verbose: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:

    svd_file_path = DATA_DIR / f"svd_{n_components}.pkl"

    if svd_file_path.exists():
        if verbose:
            print(f"[INFO] Loading SVD matrix from {svd_file_path} into memory...")
        with open(svd_file_path, "rb") as file:
            svd_results = pickle.load(file)
            user_factors = svd_results["user_factors"]
            item_factors = svd_results["item_factors"]
        if verbose:
            print("[INFO] SVD matrix loaded into memory.")
    else:
        if verbose:
            print("[INFO] Running SVD on item-user matrix...")
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        user_factors = svd.fit_transform(item_user_matrix)

        # n_components = 250 explains 80% of the variance in the item_user_matrix
        explained_variance = np.cumsum(svd.explained_variance_ratio_)
        plt.plot(range(1, n_components + 1), explained_variance)
        plt.xlabel("Number of Components")
        plt.ylabel("Cumulative Explained Variance")
        plt.title("Explained Variance by Number of SVD Components")
        plt.grid(True)
        plt.show()

        user_factors /= np.linalg.norm(user_factors, axis=1, keepdims=True) + eps
        item_factors = svd.components_.T
        item_factors /= np.linalg.norm(item_factors, axis=1, keepdims=True) + eps

        with open(svd_file_path, "wb") as file:
            pickle.dump({"user_factors": user_factors, "item_factors": item_factors}, file)

        if verbose:
            print(f"[INFO] SVD completed, result saved to {svd_file_path}.")

    return user_factors, item_factors


# article_metadata, clicks_data = load_data()

# print(clicks_data.iloc[0])
