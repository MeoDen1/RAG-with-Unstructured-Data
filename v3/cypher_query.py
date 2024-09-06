from langchain_community.graphs import Neo4jGraph

def convert_quote(text: str) -> str:
    return text.replace("'", "\\'").replace('"', '\\"')

def convert2normal(text: str) -> str:
    return text.lower().capitalize()

def create_entity(kg: Neo4jGraph, entity_name: str, entity_type: str, description: str):
    entity_name = convert_quote(entity_name)
    entity_type = convert2normal(convert_quote(entity_type))
    description = convert_quote(description)
    """
    Create entity and entity type node (if not exist) node in Neo4j db
    """
    query = f"""
MERGE(et:{entity_type} {{type: '{entity_type}'}})
MERGE(e:Entity {{name: '{entity_name}'}})
SET e.description = '{description}'
MERGE(e)-[:TYPE]->(et)
"""
    return kg.query(query)


def create_relationship(kg: Neo4jGraph, source_entity: str, target_entity: str, description: str):
    """
    Create relationships between 2 entities. Entities are created if not exist
    """
    source_entity = convert_quote(source_entity)
    target_entity = convert_quote(target_entity)
    description = convert_quote(description)

    query = f"""
MERGE(e1:Entity {{name: '{source_entity}'}})
MERGE(e2:Entity {{name: '{target_entity}'}})
MERGE(e1)-[r:RELATED]->(e2)
SET r.description = '{description}'
"""
    
    return kg.query(query)


def drop_projected_graph(kg: Neo4jGraph, graph_name: str):
    """
    Drop projected graph from db
    """
    query = f"""
CALL gds.graph.drop("{graph_name}", false)
"""
    return kg.query(query)



def create_projected_graph(kg: Neo4jGraph, graph_name: str):
    """
    Create projected graph and store in-memory db
    """
    query = f"""
CALL gds.graph.project(
    "{graph_name}",
    ["Entity"],
    {{
        RELATED: {{orientation: "UNDIRECTED"}}
    }}
)
"""
    return kg.query(query)



def generate_graph_embedding(kg: Neo4jGraph, graph_name: str, d_embed: int = 128):
    """
    Using Node2Vec algorithm to embed `graph_name`
    """
    query = f"""
CALL gds.node2vec.mutate(
    "{graph_name}",
    {{
        mutateProperty: "embedding",
        embeddingDimension: {d_embed}
    }}
)
"""
    return kg.query(query)



def detect_communities(kg: Neo4jGraph, graph_name: str):
    """
    Using Leiden algorithm to generate a hierarchy of entity communities
    """
    query = f"""
CALL gds.leiden.mutate(
    "{graph_name}",
    {{
        mutateProperty: "communityId"
    }}
YIELD communityCount, modularity, modularities
"""
    
    return kg.query(query)