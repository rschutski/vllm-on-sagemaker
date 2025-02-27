# %%
import argparse
import json

import boto3  # type: ignore
from botocore.response import StreamingBody  # type: ignore
from langchain_aws.llms.sagemaker_endpoint import LLMContentHandler, SagemakerEndpoint
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.messages.utils import convert_to_openai_messages


# %%
def get_aws_region(profile_name: str = 'default') -> str:
    session = boto3.Session(profile_name=profile_name)
    return session.region_name

# %%
class OpenAIMessagesHandler(LLMContentHandler):
    content_type: str = "application/json"
    accepts: str = "application/json"

    def transform_input(
        self, prompt: str | BaseMessage | list[BaseMessage],
        model_kwargs: dict) -> bytes:
        # Construct the payload as expected by the OpenAI-compatible API
        messages = convert_to_openai_messages(prompt)
        if not isinstance(messages, list):
            messages = [messages]
        input_data = {
            "messages": messages,
            **model_kwargs
        }
        return json.dumps(input_data).encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        # Parse the JSON response from the SageMaker endpoint
        if isinstance(output, bytes):
            decoded = output.decode("utf-8").strip("data: ")
        elif isinstance(output, StreamingBody):
            decoded = output.read().decode("utf-8")
        else:
            raise ValueError("Unexpected output type")
        try:
            response_json = json.loads(decoded)
        except json.JSONDecodeError as e:
            if (not decoded) or (decoded == "[DONE]"):
                return ""
            else:
                raise ValueError(f"Unexpected response: {decoded}") from e

        choice = response_json['choices'][0]
        if 'message' in choice:
            return choice['message']['content']
        else:
            if 'content' in choice['delta']:
                return choice['delta']['content']
        return decoded


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--region", type=str, default=get_aws_region())
    args = parser.parse_args()

    prompt = [HumanMessage(content="Hello, how are you?")]

    print("\n\n=========== Testing non-streaming API ===========")

    endpoint = SagemakerEndpoint(
        endpoint_name=args.endpoint,
        region_name=get_aws_region(),
        content_handler=OpenAIMessagesHandler(),
        model_kwargs={
            "model": args.model,
            "temperature": 0.7,
            "max_tokens": 150}
    )
    response = endpoint.invoke(prompt)
    print(response)

    print("\n\n=========== Testing streaming API ===========")

    endpoint = SagemakerEndpoint(
        endpoint_name=args.endpoint,
        region_name=get_aws_region(),
        content_handler=OpenAIMessagesHandler(),
        model_kwargs={
            "model": args.model,
            "temperature": 0.7,
            "max_tokens": 150,
            "stream": True
            },
        callbacks=[StreamingStdOutCallbackHandler()],
        streaming=True
    )
    response = endpoint.invoke(prompt)
    print(response)
