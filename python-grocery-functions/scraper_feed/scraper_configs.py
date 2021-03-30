from typing import List

from amp_types.amp_product import MappingConfigField

DEFAULT_EXTRACT_QUANTITY_FIELDS = []

DEFAULT_FIELD_MAPPING = [
    {
        "source": "image",
        "destination": "imageUrl",
        "replace_type": "key",
    },
    {
        "source": "image_url",
        "destination": "imageUrl",
        "replace_type": "key",
    },
    {
        "source": "url",
        "destination": "href",
        "replace_type": "key",
    },
]


def get_field_mapping(
    config_fields: List[MappingConfigField] = [],
) -> List[MappingConfigField]:
    if not config_fields:
        config_fields = []
    result = [*DEFAULT_FIELD_MAPPING, *config_fields]
    return result
