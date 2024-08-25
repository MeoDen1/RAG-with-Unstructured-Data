import pymupdf

from langchain.text_splitter import CharacterTextSplitter
import spacy
import pytextrank
from textblob import TextBlob



def get_data(file_path: str, embed_model):
    """
    Read and return list of chunks and corresponding embedding vector retrieved from `file_path`
    """
    doc = pymupdf.open(file_path)
    # Merge all page into a string
    doc_text = '\n\n'.join([doc[i].get_text() for i in range(2, len(doc))])

    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=1500,
        chunk_overlap=200,
    )

    # Split text into chunks
    chunks = text_splitter.split_text(doc_text)

    # Embed chunks
    embed_chunks = []
    count = 0
    for chunk in chunks:
        embed_chunks.append(embed_model.get_text_embedding(chunk))
        count += 1
        if count % 10 == 0:
            print("Chunk count: %d" % count)

    return [{'chunk': chunks[i], 'embedding': embed_chunks[i]} for i in range(len(chunks))]

def get_topic(text, nlp):
    doc = nlp(text)

    res = set()

    for phrase in doc._.phrases[:10]:
        res.add(phrase.text.lower())

    return res