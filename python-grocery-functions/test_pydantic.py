from polyfactory.factories.pydantic_factory import ModelFactory

from storage.postgres.pydantic_models import PydanticHandleConfig


class HandleFeedConfigFactory(ModelFactory[PydanticHandleConfig]):
    """Factory for generating realistic HandleFeedConfig test data."""

    __model__ = PydanticHandleConfig
    __check_model__ = False  # Disable model checking to avoid deprecation warning


j_model = HandleFeedConfigFactory.build(categoriesLimits=[1, None])  # type: ignore
j_dict = j_model.model_dump()
j_model = PydanticHandleConfig(**j_dict)


print(j_model.categoriesLimits)
