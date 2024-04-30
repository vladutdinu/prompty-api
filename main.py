import uuid
import numpy as np
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import UsageCounter, Prompt, PromptCheckResult
from qdrant_client import models
from utils import Qdrant, Chunker
from middleware import FileCountSuccessMiddleware

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
CHUNKER_TOKENIZER = os.getenv("CHUNKER_TOKENIZER")
CHUNKER_MODEL = os.getenv("CHUNKER_MODEL")
CHUNKER_MAX_LEN_EMBEDDINGS = int(os.getenv("CHUNKER_MAX_LEN_EMBEDDINGS"))
SENSITIVITY = float(os.getenv("SENSITIVITY"))

client = None
ingester = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, ingester, counter
    client = Qdrant(QDRANT_URL, QDRANT_COLLECTION_NAME)
    ingester = Chunker(CHUNKER_TOKENIZER, CHUNKER_MODEL, CHUNKER_MAX_LEN_EMBEDDINGS)
    yield
    del client, ingester

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
                limit=5,
                # score_threshold=SENSITIVITY,
                with_payload=True,
                filter=models.Filter(should=[models.FieldCondition(key="metadata.poisoned", match={"value": 1})])
            ),
        ]
    )[0]

    details = [
        {
            'id': item.id,
            'poisoned': item.payload["metadata"]["poisoned"],
            'score': item.score
        }
        for item in res
    ]
    confidence = round(np.mean([entry["score"] for entry in details])*100, 2) if len(details) > 0 else None
    return PromptCheckResult(
        prompt=prompt.prompt,
        is_injected=None if confidence is None else 1 if confidence >= 65.0 else 0.5 if confidence >= 35.0 and confidence < 65.0 else 0,
        confidence_score=confidence,
        details=details,
        time="{:.2f}".format(time.time() - start) + " s"
    )

if __name__ == "__main__":
    import uvicorn, os

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", "8000"))