import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class FileCountSuccessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, filepath, path):
        super().__init__(app)
        self.filepath = filepath
        self.path = path
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path == self.path and 200 <= response.status_code < 300:
            with open(self.filepath, "r+") as file:
                data = json.load(file)
                data["success_count"] += 1
                file.seek(0)
                json.dump(data, file)
        return response

