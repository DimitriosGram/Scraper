# 🛠️🚀 Serverless Scraper Pipeline — AWS Infrastructure Project

This project is a **cloud-native, serverless web scraping pipeline** built using **AWS services**, **Serverless Framework**, **Docker**, and **GitHub Actions**. It contains two separate scraping flows:

- **Personal Product Scraper**
- **Business Product Scraper**

Each is independently deployed and managed using AWS Lambda, EventBridge, and S3, with automated deployment pipelines and modular infrastructure as code (IaC) setup.

## 🌐 Tech Stack
- AWS Lambda (container-based)
- EventBridge (scheduled invocations)
- S3 (data output)
- Secrets Manager (secure auth)
- IAM Roles (least privilege)
- Serverless Framework (IaC for Personal pipeline)
- GitHub Actions (CI/CD)
- Docker (containerization)
- Python (scraper logic & AWS SDK)

## ✅ Key Features
⚙️ Modular deployment for Personal and Business scrapers

🐳 Dockerized Lambda functions for full runtime control

🔁 Fully automated CI/CD for Business and Personal pipeline

🔐 Secure secret management using AWS services

📦 Structured IaC using Serverless Framework

📤 Data stored in S3 for external analysis or backup

---

## 📌 Project Goals

- Design a scalable, serverless architecture for periodic scraping jobs
- Automate deployment and infrastructure management using GitHub Actions and the Serverless Framework
- Separate pipelines for different data categories (Personal & Business)
- Enable modular, secure, and auditable infrastructure deployment

---

## 🧱 Infrastructure Overview

The architecture is split into two pipelines: **Personal** and **Business**. Both share the same foundational design:

### 🔹 AWS Lambda Functions
- Two separate Lambdas:
  - `Personal/main.py` – Handles scraping for personal products
  - `Business/main.py` – Handles scraping for business products
- Code is written in Python and executed on scheduled intervals

### 🔹 Amazon EventBridge (Scheduler)
- Triggers the Lambda functions using scheduled **cron expressions**
- Fully managed and decoupled scheduling mechanism

### 🔹 Amazon S3
- Output from each scraper is stored in separate S3 buckets
- Supports downstream processing, archival, or analytics

### 🔹 IAM Roles and Policies
- Each Lambda is granted **least-privilege IAM roles**
- Ensures scoped access only to S3 and necessary AWS services

---

## 🧩 Serverless Framework – Infrastructure as Code

The **Serverless Framework** is used to define and deploy the infrastructure for the `Personal` pipeline.

### Key Features:
- `serverless.yaml` defines:
  - Lambda function configuration (runtime, handler, memory, timeout)
  - EventBridge trigger rules
  - IAM permissions
  - S3 output configurations
- Supports fast iteration, consistent deployments, and rollback capabilities

---

## 🔁 CI/CD – GitHub Actions Workflow

A custom **GitHub Actions** workflow automates the deployment of the Business scraper:

### File: `workflows/deployBusiness.yml`

- **Triggers**:
  - Manual (`workflow_dispatch`)
  - On push to main or target branch

- **Steps**:
  1. Set up Node and Python environments
  2. Install dependencies (Serverless, Python packages)
  3. Lint and validate code
  4. Deploy to AWS using `serverless deploy`

This ensures continuous integration and deployment without manual intervention.

---

## 🐳 Docker Support

Both `Business` and `Personal` scrapers supports Docker-based packaging for local testing or alternate deployment strategies.

### File: `Personal or Business/dockerfile`

- Python runtime environment
- Installs all dependencies via `requirements.txt`
- Sets up the scraper as an executable Lambda-like container

### Script: `script/build_and_push.sh`

- Builds the Docker image
- Tags and pushes the image to a container registry (e.g., Amazon ECR)
- Assigns docker image to any choosen Lambda function

---
  
## 🚀 Deployment Instructions

🔧 Prerequisites
Before deploying either pipeline, make sure you have:

- Python 3.11+ (for scraper logic)
- Docker (for building containerized Lambdas)
- AWS CLI (for deployment/debugging)
- **Node.js + npm** (for Serverless Framework CLI only)
  ```bash
  npm install -g serverless

---

## 🤖 Build & Deployment Automation

To streamline deployment and reduce manual work, I created a custom shell script in the [`/script`](./script) directory to fully automate the Docker build-and-deploy process:

- Builds the Docker image
- Logs into ECR
- Pushes the image to the correct repository
- Updates the Lambda function with the new image

This was a manual, multi-step task — so I took the initiative to automate it, saving time and reducing room for human error. It’s now fully integrated into the GitHub Actions pipeline.

> Script: [`build_and_push.sh`](./script/build_and_push.sh)

---

## 📦 Environment Variables
These are accessed via .env or injected in the AWS Lambda environment. 

Required variables:

- AWS_BUCKET	Name of the target S3 bucket
- MF_username	Username for MoneyFacts (very important)
- Secrets (AWS)	Stored in Secrets Manager, e.g. MoneyFactsLogin

🔐 Secrets like passwords should not be hardcoded. They're retrieved securely from AWS Secrets Manager using boto3.

---

## 📁 Deploying via CI/CD (Business or Personal Scraper)
The Business or Personal scraper is deployed automatically via GitHub Actions:

- Triggered on pushes to ```dev``` or ```main``` branches
- Or manually via workflow dispatch

CI/CD handles:

- Testing with pytest
- Docker build/tag/push to ECR
- Lambda update with new container image

To run tests locally:

```pytest tests/unit/Business/```
