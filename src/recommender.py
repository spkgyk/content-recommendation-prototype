from scipy.sparse import csr_matrix
from typing import Tuple, List
import concurrent.futures
import pandas as pd
import numpy as np
import faiss

from data_loader import get_svd_matrix


class Recommender:
    def __init__(self, article_metadata: pd.DataFrame, clicks_data: pd.DataFrame):
        self.article_metadata = article_metadata
        self.clicks_data = clicks_data

        self.item_user_matrix = self._create_item_user_matrix()
        self.user_matrix, self.article_matrix = self._compute_matrix_factorization()
        self.user_publisher_indices = self._create_user_preference_indices("publisher_id")
        self.user_category_indices = self._create_user_preference_indices("category_id")
        self.embeddings_index = self._build_embeddings_index()
        self.popular_articles = self._precompute_popular_articles()

    def _create_item_user_matrix(self) -> csr_matrix:
        interaction_freq = self.clicks_data.groupby(["user_id", "click_article_id"]).size().reset_index(name="frequency")

        rows = interaction_freq["user_id"].values
        cols = interaction_freq["click_article_id"].values
        data = interaction_freq["frequency"].values
        shape = (rows.max() + 1, cols.max() + 1)

        item_user_matrix = csr_matrix((data, (rows, cols)), shape=shape)
        return item_user_matrix

    def _create_user_preference_indices(self, column_name: str) -> List[List[int]]:
        rows = self.clicks_data["user_id"].values
        cols = self.clicks_data[column_name].values
        data = np.ones(len(self.clicks_data))
        shape = (rows.max() + 1, cols.max() + 1)

        matrix = csr_matrix((data, (rows, cols)), shape=shape)

        return matrix.tolil().rows.tolist()

    def _build_embeddings_index(self) -> faiss.IndexFlatIP:
        embedding_matrix = np.stack(self.article_metadata["embedding"].values)
        embeddings_index = faiss.IndexFlatIP(embedding_matrix.shape[1])
        embeddings_index.add(embedding_matrix)
        return embeddings_index

    def _precompute_popular_articles(self):
        article_popularity = np.bincount(self.clicks_data["click_article_id"].values)
        popular_article_indices = article_popularity.argsort()[::-1]
        popular_articles_df = self.article_metadata.iloc[popular_article_indices].copy()
        popular_articles_df["score"] = article_popularity[popular_article_indices] / article_popularity.max() * 6
        return popular_articles_df

    def _compute_matrix_factorization(self) -> Tuple[np.ndarray, np.ndarray]:
        return get_svd_matrix(self.item_user_matrix)

    def recommend(self, user_id: int, k: int = 10) -> pd.DataFrame:
        if user_id >= self.item_user_matrix.shape[0]:
            # Cold start: recommend popular articles
            return self.popular_articles.iloc[:k]

        # Get user's interacted articles
        interacted_articles = self.item_user_matrix[user_id].nonzero()[1]
        time_spent = self.item_user_matrix[user_id].data

        if len(interacted_articles) == 0:
            return self.popular_articles.iloc[:k]

        # Execute CF score computation in a separate thread at the beginning
        user_factor = self.user_matrix[user_id]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._compute_cf_scores, self.article_matrix, user_factor)

            # Compute average embedding of interacted articles
            article_embeddings = self.article_metadata["embedding"].values[interacted_articles]
            avg_embedding: np.ndarray = np.average(article_embeddings, axis=0, weights=time_spent)

            # Find similar articles using faiss
            similar_scores, similar_articles = self.embeddings_index.search(avg_embedding.reshape(1, -1), k * 5)
            similar_scores: np.ndarray = similar_scores[0]
            similar_articles: np.ndarray = similar_articles[0]

            non_interacted_mask = np.isin(similar_articles, interacted_articles, invert=True)
            similar_scores, similar_articles = similar_scores[non_interacted_mask], similar_articles[non_interacted_mask]

            # Get recommended articles
            recommended_articles: pd.DataFrame = self.article_metadata.iloc[similar_articles].copy()
            recommended_articles["score"] = 2 * similar_scores / similar_scores.max()

            # Boost scores for user's favorite publishers and categories
            user_publishers = self.user_publisher_indices[user_id]
            user_categories = self.user_category_indices[user_id]

            recommended_articles.loc[recommended_articles["publisher_id"].isin(user_publishers), "score"] += 1
            recommended_articles.loc[recommended_articles["category_id"].isin(user_categories), "score"] += 1

            # Boost scores for articles with similar word length to user's average word length
            user_avg_word_length = self.article_metadata.loc[interacted_articles, "words_count"].mean()
            word_length_diff: np.ndarray = np.absolute(recommended_articles["words_count"] - user_avg_word_length)
            word_length_score = 1 - (word_length_diff / word_length_diff.max())
            recommended_articles["score"] += word_length_score

            # Exponential decay for recency score
            max_article_time = self.article_metadata["created_at_ts"].max()
            min_article_time = self.article_metadata["created_at_ts"].min()
            max_age = max_article_time - min_article_time
            normalized_age = (recommended_articles["created_at_ts"] - max_article_time) / max_age
            recency_score = np.exp(30 * normalized_age)
            recommended_articles["score"] += recency_score

            # Wait for the CF scores to be computed
            cf_scores = future.result()
            recommended_articles["score"] += cf_scores[recommended_articles.index]

            # Sort by score
            recommended_articles = recommended_articles.sort_values("score", ascending=False)

            return recommended_articles.iloc[:k]

    def _compute_cf_scores(self, article_matrix: np.ndarray, user_factor: np.ndarray):
        cf_scores: np.ndarray = article_matrix.dot(user_factor)
        cf_scores = 2 * (cf_scores - cf_scores.min()) / (cf_scores.max() - cf_scores.min())
        return cf_scores
