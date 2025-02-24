import argparse
import os

import boto3  # type: ignore


def get_env_for_sagemaker(verbose: bool = True):    
    """
    Collect all environment variables prefixed with 'SM_VLLM_' and return as a new dict.
    This is used to pass environment variables to the SageMaker container.
    """
    env = {}
    for key, value in os.environ.items():
        if key.startswith('SM_VLLM'):
            env[key] = value
    if verbose:
        variables = "\n".join([f"{key}: {value}" for key, value in env.items()])
        print(f"Environment variables passed to vLLM: {variables}")
    return env


def create_sagemaker_endpoint(region, instance_type, role_arn, image_uri, endpoint_name):
    sagemaker = boto3.client('sagemaker', region_name=region)

    env = get_env_for_sagemaker()
    create_model_response = sagemaker.create_model(
        ModelName=endpoint_name + '-model',
        PrimaryContainer={
            'Image': image_uri,
            # All variables to be passed to vLLM should be prepended with 'SM_VLLM_'.
            # and have underscores in place of dashes. Argument conversion is done
            # in the `serve` entrypoint script.
            'Environment': {
                'SM_VLLM_HOST': '0.0.0.0',
                'SM_VLLM_PORT': '8080',  # required for SageMaker endpoints
                'INSTANCE_TYPE': instance_type,
                **env,
            },
        },
        ExecutionRoleArn=role_arn,
    )

    create_endpoint_config_response = sagemaker.create_endpoint_config(
        EndpointConfigName=endpoint_name + '-config',
        ProductionVariants=[
            {
                'VariantName': 'default',
                'ModelName': endpoint_name + '-model',
                'InstanceType': instance_type,
                'InitialInstanceCount': 1,
            },
        ],
    )

    create_endpoint_response = sagemaker.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_name + '-config',
    )

    print(f"Endpoint {endpoint_name} created. Check on the sagemaker console.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', default='us-east-1', help='The region to create the endpoint')
    parser.add_argument('--instance-type', required=True, help='Instance type for the SageMaker endpoint')
    parser.add_argument('--role-arn', required=True, help='The ARN of the IAM role for SageMaker to access resources')
    parser.add_argument('--image-uri', required=True, help='The URI of the Docker image in ECR')
    parser.add_argument('--endpoint-name', default='vllm-endpoint', help='The name of the endpoint to create')

    args = parser.parse_args()

    create_sagemaker_endpoint(
        region=args.region,
        instance_type=args.instance_type,
        role_arn=args.role_arn,
        image_uri=args.image_uri,
        endpoint_name=args.endpoint_name,
    )
