from typing import Dict


# Union-Find data structure for grouping GTINs
class UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

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
