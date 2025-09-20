
from amp_types.amp_product import ProcessedMpnOffer


# Union-Find data structure for grouping GTINs
class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        # Path compression
        if x not in self.parent:
            self.parent[x] = x
        while x != self.parent[x]:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: str, y: str) -> None:
        xroot: str = self.find(x)
        yroot: str = self.find(y)
        if xroot != yroot:
            self.parent[yroot] = xroot


def get_offer_from_gtin(
    gtin_offer_object_map: dict[str, ProcessedMpnOffer], gtin: str
) -> ProcessedMpnOffer:
    return gtin_offer_object_map[gtin]
