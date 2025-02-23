#!/bin/bash

# Default values
default_image_name="sagem-mlchem-vllm-endpoints"
default_aws_region="us-east-1"
default_tag="latest"

# Function to display usage
usage() {
    echo "Usage: $0 [options]
Options:
    --image-name    The image name (default: $default_image_name)
    --region        The AWS region (default: $default_aws_region)
    --tag           The image tag (default: $default_tag)"
    exit 1
}

# Initialize variables with default values
image_name=$default_image_name
region=$default_aws_region
tag=$default_tag

# Set options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --image-name) image_name="$2"; shift ;;
        --region) region="$2"; shift ;;
        --tag) tag="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Determine domain based on region
if [ "$region" = "cn-north-1" ] || [ "$region" = "cn-northwest-1" ]; then
    domain="amazonaws.com.cn"
else
    domain="amazonaws.com"
fi

# Retrieve AWS Account ID
aws_account=$(aws sts get-caller-identity --query Account --output text)

# Get the latest image URI
img_uri=$(aws ecr describe-images --repository-name $image_name \
    --region $region \
    --query "sort_by(imageDetails[?imageTags != null] | [?contains(imageTags, \`${tag}\`)], &imagePushedAt)[-1].imageTags[0]" \
    --output text |\
awk -v aws_account=$aws_account \
    -v aws_region=$region \
    -v img_name=$image_name \
    -v domain=$domain '{print aws_account ".dkr.ecr." aws_region "." domain "/" img_name ":" $1}')

echo $img_uri
