from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import Prompt, PromptCheckResult
from qdrant_client import models
import uuid
import numpy as np
from utils import Qdrant, Chunker

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
CHUNKER_MODEL = os.getenv("CHUNKER_MODEL")
CHUNKER_MAX_LEN_EMBEDDINGS = int(os.getenv("CHUNKER_MAX_LEN_EMBEDDINGS"))

app = FastAPI()

qdrant_client = None
ingester = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qdrant_client, ingester
    qdrant_client = Qdrant(QDRANT_URL, QDRANT_COLLECTION_NAME)
    ingester = Chunker(CHUNKER_MODEL, CHUNKER_MAX_LEN_EMBEDDINGS)
    yield
    del qdrant_client, ingester

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

@app.post("/upload_prompt")
async def upload_prompt(prompt: Prompt) -> models.UpdateResult:
    points = []
    for query in prompt.prompt:
        chunks = ingester.chunk_it(query)
        for _, chunk in enumerate(chunks):
            id = uuid.uuid4().hex
            points.append(models.PointStruct(
                    id=id,
                    vector=list(ingester.embeddings.embed(chunk))[0],
                    payload={"metadata":{"poisoned": prompt.poisoned}, "page_content": chunk}
                ))
    qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)


@app.get("/check_prompt", response_model=PromptCheckResult)
async def check_prompt(prompt: Prompt) -> PromptCheckResult:
    import time
    start = time.time()

    res = qdrant_client.search_batch(
        collection_name=QDRANT_COLLECTION_NAME,
        requests=[
            models.SearchRequest(
                vector=list(ingester.embeddings.embed(prompt.prompt))[0],
                limit=5,
                score_threshold=0.85,
                with_payload=True,
                filter=models.Filter(should=[models.FieldCondition(key="poisoned", match={"value": 1})])
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

    return PromptCheckResult(
        prompt=prompt,
        is_injected=1 if len(details) > 0 else 0,
        confidence_score=np.mean(details[:,2]),
        details=details,
        time="{:.2f}".format(start - time.time()) + " s"
    )

if __name__ == "__main__":
    import uvicorn, os

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", "8000"))