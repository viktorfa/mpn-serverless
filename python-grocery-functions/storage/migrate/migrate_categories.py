import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config.vars import POSTGRES_URL
from storage.postgres.postgres_tables import CategoriesTable


def topological_sort(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from collections import defaultdict, deque

    # Build the graph
    graph = defaultdict(list)  # parent -> list of children
    in_degree = defaultdict(int)  # child -> number of incoming edges

    # Create a mapping from (context, key) to item
    category_map = {}
    for item in categories:
        key = item.get("key")
        context = item.get("context")
        category_map[(context, key)] = item

    for item in categories:
        key = item.get("key")
        context = item.get("context")
        parent_key = item.get("parent")
        if parent_key:
            parent = (context, parent_key)
            graph[parent].append((context, key))
            in_degree[(context, key)] += 1

    # Initialize queue with nodes having in_degree 0 (no dependencies)
    queue = deque()
    for item in categories:
        key = item.get("key")
        context = item.get("context")
        if in_degree[(context, key)] == 0:
            queue.append((context, key))

    sorted_categories = []
    while queue:
        current = queue.popleft()
        context, key = current
        sorted_categories.append(category_map[current])

        for child in graph[current]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(sorted_categories) != len(categories):
        raise ValueError("Cycle detected or missing parent categories.")

    return sorted_categories


def migrate_data(json_file_path, database_url):
    # Create the database engine
    engine = create_engine(database_url)

    # Read the JSON file
    with open(json_file_path) as f:
        data = json.load(f)

    try:
        sorted_data = topological_sort(data)
    except ValueError as ve:
        print(f"Error during sorting: {ve}")
        raise

    with Session(engine) as session:
        try:
            for item in sorted_data:
                # Map the fields
                key = item.get("key")
                context = item.get("context")
                level = item.get("level")
                title = item.get("text") if "text" in item else item.get("name")
                description = item.get("description")
                active = item.get("active")
                parent = item.get("parent")

                # Create the Spider instance
                category = CategoriesTable(
                    key=key,
                    context=context,
                    level=level,
                    title=title,
                    description=description,
                    active=active,
                    parent=parent,
                )

                # Add to session
                session.add(category)

            # Commit the session
            session.commit()
        except:
            session.rollback()
            raise


if __name__ == "__main__":
    json_file_path = Path(__file__).parent.parent / "strapi.mpncategories.json"
    json_file = str(json_file_path)

    migrate_data(json_file, POSTGRES_URL)
