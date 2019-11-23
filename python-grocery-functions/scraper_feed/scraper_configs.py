import pydash

from amp_types.amp_product import ScraperConfig, MappingConfig

configs = {
    "www.iherb.com": {"fields": {"sku": "mpn"}},
    "meny": {
        "extractQuantityFields": ["unit_price_raw", "product_variant", "title"],
        "fields": {"sku": "ean", "product_variant": "description"},
    },
    "kolonial": {
        "extractQuantityFields": ["unit_price_raw", "product_variant", "title"],
        "fields": {"product_variant": "description"},
    },
    "europris": {
        "extractQuantityFields": ["description", "name"],
        "fields": {"name": "title", "link": "href"},
    },
}

DEFAULT_FIELD_MAP = {
    "additionalProperties": {},
    "fields": {
        "image": "imageUrl",
        "image_url": "imageUrl",
        "url": "href",
        "title": "title",
        "description": "description",
        "sku": "sku",
        "provenance_id": "provenanceId",
        "provenance": "provenance",
        "dealer": "dealer",
        "brand": "brand",
        "categories": "categories",
        "availability": "availability",
        "itemCondition": "itemCondition",
    },
    "extractQuantityFields": ["title", "description"],
}


def get_field_map(config: ScraperConfig) -> MappingConfig:
    try:
        special_config = configs[config["source"]]
        new_fields = {**DEFAULT_FIELD_MAP["fields"]}
        for k, v in special_config.get("fields", {}).items():
            new_fields[k] = pydash.flatten([v, new_fields.get(k, [])])

        result = {
            "additionalProperties": {
                **DEFAULT_FIELD_MAP,
                **special_config.get("additionalProperties", {}),
            },
            "fields": new_fields,
            "extractQuantityFields": special_config.get("extractQuantityFields", [])
            or DEFAULT_FIELD_MAP["extractQuantityFields"],
        }
        return result
    except KeyError:
        return DEFAULT_FIELD_MAP
