from typing import Any, List, Literal, TypedDict


class MappingConfigField(TypedDict):
    value_type: str
    replace_type: Literal["fixed", "key", "ignore"]
    replace_value: Any
    source: str
    destination: str
    text: str
    force_replace: bool


DEFAULT_EXTRACT_QUANTITY_FIELDS = []
DEFAULT_EXTRACT_PROPERTIES_FIELDS = ["title", "subtitle"]
DEFAULT_EXTRACT_INGREDIENTS_FIELDS = ["rawIngredients"]
DEFAULT_EXTRACT_CATEGORIES_FIELD = "categories"

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
