import json
from typing import Optional

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from storage.s3 import get_s3_file_content


def get_s3_object_as_data_frame(bucket: str, key: str) -> pd.DataFrame:
    """
    Gets a json file from s3 as a pandas data frame.
    """
    return pd.read_json(get_s3_file_content(bucket, key))


def get_best_offers_df(offer_df, product_df, vectorizer, tf_idf_matrix, n=30) -> pd.DataFrame:
    """
    Gets a data frame with the best offers according to the code in this function.
    """
    offers = []
    for i, row in offer_df.iterrows():
        match = cosine_similarity(
            vectorizer.transform([row.heading]), tf_idf_matrix)
        highest = keep_n_highest(match[0], 1)
        idx = highest.nonzero()[0]
        if idx.size > 0 and highest[idx[0]] > .5:
            product = product_df.iloc[idx[0]]
            if quantity_equal(product, row) and row.price and product['price']:
                price_diff = row.price - product['price']
                diff_ratio = row.price / product['price']
                if price_diff < 0:
                    offer = dict(
                        offer_index=i,
                        product_index=idx[0],
                        source=product['source'],
                        rebate=1 - diff_ratio,
                        offer_name=row.heading,
                        product_name=product.title,
                    )
                    offers.append(offer)
    unique_offers = [offer for i, offer in enumerate(
        offers) if offer['offer_name'] not in [x['offer_name'] for x in offers[i+1:]]]
    best_offers = sorted(
        unique_offers, key=lambda x: x['rebate'], reverse=True)[:30]
    best_offers
    best_offers_df = pd.DataFrame([get_offer_object_from_shopgun_object(
        offer_df.iloc[x['offer_index']], x) for x in best_offers])
    return best_offers_df


def quantity_equal(product, offer) -> bool:
    try:
        return product['quantity_info'][0][0] == offer['quantity_info'][0]
    except Exception:
        return False


def is_unique(item, index, _list) -> bool:
    return item['name'] in [x['name'] for x in _list[index:]]


def get_offer_object_from_shopgun_object(shopgun_object, offer_object) -> dict:
    return {
        **shopgun_object,
        'rebate': offer_object['rebate'],
        'offer_index': offer_object['offer_index'],
        'product_index': offer_object['product_index'],
        'source': offer_object['source'],
    }


def keep_n_highest(arr, n=2):
    idx = np.argpartition(arr, -n)[-n:]
    result = np.array(np.zeros(arr.size))
    for i in idx:
        result[i] = arr[i]
    return result


def get_vectorizer(product_names, offer_names):
    vectorizer = TfidfVectorizer(
        min_df=1,
        strip_accents='unicode',
        use_idf=True,
    )

    vectorizer.fit(product_names)
    vectorizer.fit(offer_names)
    return vectorizer


def extract_shopgun_quantity(shopgun_quantity) -> Optional[list]:
    try:
        return [shopgun_quantity['size']['from'], shopgun_quantity['unit']['symbol']]
    except KeyError:
        return None
    except TypeError:
        return None


def extract_quantity_value(quantity_info) -> Optional[float]:
    if quantity_info and type(quantity_info) is list and len(quantity_info) > 0:
        try:
            return quantity_info[0][0]
        except TypeError:
            return quantity_info[0]
    else:
        return None
