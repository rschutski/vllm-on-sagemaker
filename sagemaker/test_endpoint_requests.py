import argparse

import boto3  # type: ignore
import requests
from requests_aws4auth import AWS4Auth


def get_aws_region(profile_name: str = 'default') -> str:
    session = boto3.Session(profile_name=profile_name)
    return session.region_name

def get_aws_auth(profile_name: str = 'default'):
    session = boto3.Session(profile_name=profile_name)
    credentials = session.get_credentials()
    aws_auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        session.region_name,
        "sagemaker",
        session_token=credentials.token,
    )
    return aws_auth


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    args = parser.parse_args()


    region = get_aws_region()
    aws_auth = get_aws_auth()

    endpoint = f"https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{args.endpoint}/invocations"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", 
                "content": [
                    {"type": "text", "text": "Describe this image in one sentence."},
                    {"type": "image_url", 
                     "image_url": {"url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"}}
                ]
            }
        ],
        "max_tokens": 1024
    }

    print("\n\n=========== Testing non-streaming API ===========")
    response = requests.post(endpoint, auth=aws_auth, json=payload, headers=headers)
    print(response.json())
