#!/bin/bash
# Enable exit-on-error mode
set -e

# Function to be executed on error or script termination
error_capture() {
echo "ERROR: Something went wrong... but what went wrong is the question"
echo "Dimi, do a bit of research to see how you can capture the error message and print it here" 
exit 0
}

# Trap the ERR signal and call the cleanup_function
trap 'error_capture' ERR

account_id=$1
region=$2
repo_name=$3
image_tag=$4
lambda_function_name=$5
sso_profile=$6

echo "AWS Account ID: ${account_id}"
echo "AWS Account Region: ${region}"
echo "AWS ECR Repo: ${repo_name}"
echo "Image tag is: ${image_tag}"
echo "SSO Profile is: ${sso_profile}"

echo "Logging in to AWS ECR"
aws ecr get-login-password --region ${region} --profile ${sso_profile}| docker login --password-stdin --username AWS "${account_id}.dkr.ecr.${region}.amazonaws.com"
echo "Checking if ${repo_name} exists. If it doesn't exist, this process will exit gracefully (no images built or pushed) and the workflow will continue."
aws ecr describe-repositories --repository-name ${repo_name} --profile ${sso_profile}
echo "ECR Repository ${repo_name} found. Building image..."


docker build -t "${account_id}.dkr.ecr.${region}.amazonaws.com/${repo_name}:${image_tag}" .
echo "Pushing image..."
docker push "${account_id}.dkr.ecr.${region}.amazonaws.com/${repo_name}:${image_tag}"
echo "Docker image uploaded" 

echo "Assign new image to lambda function: ${lambda_function_name}" 
aws lambda update-function-code --function-name ${lambda_function_name} --image-uri "${account_id}.dkr.ecr.${region}.amazonaws.com/${repo_name}:${image_tag}" --profile ${sso_profile}
echo "New image assigned to lambda function"