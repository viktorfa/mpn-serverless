import pickle

import pandas as pd
from sklearn.base import TransformerMixin


def unpickle(p):
    return CustomUnpickler(p).load()


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


class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == "DataFrameColumnExtracter":
            return DataFrameColumnExtracter
        return super().find_class(module, name)
