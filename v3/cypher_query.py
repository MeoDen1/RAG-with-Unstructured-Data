from langchain_community.graphs import Neo4jGraph

def convert_quote(text: str) -> str:
    return text.replace("'", "\\'").replace('"', '\\"')

def convert2normal(text: str) -> str:
    return text.lower().capitalize()

def create_entity(kg: Neo4jGraph, entity_name: str, entity_type: str, description: str):
    """
    Create entity and entity type node (if not exist) node in Neo4j db
    """

    entity_name = convert_quote(entity_name)
    entity_type = convert2normal(convert_quote(entity_type))
    description = convert_quote(description)

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
MATCH (e1: Entity)-[r:RELATED]->(e2: Entity)
CALL gds.graph.project(
    "{graph_name}",
    e1,
    e2,
    {{}},
    {{
        undirectedRelationshipTypes: ['*']
    }}
)
"""
    return kg.query(query)



def create_graph_embedding(kg: Neo4jGraph, graph_name: str, d_embed: int = 128):
    """
    Using Node2Vec algorithm to embed `graph_name`
    """
    query = f"""
CALL gds.node2vec.write(
    "{graph_name}",
    {{
        writeProperty: "embedding",
        embeddingDimension: {d_embed}
    }}
)
"""
    return kg.query(query)



def generate_communities(kg: Neo4jGraph, graph_name: str):
    """
    Using Leiden algorithm to generate a hierarchy of entity communities
    """
    query = f"""
CALL gds.leiden.write(
    "{graph_name}",
    {{
        writeProperty: "communityId"
    }}
)
YIELD communityCount, modularity, modularities
"""
    
    return kg.query(query)


def create_community(kg: Neo4jGraph, community_id: int, title: str, summary: str, rating: float, rating_explanation: str, findings: str, embedding):
    """
    Create community node
    """
    title = convert_quote(title)
    summary = convert_quote(summary)
    rating_explanation = convert_quote(rating_explanation)
    findings = convert_quote(findings)
    
    query = f"""
MATCH (e:Entity)
WHERE e.communityId = {community_id}
MERGE (c:Community {{id: {community_id}}})
SET c.title = '{title}'
SET c.summary = '{summary}'
SET c.rating = {rating}
SET c.rating_explanation = '{rating_explanation}'
SET c.findings = '{findings}'
MERGE (e)-[:BELONG_TO]->(c)
WITH c
CALL db.create.setNodeVectorProperty(c, "embedding", {embedding})
"""

    return kg.query(query)


def embed_community_summary(kg: Neo4jGraph, index_name: str, vector_dim: int):
    """
    Embed community summary
    """

    query = f"""
CREATE VECTOR INDEX {index_name} IF NOT EXISTS
FOR (c:Community)
ON (c.summary)
OPTIONS {{
    `vector.dimensions`: {vector_dim},
    `vector.similarity_function`: 'cosine'
}}
"""

    kg.query(query)



#######
# GET

def get_list_community(kg: Neo4jGraph):
    """
    Return list of community id
    """
    query = """
MATCH (n:Entity) RETURN DISTINCT n.communityId AS communityId
"""
    result = kg.query(query)
    output = []
    for obj in result:
        output.append(obj['communityId'])

    return output


def get_community_info(kg: Neo4jGraph, community_id: int):
    """
    Get all entites and relationship from community `community_id` to fit for community summarize prompt.
    """

    # Retrieve all entity and relationship related to community
    query = f"""
MATCH (e1: Entity)
WHERE e1.communityId = {community_id}
RETURN e1.name, e1.description
"""

    result = kg.query(query)
    output1 = set()
    for res in result:
        if res["e1.description"] is None:
            res["e1.description"] = "None"
        output1.add(','.join([res["e1.name"], res["e1.description"]]))

############
    query = f"""
MATCH (e1: Entity)-[r:RELATED]->(e2:Entity)
WHERE e1.communityId = {community_id}
RETURN e1.name, e2.name, r.description    
"""
    result = kg.query(query)
    output2 = set()
    for res in result:
        if res["r.description"] is None:
            res["r.description"] = "None"
        output2.add(','.join((res["e1.name"], res["e2.name"], res["r.description"])))
    

    return list(output1), list(output2)


def get_search_result(kg: Neo4jGraph, index_name: str, result_number: int, query):
    query = f"""
CALL db.index.vector.queryNodes("{index_name}", {result_number}, {query})
YIELD node AS c, score
RETURN c.title AS title, c.summary AS summary, c.rating AS rating, c.rating_explanation AS re, c.findings as findings, score
"""
    
    result = kg.query(query)
    output = []
    for res in result:
        output.append([res["title"], res["summary"], res["rating"], res["re"], res["findings"], res["score"]])

    return output