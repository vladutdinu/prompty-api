import uuid
import numpy as np
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import CleanPrompt, PromptAccuracy, UsageCounter, Prompt, PromptCheckResult
from qdrant_client import models
from utils import POSSIBLE_INJECTION_SEQUENCES, Qdrant, Chunker, cos_similarity, distance_to_similarity, euclidean_distance
from middleware import FileCountSuccessMiddleware
from itertools import chain

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
CHUNKER_TOKENIZER = os.getenv("CHUNKER_TOKENIZER")
CHUNKER_MODEL = os.getenv("CHUNKER_MODEL")
CHUNKER_MAX_LEN_EMBEDDINGS = int(os.getenv("CHUNKER_MAX_LEN_EMBEDDINGS"))
SENSITIVITY = float(os.getenv("SENSITIVITY"))
LIMIT = int(os.getenv("LIMIT"))
CONFIDENCE_SENSITIVITY = float(os.getenv("CONFIDENCE_SENSITIVITY"))

client = None
ingester = None
possible_injection_sequences = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, ingester, possible_injection_sequences
    client = Qdrant(QDRANT_URL, QDRANT_COLLECTION_NAME)
    ingester = Chunker(CHUNKER_TOKENIZER, CHUNKER_MODEL, CHUNKER_MAX_LEN_EMBEDDINGS)
    possible_injection_sequences = list(set(chain(*[encoder.ids for encoder in ingester.tokenizer.encode_batch(POSSIBLE_INJECTION_SEQUENCES, add_special_tokens=False)])))
    yield
    del client, ingester, possible_injection_sequences

app = FastAPI(lifespan=lifespan)

try:
    with open(os.getenv("COUNT_FILE"), "r") as file:
        success_counter = json.load(file)
except FileNotFoundError:
    success_counter = {"success_count": 0}
    with open(os.getenv("COUNT_FILE"), "w") as file:
        json.dump(success_counter, file)

app.add_middleware(FileCountSuccessMiddleware, filepath=os.getenv("COUNT_FILE"), path="/check_prompt")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_counter")
async def get_counter() -> UsageCounter:

    """How many times the check_prompt endpoint has been user
    Raises:
        HTTPException: Counter file not found

    Returns:
        JSON: {
            "counter": usage_number
        }
    """

    success_counter = None
    try:
        with open(os.getenv("COUNT_FILE"), "r") as file:
            success_counter = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Counter file not found")
    if success_counter is not None:
        return UsageCounter(count=success_counter["success_count"])

@app.post("/upload_prompt")
async def upload_prompt(prompt: Prompt) -> models.UpdateResult:
    
    """Upload a prompt
    Args:
        prompt (str): The prompt text, it has to be a string with more than 3 words
        poisoned (float): 0 if its not injected, 0.5 if its probably injected, 1 if its injected

    Raises:
        HTTPException: Collection not found

    Returns:
        JSON: {
            "operation_id": the operation id,
            "status": completed/acknowledged
        }
    """

    res = client.client.scroll(
        collection_name=QDRANT_COLLECTION_NAME,
        scroll_filter=models.Filter(must=[models.FieldCondition(key="page_content", match={"value": prompt.prompt})])
    )[0]

    if len(res) != 0:
        raise HTTPException(status_code=409, detail="Prompt has been already registered.")

    points = []
    chunks = ingester.chunk_it(prompt.prompt)
    for _, chunk in enumerate(chunks):
        id = uuid.uuid4().hex
        points.append(models.PointStruct(
                id=id,
                vector=list(ingester.embeddings.embed(chunk))[0],
                payload={"metadata":{"poisoned": prompt.poisoned}, "page_content": chunk}
            ))
    return client.client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)


@app.post("/check_prompt", response_model=PromptCheckResult)
async def check_prompt(prompt: Prompt) -> PromptCheckResult:
    """Check a prompt
    Args:
        prompt (str): The prompt text, it has to be a string with more than 3 words

    Raises:
        HTTPException: Index out of bounds

    Returns:
        JSON: {
            "prompt": the verified prompt,
            "poisoned": 0 if its not injected, 0.5 if its probably injected, 1 if its injected,
            "confidence_score": percentage between 0% and 100%,
            "time": the amount of time needed to process the request
        }
    """
    import time
    start = time.time()

    res = client.client.search_batch(
        collection_name=QDRANT_COLLECTION_NAME,
        requests=[
            models.SearchRequest(
                vector=list(ingester.embeddings.embed(prompt.prompt))[0],
                limit=LIMIT,
                #score_threshold=SENSITIVITY,
                with_payload=True,
                #filter=models.Filter(should=[models.FieldCondition(key="metadata.poisoned", match={"value": 1})])
            ),
        ]
    )[0]

    dtypes = [('id', 'U10'), ('poisoned', np.bool_), ('score', np.float64)]
    details = np.array([(item.id, item.payload["metadata"]["poisoned"], item.score) for item in res], dtype=dtypes)
  
    total_score = sum(item[2] for item in details)
    normalized_scores = [item[2] / total_score * len(details) for item in details]

    # Calculate weighted sums using normalized scores
    poisoned_weight = sum(normalized_scores[i] for i, item in enumerate(details) if item[1])
    not_poisoned_weight = sum(normalized_scores[i] for i, item in enumerate(details) if not item[1])

    # Add counts to the weights
    poisoned_count = sum(1 for item in details if item[1])
    not_poisoned_count = len(details) - poisoned_count

    total_poisoned_weight = poisoned_weight + poisoned_count
    total_not_poisoned_weight = not_poisoned_weight + not_poisoned_count

    # Total weights
    total_weights = total_poisoned_weight + total_not_poisoned_weight

    # Calculating combined probabilities
    combined_probability_poisoned = total_poisoned_weight / total_weights
    combined_probability_not_poisoned = total_not_poisoned_weight / total_weights

    return PromptCheckResult(
        prompt=prompt.prompt,
        is_injected=1 if combined_probability_poisoned >= CONFIDENCE_SENSITIVITY else 0,
        injection_confidence_score=round(combined_probability_poisoned*100, 2) if combined_probability_poisoned >= CONFIDENCE_SENSITIVITY else round(combined_probability_not_poisoned*100, 2),
        time="{:.2f}".format(time.time() - start) + " s"
    )

@app.post("/clean_prompt", response_model=CleanPrompt)
async def clean_prompt(prompt: Prompt) -> CleanPrompt:
    """Clean the prompt
    Args:
        prompt (str): The prompt text, it has to be a string with more than 3 words

    Raises:
        HTTPException: Index out of bounds

    Returns:
        JSON: {
            "prompt": the infected prompt,
            "cleaned_prompt": the cleaned prompt
        }
    """
    initial_prompt = ingester.tokenizer.encode(prompt.prompt, add_special_tokens=False).ids
    cleaned_initial_prompt =  [id for id in initial_prompt if id not in possible_injection_sequences]
    cleaned_prompt = " ".join(ingester.tokenizer.id_to_token(tkn) for tkn in cleaned_initial_prompt)
    return CleanPrompt(
        prompt=prompt.prompt,
        cleaned_prompt=cleaned_prompt
    )

@app.post("/check_accuracy")
async def check_accuracy(prompt: PromptAccuracy):
    """Check a prompt
    Args:
        system_prompt (str): The system prompt from your LLM
        user_prompt (str): The user prompt
        answer (str): The answer your LLM gives
        calculation_method (str): euclidean or cosine 
    Returns:
        JSON: {
            "relevance": percentage of the relevance of the answer in regards with the system prompt
        }
    """
    if prompt.calculation_method == 'euclidean':
        return {
            "relevance": distance_to_similarity(euclidean_distance(list(ingester.embeddings.embed(prompt.system_prompt + prompt.user_prompt))[0], 
                                                                   list(ingester.embeddings.embed(prompt.answer))[0]))
        }
    elif prompt.calculation_method == 'cosine':
        return {
            "relevance": cos_similarity(list(ingester.embeddings.embed(prompt.system_prompt + prompt.user_prompt))[0], 
                                        list(ingester.embeddings.embed(prompt.answer))[0])
        }

if __name__ == "__main__":
    import uvicorn, os

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", "8000"))