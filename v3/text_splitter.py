import tiktoken

"""Re-implement character text chunking strategy"""

class TextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int, encoding_name: str = "cl100k_base"):
        # chunk_size can not equal to chunk_overlap
        assert chunk_size != chunk_overlap

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def split_text(self, text: str):
        # Using gpt embedding model and tiktoken tokenizer
        output: list[str] = []

        # Tokenize text into list of token ids
        tokens = self.tokenizer.encode(text)

        # Given n = chunk_overlap. The last n tokens of previous chunk will
        # be carried over to the beginning of the next chunk

        start_tkn = 0
        
        while start_tkn < len(tokens):
            end_tkn = min(len(tokens), start_tkn + self.chunk_size)
            output.append(self.tokenizer.decode(tokens[start_tkn:end_tkn]))
            start_tkn = start_tkn + self.chunk_size - self.chunk_overlap

        return output

if __name__ == "__main__":
    text_splitter = TextSplitter(2, 1)
    print(text_splitter.split_text("hello word"))
    t0 = [1, 2]
    print(t0[0: 1000])
