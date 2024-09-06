# Sources: https://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/summarize/prompts.py

def get_prompt(entity_name: str | list[str], description_list: list[str]):
    SUMMARIZE_PROMPT = f"""
Given one or two entities and list of description which related to the same or group of enities.
Please concatenate all these into a single, comprehensive description. Make sure to include information collected from all the description
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
If the provided descriptions contain any inappropirate information, you can skip it. Only return appropireate one. 
Make sure it is written in third person, and include the entity names so we have the full context.

##### 
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""
    return SUMMARIZE_PROMPT