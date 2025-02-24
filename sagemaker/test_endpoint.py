import argparse
import base64
import json
import sys
from typing import Any

import boto3  # type: ignore
import requests
from botocore.eventstream import EventStream  # type: ignore
from botocore.response import StreamingBody  # type: ignore


def append_chunk_try_decode(chunk: bytes, buffer: str) -> tuple[dict[str, Any], str]:
    data_str = chunk.decode('utf-8')
    data = {}
    if data_str.startswith("data: "):
        data_str = data_str[len("data: "):]
    try:
        buffer += data_str
        data = json.loads(buffer.strip())
    except json.JSONDecodeError:
        pass
    else:
        buffer = ''
    return data, buffer

def process_response(response: StreamingBody | EventStream):
    """
    Process a response from SageMaker and print the
    messages sent by the model.
    """
    buffer = ''
    for chunk in response:
        if not chunk:
            continue
        elif isinstance(chunk, dict):
            chunk = chunk["PayloadPart"]["Bytes"]
        
        data, buffer = append_chunk_try_decode(chunk, buffer)

        if data:
            for choice in data['choices']:
                if 'message' in choice:
                    print(choice['message']['content'])
                else:
                    if 'content' in choice['delta']:
                        print(choice['delta']['content'], end="")
                        sys.stdout.flush()
    print('')

parser = argparse.ArgumentParser(description='Send a request to the SageMaker endpoint for inference.')
parser.add_argument('--region', type=str, default='us-east-1', help='The region of the SageMaker endpoint')
parser.add_argument('--endpoint-name', type=str, required=True, help='The SageMaker endpoint')
args = parser.parse_args()

# Create SageMaker runtime client
client = boto3.client("runtime.sagemaker", region_name=args.region)
url = "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
image_content = requests.get(url, timeout=30).content
encoded_image = base64.b64encode(image_content).decode('utf-8')

payload = {
    # NOTE: The 'model' parameter is mandated by OpenAI API interface,
    # but it doesn't mean we can choose the model on the fly, the model is set
    # when creating the Sagemaker Endpoiont.
    "model": "Qwen/Qwen2.5-VL-3B-Instruct",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
		{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in one sentence."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        # can pass image urls directly, but we won't do it to actually check the image content
                        "url": f"data:image/jpeg;base64,{encoded_image}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 1024
}

# Demo: Non-streaming mode
#
# parameters are compatible with OpenAI API format: 
# https://platform.openai.com/docs/api-reference/introduction
# with extra ones supported by vLLM, see vLLM Docs.
#
# NOTE: The streaming behavior is actually controlled by the 'stream=True' parameter
# inside the vLLM, but since you use invoke_endpoint,
# even if you pass 'stream=True', you still won't get the real streaming response.

print("\n\n=========== Testing non-streaming API ===========")
sys.stdout.flush()
response = client.invoke_endpoint(
    EndpointName=args.endpoint_name,
    Body=json.dumps(payload),
    ContentType="application/json",
)
process_response(response['Body'])

# Demo: streaming mode
#
# parameters are compatible with OpenAI API format: 
# https://platform.openai.com/docs/api-reference/introduction
# with extra ones supported by vLLM, see vLLM Docs.
# 
# NOTE: The streaming behavior is actually controlled by the 'stream=True' parameter
# inside the vLLM, but if you use invoke_endpoint, instead of invoke_endpoint_with_response_stream,
# even if you pass 'stream=True', you still won't get the real streaming response.
spayload = payload.copy()
spayload["stream"] = True # stream must be True when using invoke_endpoint_with_response_stream"

print("\n\n=========== Testing streaming API ===========")
sys.stdout.flush()
stream_response = client.invoke_endpoint_with_response_stream(
    EndpointName=args.endpoint_name,
    Body=json.dumps(spayload),
    ContentType="application/json",
)
process_response(stream_response['Body'])