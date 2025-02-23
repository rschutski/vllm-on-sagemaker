import os
import sys

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

instance_to_gpus = {
    "ml.g5.4xlarge": 1,
    "ml.g6.4xlarge": 1,
    "ml.g5.12xlarge": 4,
    "ml.g6.12xlarge": 4,
    "ml.g5.48xlarge": 8,
    "ml.g6.48xlarge": 8,
    "ml.p4d.24xlarge": 8,
    "ml.p4de.24xlarge": 8,
    "ml.p5.48xlarge": 8,
    "ml.g4dn.xlarge": 1,
    "ml.g4dn.2xlarge": 1,
    "ml.g4dn.4xlarge": 1,
    "ml.g4dn.12xlarge": 4,
    "ml.p3.2xlarge": 1,
    "ml.p3.8xlarge": 4,
    "ml.p3.16xlarge": 8,
    "ml.p3dn.24xlarge": 8,
}

def get_num_gpus(instance_type):
    try:
        return instance_to_gpus[instance_type]
    except KeyError:
        raise ValueError(f"Instance type {instance_type} not found in the dictionary")

def create_chat_completion_stub(request, payload):
    # Stub function to replace vllm call
    return {"message": "This is a stub response"}

app = FastAPI()

@app.get("/ping")
def ping():
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)

@app.post("/invocations")
async def invocations(request: Request):
    try:
        payload = await request.json()
        # Simulate request validation
        if "message" not in payload:
            raise ValidationError("Invalid request format")
    except ValidationError as e:
        return JSONResponse(content={"error": "Invalid request format", "details": str(e)}, status_code=400)

    response = create_chat_completion_stub(request, payload)
    return JSONResponse(content=response)

def start_api_server():
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    instance_type = os.getenv('INSTANCE_TYPE')
    if instance_type is None:
        sys.exit("INSTANCE_TYPE must be provided")

    num_gpus = get_num_gpus(instance_type)
    print(f"Starting server with {num_gpus} GPUs")

    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_api_server()
