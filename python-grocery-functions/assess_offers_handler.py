import json
from bson.json_util import dumps

from assess_offers.core import get_s3_object_as_data_frame, get_vectorizer, get_best_offers_df, extract_quantity_value, extract_shopgun_quantity
from storage.db import save_promoted_offers


def assess_offers(event, context):
    BUCKET_NAME = 'grocery-prices'
    kolonial_df = get_s3_object_as_data_frame(
        BUCKET_NAME, 'kolonial_scraper_feed/simple_kolonial_spider-latest.json')
    meny_df = get_s3_object_as_data_frame(
        BUCKET_NAME, 'meny_scraper_feed/meny_spider-latest.json')
    shopgun_df = get_s3_object_as_data_frame(
        BUCKET_NAME, 'shopgun_scraper_feed/shopgun_catalog_spider-latest.json')

    # Standardizing fields
    kolonial_df['image_url'] = kolonial_df.image_url.map(
        lambda x: 'https://kolonial.no{}'.format(x).replace('product_list', 'product_large') if x[0] == '/' else x)
    shopgun_df['image_url'] = shopgun_df.images.map(lambda x: x['zoom'])
    shopgun_df['price'] = shopgun_df.pricing.map(lambda x: x['price'])
    shopgun_df['quantity_info'] = shopgun_df.quantity.map(
        extract_shopgun_quantity)
    shopgun_df['quantity_value'] = shopgun_df.quantity_info.map(
        extract_quantity_value)
    kolonial_df['quantity_value'] = kolonial_df.quantity_info.map(
        extract_quantity_value)
    kolonial_df['id'] = kolonial_df.kolonial_id
    kolonial_df['source'] = 'kolonial'
    meny_df['quantity_value'] = meny_df.quantity_info.map(
        extract_quantity_value)
    meny_df['id'] = meny_df.meny_id
    meny_df['source'] = 'meny'

    product_df = kolonial_df.append(
        meny_df, sort=False).fillna('').reset_index()
    offer_df = shopgun_df

    product_names = product_df['title'] + ' ' + \
        product_df['product_variant'] + ' ' + product_df['unit_price_raw']
    offer_names = offer_df['heading']

    vectorizer = get_vectorizer(product_names, offer_names)
    tf_idf_matrix = vectorizer.transform(product_names)

    best_offers_df = get_best_offers_df(
        shopgun_df, product_df, vectorizer, tf_idf_matrix)

    result = save_promoted_offers(best_offers_df)

    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event,
        "result": dumps(result.bulk_api_result),
    }
