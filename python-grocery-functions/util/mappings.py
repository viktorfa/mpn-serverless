def get_offer_context_from_site_collection(site_collection: str) -> str:
    if site_collection in site_collection_to_context:
        return site_collection_to_context[site_collection]
    else:
        raise ValueError(f"Unknown site collection: {site_collection}")


site_collection_to_context = {
    "groceryoffers": "amp-no",
    "byggoffers": "bygg-no",
    "beautyoffers": "beauty-no",
    "suppoffers": "supp-no",
    #
    "degroceryoffers": "amp-de",
    "debyggoffers": "bygg-de",
    "debeautyoffers": "beauty-de",
    #
    "dkgroceryoffers": "amp-dk",
    "dkbyggoffers": "bygg-dk",
    "dkbeautyoffers": "beauty-dk",
    #
    "segroceryoffers": "amp-se",
    "sebyggoffers": "bygg-se",
    "sebeautyoffers": "beauty-se",
    #
    "figroceryoffers": "amp-fi",
    #
    "plgroceryoffers": "amp-pl",
    #
    "nlgroceryoffers": "amp-nl",
    #
    "frgroceryoffers": "amp-fr",
    #
    "esgroceryoffers": "amp-es",
    #
    "ukgroceryoffers": "amp-uk",
    "ukbyggoffers": "bygg-uk",
    "ukbeautyoffers": "beauty-uk",
    #
    "itgroceryoffers": "amp-it",
    #
    "usgroceryoffers": "amp-us",
    "usbeautyoffers": "beauty-us",
    "usbyggoffers": "bygg-us",
    #
    "augroceryoffers": "amp-au",
    #
    "thgroceryoffers": "amp-th",
    #
    "sggroceryoffers": "amp-sg",
}
