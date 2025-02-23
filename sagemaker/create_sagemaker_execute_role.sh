#!/bin/sh

# Trust policy JSON content
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

ROLE_NAME=AmazonSageMaker-ExecutionRole-20240501T093332

# Create the role and capture the role ARN
#SAGEMAKER_ROLE_ARN=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document "$TRUST_POLICY" --query 'Role.Arn' --output text)

# Get the role ARN or create it
SAGEMAKER_ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text) || \
    SAGEMAKER_ROLE_ARN=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document "$TRUST_POLICY" --query 'Role.Arn' --output text)

# Attach SageMaker full access policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# Attach S3 read-only access policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Attach ECR read-only access policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

echo "$SAGEMAKER_ROLE_ARN"