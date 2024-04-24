from semantic_text_splitter import TextSplitter
from tokenizers import Tokenizer
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

class Qdrant:
    def __init__(self, url, collection_name):
        self.client = QdrantClient(url=url)
        self.collection = self.client.get_collection(collection_name=collection_name)

class Chunker:
    def __init__(self, model, max_tokens):
        self.tokenizer = Tokenizer.from_pretrained(model)
        self.splitter = TextSplitter.from_huggingface_tokenizer(self.tokenizer, trim_chunks=True)
        self.embeddings = TextEmbedding(model)
        self.max_tokens = max_tokens

    def chunk_it(self, text):
        chunks = self.splitter.chunks(text, self.max_tokens)
        return chunks