from prompts import graph_extractor_prompts
from LLM import LLM

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
    def __init__(self, llm: LLM) -> None:
        self.__llm = llm
        self.data: dict[str, list[str]] = {}

    def __create_graph_prompt(self, input_text: str) -> str:
        return graph_extractor_prompts.get_prompt(
            input_text, 
            DEFAULT_ENTITY_TYPES,
            DEFAULT_TUPLE_DELIMITER,
            DEFAULT_RECORD_DELIMITER,
            DEFAULT_COMPLETION_DELIMITER
        )
    
    def __preprocess(self, result: str):
        """
        Preprocess result and store in class total data. 

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

            key = f"{parts[1]}{DEFAULT_TUPLE_DELIMITER}{parts[2]}"

            # Initialize node if not exists
            if key not in self.data.keys():
                self.data[key] = []

            self.data[key].append(parts[3])

    def __summarize(self):
        """
        Summarize description of merged node
        """
        for item in self.data.items():
            if len(item[1]) == 1:
                continue

            # Call llm to summarize


    
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
        result = self.__llm.generate(prompt)

        # Check if the model has finished the extraction
        attempt = 1
        while not result.find(DEFAULT_COMPLETION_DELIMITER):
            if attempt > attempt_limit:
                raise NameError(f"Model failed to extract information from: \n{text}\n")
            
            result = self.__llm.generate(prompt)
            attempt += 1

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