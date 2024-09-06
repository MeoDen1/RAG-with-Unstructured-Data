from prompts import graph_extractor_prompts, summarize_prompts
from LLM import LLM
import json

DEFAULT_TUPLE_DELIMITER = "<TD>"
DEFAULT_RECORD_DELIMITER = "<RD>"
DEFAULT_COMPLETION_DELIMITER = "<COMPLETE>"
DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]

class GraphExtractor:
    """
    Extract graph *entites* and *relationship* from text. For each class call, it will return
    list of entity and relationship object in the following format:\n

    "entity_name\<TD\>entity_type": description

    "source_entity\<TD\>target_entity": description

    """
    # Private
    def __init__(self, llm: LLM) -> None:
        self.__llm = llm
        self.temp: dict[str, list[str]] = {}
        # Data is stored in JSON format
        self.data = []
        self.error_count = 0
        

    def __create_graph_prompt(self, input_text: str) -> str:
        return graph_extractor_prompts.get_prompt(
            input_text, 
            DEFAULT_ENTITY_TYPES,
            DEFAULT_TUPLE_DELIMITER,
            DEFAULT_RECORD_DELIMITER,
            DEFAULT_COMPLETION_DELIMITER
        )
    
    def __create_summarize_prompt(self, entity_name: str | list[str], description_list: list[str]) -> str:
        return summarize_prompts.get_prompt(
            entity_name, description_list
        )
    
    def __entity_json_format(self, entity_name, entity_type, description):
        return {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "description": description
        }
    
    def __relationship_json_format(self, source_entity, target_entity, description):
        return {
            "source_entity": source_entity,
            "target_entity": target_entity,
            "description": description
        }
    
    def __preprocess(self, result: str):
        """
        Preprocess result and store in class total temp. 

        The *entity* is merged by name and type, while the *relationship* is merged by pair of entities
        """
        result = result.replace(DEFAULT_COMPLETION_DELIMITER, '')
        records = result.split(DEFAULT_RECORD_DELIMITER)

        for record in records:
            record = record.strip('()\n ')
            parts = record.split(DEFAULT_TUPLE_DELIMITER)

            # 0       1              2             3              4
            # obj, entity_name, entity_type, entity_description = parts
            # obj, source_entity, target_entity, description, strength = parts

            # In case the model fails to follow instruction
            if len(parts) != 4 and len(parts) != 5:
                print(f"Error encounter: {record} \n")
                self.error_count += 1
                continue

            # Make sure there are all upper
            key = f"{parts[0].upper()}{DEFAULT_TUPLE_DELIMITER}{parts[1].upper()}{DEFAULT_TUPLE_DELIMITER}{parts[2].upper()}"

            # Initialize node if not exists
            if key not in self.temp.keys():
                self.temp[key] = []

            self.temp[key].append(parts[3])


    #############################
    # Public
    def summarize(self, cooldown=1):
        """
        Merge all duplicated entities and relationships 
        """
        for item in self.temp.items():
            # Call llm to summarize

            parts = item[0].split(DEFAULT_TUPLE_DELIMITER)

            obj, key1, key2 = parts 
            # ["ENTITY", entity_name, entity_type] | 
            # ["RELATIONSHIP", source_entity, target_entity]

            entity_name = [key1, key2]
            if obj == "ENTITY":
                entity_name = key1


            # If the obj only has 1 description then skip summarization
            summarized = item[1][0]

            if len(item[1]) > 1:
                prompt = self.__create_summarize_prompt(entity_name, item[1])
                # In-case of safety setting
                try:
                    summarized = self.__llm.generate(prompt, cooldown)
                except Exception as error:
                    print(f"Error: {error} \n\n-Key: {entity_name} \n-Description: {item[1]} \n")

            if obj == "ENTITY":
                self.data.append(self.__entity_json_format(key1, key2, summarized))
            else:
                self.data.append(self.__relationship_json_format(key1, key2, summarized))


    def save_data(self, json_path: str):
        """
        Save data in JSON format
        """
        with open(json_path, 'w') as fp:
            json.dump(self.data, fp)

        print("File is successfully saved at: %s" % json_path)


    
    def extract_text(self, text: str, attempt_limit=5, store=True):
        """
        Extract *entities* and *relationship* from a text string

        Parameters
        -
        attempt_limit: maximum number of LLM extraction attempts.

        store: If true, the extracted *entities* and *relationship* will be stored in class. Merge any duplication
        """
        # Get llm extraction response 
        prompt = self.__create_graph_prompt(text)
        result = ""

        # Check if the model has finished the extraction
        attempt = 0
        while result.find(DEFAULT_COMPLETION_DELIMITER) == -1:
            if attempt > attempt_limit:
                print(f"Model failed to extract information from: \n{text}\n")
                return ""
            
            attempt += 1
            
            try:
                result = self.__llm.generate(prompt)
            except:
                continue
            

        result = result.replace(DEFAULT_COMPLETION_DELIMITER, '')

        if store:
            self.__preprocess(result)

        return result
    



if __name__ == "__main__":
    __test_result = """("entity"<TD>CENTRAL INSTITUTION<TD>ORGANIZATION<TD>The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday)
    <RD>
    ("entity"<TD>MARTIN SMITH<TD>PERSON<TD>Martin Smith is the chair of the Central Institution)
    <RD>
    ("entity"<TD>MARKET STRATEGY COMMITTEE<TD>ORGANIZATION<TD>The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply)
    <RD>
    ("relationship"<TD>MARTIN SMITH<TD>CENTRAL INSTITUTION<TD>Martin Smith is the Chair of the Central Institution and will answer questions at a press conference<TD>9)
    <COMPLETE>"""


    def test_preprocess(result: str):
        output = []
        result = result.replace(DEFAULT_COMPLETION_DELIMITER, '')
        records = result.split(DEFAULT_RECORD_DELIMITER)
        for record in records:
            record = record.strip('()\n ')
            print(record)
            

    # test_preprocess(__test_result)
    t = {1: 2, 2: 3}
    for l in t.items():
        print(l[1])