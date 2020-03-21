import pandas as pd
import json
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from time import time
import pickle
from pprint import pprint
import pydash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_union

import pymongo
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import Normalizer
from sklearn.base import TransformerMixin, BaseEstimator


class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        assert isinstance(X, pd.DataFrame)

        try:
            return X[self.columns]
        except KeyError:
            cols_error = list(set(self.columns) - set(X.columns))
            raise KeyError(
                "The DataFrame does not include the columns: %s" % cols_error
            )


class DataFrameColumnExtracter(TransformerMixin):
    def __init__(self, column):
        self.column = column

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if type(X) is pd.DataFrame:
            return X[self.column].fillna("")
        else:
            return X


def get_vec_pipe(column, num_comp=0, reducer="svd"):
    """ Create text vectorization pipeline with optional dimensionality reduction. """

    tfv = TfidfVectorizer(
        min_df=1,
        max_features=None,
        strip_accents="unicode",
        analyzer="char",
        token_pattern=r"\w{1,}",
        ngram_range=(3, 3),
        use_idf=1,
        smooth_idf=1,
        sublinear_tf=1,
    )

    # Vectorizer
    vec_pipe = [
        ("col_extr", DataFrameColumnExtracter(column)),
        # ('col_extr', JsonFields(0, ['title', 'body', 'url'])),
        # ('squash', Squash()),
        ("vec", tfv),
    ]

    # Reduce dimensions of tfidf
    if num_comp > 0:
        if reducer == "svd":
            vec_pipe.append(("dim_red", TruncatedSVD(num_comp)))
        elif reducer == "kbest":
            vec_pipe.append(("dim_red", SelectKBest(chi2, k=num_comp)))
        elif reducer == "percentile":
            vec_pipe.append(
                ("dim_red", SelectPercentile(f_classif, percentile=num_comp))
            )

        vec_pipe.append(("norm", Normalizer()))

    return Pipeline(vec_pipe)


def get_pipeline() -> FeatureUnion:
    pipeline_1 = get_vec_pipe("title")
    pipeline_2 = get_vec_pipe("subtitle")
    pipeline_3 = get_vec_pipe("description")
    pipeline_4 = get_vec_pipe("categoriesString")
    pipeline_5 = get_vec_pipe("combinedText")
    combined_pipeline = make_union(pipeline_1, pipeline_5)

    combined_pipeline.transformer_weights = {"pipeline-1": 16, "pipeline-2": 8}

    return combined_pipeline


def get_category_string(row):
    _categories = row.get("categories")
    categories = _categories[1:] if type(_categories) is list else []
    return " ".join((str(x) for x in categories))


def get_model(offers: list) -> dict:
    print(f"Creating model from {len(offers)} offers.")
    start_time = time()
    offers_df = get_processed_df(pd.DataFrame(offers))

    index_to_uri_map = offers_df["uri"].to_list()
    pipeline = get_pipeline()
    fitted_pipeline = pipeline.fit(offers_df)
    tf_idf_matrix = pipeline.transform(offers_df)

    print(f"Time spent: {time() - start_time} s.")
    return dict(
        index_to_uri_map=index_to_uri_map,
        fitted_pipeline=fitted_pipeline,
        tf_idf_matrix=tf_idf_matrix,
        offers_df=offers_df,
    )


def get_processed_df(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["categoriesString"] = result.apply(get_category_string, axis=1)
    result["combinedText"] = result.apply(get_combined_text, axis=1)
    return result


def get_combined_text(row: pd.Series):
    categories_string = get_category_string(row)
    values = [
        row.get("title", ""),
        row.get("subtitle", ""),
        row.get("description", ""),
        categories_string,
    ]
    result = " ".join(str(x) for x in values)
    return result


def keep_n_highest(arr, n=2):
    idx = np.argpartition(arr, -n)[-n:]
    result = np.array(np.zeros(arr.size))
    for i in idx:
        result[i] = arr[i]
    return result


def get_similarities(input_df, fitted_pipeline, tf_idf_matrix):
    match_matrix = cosine_similarity(fitted_pipeline.transform(input_df), tf_idf_matrix)
    return match_matrix


def get_most_similar_offers(offers: list, *args, **kwargs):
    offers_df = get_processed_df(pd.DataFrame(offers))
    return get_most_similar_offers_of_df(offers_df, *args, **kwargs)


def get_most_similar_offers_of_df(input_df, fitted_pipeline, tf_idf_matrix, n=16):
    print(f"Getting similar offers from {len(input_df)} offers.")
    start_time = time()
    match_matrix = get_similarities(input_df, fitted_pipeline, tf_idf_matrix)
    highest_matches = list(keep_n_highest(match, n) for match in match_matrix)
    match_indexes = list(matches.nonzero()[0] for matches in highest_matches)

    result = []
    for i, match in enumerate(highest_matches):
        sorted_matches = get_sorted_matches(match, match_indexes[i], n)
        result.append(sorted_matches)

    print(f"Time spent: {time() - start_time} s.")
    return result


def get_sorted_matches(matches, idx, n):
    return sorted(
        ({"idx": i, "score": score} for i, score in zip(idx, matches[idx[0:n]])),
        key=lambda x: -x["score"],
    )

