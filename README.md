# 🛠️ Serverless Scraper Pipeline — AWS Infrastructure Project

This project is a **cloud-native, serverless web scraping pipeline** built using **AWS services**, **Serverless Framework**, **Docker**, and **GitHub Actions**. It contains two separate scraping flows:

- **Personal Product Scraper**
- **Business Product Scraper**

Each is independently deployed and managed using AWS Lambda, EventBridge, and S3, with automated deployment pipelines and modular infrastructure as code (IaC) setup.

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

> The `Business` pipeline is currently deployed manually or via CI; it can be migrated to Serverless Framework easily.

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

The `Personal` scraper supports Docker-based packaging for local testing or alternate deployment strategies.

### File: `Personal/dockerfile`

- Python runtime environment
- Installs all dependencies via `requirements.txt`
- Sets up the scraper as an executable Lambda-like container

### Script: `script/build_and_push.sh`

- Builds the Docker image
- Tags and pushes the image to a container registry (e.g., Amazon ECR)
- Can be extended to support Lambda container-based deployment
