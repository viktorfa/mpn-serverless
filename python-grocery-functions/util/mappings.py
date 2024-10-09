def get_offer_context_from_site_collection(site_collection: str) -> str:
    if site_collection in site_collection_to_context:
        return site_collection_to_context[site_collection]
    else:
        raise ValueError(f"Unknown site collection: {site_collection}")


site_collection_to_context = {
    "herbvuoffers": "herbvu",
    #
    "groceryoffers": "amp-no",
    "byggoffers": "bygg-no",
    "beautyoffers": "beauty-no",
    "suppoffers": "supp-no",
    "bookoffers": "book-no",
    "extraoffers": "extra-no",
    #
    "degroceryoffers": "amp-de",
    "debyggoffers": "bygg-de",
    "debeautyoffers": "beauty-de",
    "deextraoffers": "extra-de",
    #
    "dkgroceryoffers": "amp-dk",
    "dkbyggoffers": "bygg-dk",
    "dkbeautyoffers": "beauty-dk",
    "dkextraoffers": "extra-dk",
    #
    "segroceryoffers": "amp-se",
    "sebyggoffers": "bygg-se",
    "sebeautyoffers": "beauty-se",
    "seextraoffers": "extra-se",
    #
    "figroceryoffers": "amp-fi",
    "fibyggoffers": "bygg-fi",
    "fiextraoffers": "extra-fi",
    #
    "plgroceryoffers": "amp-pl",
    "plextraoffers": "extra-pl",
    #
    "nlgroceryoffers": "amp-nl",
    "nlextraoffers": "extra-nl",
    #
    "frgroceryoffers": "amp-fr",
    "frextraoffers": "extra-fr",
    #
    "esgroceryoffers": "amp-es",
    "esextraoffers": "extra-es",
    #
    "ukgroceryoffers": "amp-uk",
    "ukbyggoffers": "bygg-uk",
    "ukbeautyoffers": "beauty-uk",
    "ukextraoffers": "extra-uk",
    #
    "itgroceryoffers": "amp-it",
    "itextraoffers": "extra-it",
    #
    "usgroceryoffers": "amp-us",
    "usbeautyoffers": "beauty-us",
    "usbyggoffers": "bygg-us",
    "usextraoffers": "extra-us",
    #
    "augroceryoffers": "amp-au",
    "auextraoffers": "extra-au",
    #
    "thgroceryoffers": "amp-th",
    "thextraoffers": "extra-th",
    #
    "sggroceryoffers": "amp-sg",
    "sgextraoffers": "extra-sg",
}
