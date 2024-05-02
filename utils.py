from semantic_text_splitter import TextSplitter
from tokenizers import Tokenizer
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from math import sqrt, pow, exp

POSSIBLE_INJECTION_SEQUENCES=[
        "Ignore",
        "Disregard",
        "Skip",
        "Forget",
        "Neglect",
        "Overlook",
        "Omit",
        "Bypass",
        "Pay no attention to",
        "Do not follow",
        "Do not obey", 
        "and start over",
        "and start anew",
        "and begin afresh",
        "and start from scratch",
]

def squared_sum(x):
  """ return 3 rounded square rooted value """
 
  return round(sqrt(sum([a*a for a in x])),3)
 
def euclidean_distance(x,y):
  """ return euclidean distance between two lists """
 
  return sqrt(sum(pow(a-b,2) for a, b in zip(x, y)))

def distance_to_similarity(distance):
  return 1/exp(distance)

def cos_similarity(x,y):
  """ return cosine similarity between two lists """
 
  numerator = sum(a*b for a,b in zip(x,y))
  denominator = squared_sum(x)*squared_sum(y)
  return round(numerator/float(denominator),3)

class Qdrant:
    def __init__(self, url, collection_name):
        self.client = QdrantClient(url=url)
        self.collection = self.client.get_collection(collection_name=collection_name)

class Chunker:
    def __init__(self, tokenizer, model, max_tokens):
        try:
            self.tokenizer = Tokenizer.from_file(tokenizer)
        except:
            self.tokenizer = Tokenizer.from_pretrained(tokenizer)
        self.splitter = TextSplitter.from_huggingface_tokenizer(self.tokenizer, trim_chunks=True)
        self.embeddings = TextEmbedding(model, cache_dir="/models")
        self.max_tokens = max_tokens

    def chunk_it(self, text):
        chunks = self.splitter.chunks(text, self.max_tokens)
        return chunks
    