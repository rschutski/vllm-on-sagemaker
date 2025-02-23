import argparse
import sys

import boto3


def remove_sagemaker_endpoint(endpoint_name):
    client = boto3.client('sagemaker')
    try:
        response = client.delete_endpoint(EndpointName=endpoint_name)
        print(f"Endpoint {endpoint_name} deleted successfully.")
    except client.exceptions.ClientError as e:
        print(f"Error deleting endpoint {endpoint_name}: {e}")

def remove_sagemaker_model(model_name):
    client = boto3.client('sagemaker')
    try:
        response = client.delete_model(ModelName=model_name)
        print(f"Model {model_name} deleted successfully.")
    except client.exceptions.ClientError as e:
        print(f"Error deleting model {model_name}: {e}")

def remove_sagemaker_endpoint_config(config_name):
    client = boto3.client('sagemaker')
    try:
        response = client.delete_endpoint_config(EndpointConfigName=config_name)
        print(f"Endpoint configuration {config_name} deleted successfully.")
    except client.exceptions.ClientError as e:
        print(f"Error deleting endpoint configuration {config_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove SageMaker endpoint, model, or endpoint configuration.")
    parser.add_argument('--endpoint-name', type=str, help="Name of the SageMaker endpoint to remove.")
    args = parser.parse_args()
    if args.endpoint_name:
        remove_sagemaker_endpoint(args.endpoint_name)
        remove_sagemaker_model(args.endpoint_name + "-model")
        remove_sagemaker_endpoint_config(args.endpoint_name + "-config")

    if not args.endpoint_name:
        print("Please provide the name of the SageMaker endpoint to remove.")
        sys.exit(1)