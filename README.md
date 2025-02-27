# SageMaker Endpoint for vLLM

You can use the [LMI](https://docs.djl.ai/docs/serving/serving/docs/lmi/index.html) to easily run vLLM on Amazon SageMaker. However, the version of vLLM supported by LMI lags several versions behind the latest community version. If you want to run the latest version, try this repo!

## Prerequisites

Make sure you have the following tools installed:
- AWS CLI (and run `aws configure`)
- Docker
- Python 3 with `boto3` installed. Optional: `langchain`, `langchain-aws` for the Langchain integration example.

## Usage

### 1. Set Environment Variables

Start by setting up some environment variables. Adjust them as needed:

```sh
export REGION='us-east-1' # change as needed
export IMAGE_NAME='vllm-on-sagemaker' # name of the image. Will create a repository with this name in ECR
export IMAGE_TAG='v0.7.3' # This is the version of the vllm-openai image to use. You may need to update
# scripts if you change it. The same tag will be given to the docker image in ECR
export SAGEMAKER_ENDPOINT_NAME='vllm-on-sagemaker' # change as needed
export SM_VLLM_MODEL="Qwen/Qwen2.5-VL-3B-Instruct" # all arguments to vLLM are passed 
# through the environment variables with `SM_VLLM` prefix.
```

The options to vLLM are passed through environmental variables. The variable name should be the option name
uppercased, where all dashes are replaced by underscores, you should also add the SM_VLLM prefix.
Check https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html to see the full list of vLLM options.

### 2. Build and Push Docker Image

Build the Docker image that will be used to run the SageMaker Endpoint serving container. After building, the image will be pushed to AWS ECR. The container implements `/ping` and `/invocations` APIs, as required by SageMaker Endpoints.

```sh
sagemaker/build_and_push_image.sh --region "$REGION" --image-name "$IMAGE_NAME" --tag "$IMAGE_TAG"
```

### 3. Get the Image URI

After the image is built and pushed, retrieve the image URI. This script ensures the image exists in ECR:

```sh
export IMAGE_URI=$(sagemaker/get_ecr_image_uri.sh --region "$REGION" --image-name "$IMAGE_NAME" --tag "$IMAGE_TAG")
echo $IMAGE_URI
```

### 4. Get ARN of the SageMaker Execution Role

Create a SageMaker execution role to allow the endpoint to run properly:

```sh
export SM_ROLE=$(sagemaker/create_sagemaker_execute_role.sh)
echo $SM_ROLE
```

or use your existing role to get the ARN:

```sh
ROLE_NAME="AmazonSageMaker-ExecutionRole-20240501T093332"
export SM_ROLE=$(aws iam get-role --role-name $ROLE_NAME --query Role.Arn --output text)
echo $SM_ROLE
```

### 5. Create the SageMaker Endpoint

Now, create the SageMaker Endpoint. Choose the appropriate and instance type. All parameters 
for vLLM are passed through the environment variables with `SM_VLLM` prefix and will 
be taken from your current environment.

```sh
python3 sagemaker/create_sagemaker_endpoint.py \
    --region "$REGION" \
    --instance-type ml.g4dn.4xlarge \
    --role-arn $SM_ROLE \
    --image-uri $IMAGE_URI \
    --endpoint-name $SAGEMAKER_ENDPOINT_NAME
```

### 6. Check the Endpoint

Go to the AWS console -> SageMaker -> Inference -> Endpoints. You should see the endpoint being created. Wait until the creation process is complete. You can also use aws cli to check the status:

```sh
aws sagemaker describe-endpoint --endpoint-name $SAGEMAKER_ENDPOINT_NAME --region $REGION
```

### 7. Send Requests to the Endpoint

Once the endpoint is created and in 'InService' status, you can start sending requests to it.

You can use the SageMaker `/invocations` API to call the endpoint; it is compatible with the OpenAI chat completion API. Check the `sagemaker/test_endpoint.py` for example requests. The example implements a request to VLM model asking it to describe an image using `boto3` for interaction with Sagemaker.

```sh
python sagemaker/test_endpoint.py --endpoint-name $SAGEMAKER_ENDPOINT_NAME --region $REGION
```

The following script shows a simple integration example with Langchain. You will need `langchain-aws` and `langchain` installed to run it.

```sh
python sagemaker/test_endpoint_langchain.py --endpoint-name $SAGEMAKER_ENDPOINT_NAME --model $SM_VLLM_MODEL
```

Pure requests implementation is also available:

```sh
python sagemaker/test_endpoint_requests.py --endpoint-name $SAGEMAKER_ENDPOINT_NAME --model $SM_VLLM_MODEL
```

Additionally, you can use `awscurl` command line utility (`curl` substitute that handles authentification properly) to send requests to the endpoint:

```sh
awscurl \
  --region "${REGION}" \
  --service sagemaker \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"model": "Qwen/Qwen2.5-VL-3B-Instruct", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": [{"type": "text", "text": "Describe this image in one sentence."}, {"type": "image_url", "image_url": {"url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"}}]}], "max_tokens": 1024}' \
  "https://runtime.sagemaker.${REGION}.amazonaws.com/endpoints/${SAGEMAKER_ENDPOINT_NAME}/invocations"
```

### 8. Delete the Endpoint

To change the model or delete the endpoint, you can use the following command. It also deletes
Sagemaker model and endpoint configuration.

```sh
python sagemaker/remove_endpoint.py --endpoint $SAGEMAKER_ENDPOINT_NAME
```