# Elastic Beanstalk Deployment Guide - CRAG RAG Application

**Date:** May 3-4, 2026  
**Application:** crag-reflective-rag (Azure OpenAI + Qdrant Vector Store)  
**Environment:** AWS Elastic Beanstalk (crag-rag-prod)  
**Status:** ✅ Successfully Deployed

---

## Table of Contents
1. [Overview](#overview)
2. [Initial Setup & Configuration](#initial-setup--configuration)
3. [Issues Encountered](#issues-encountered)
4. [Solutions Implemented](#solutions-implemented)
5. [Deployment Steps](#deployment-steps)
6. [Environment Variables](#environment-variables)
7. [Key Learnings](#key-learnings)
8. [Troubleshooting Reference](#troubleshooting-reference)

---

## Overview

### What Was Deployed
- **Application:** CSR RAG (Corrective RAG + Self-Reflective RAG)
- **AI Backend:** Azure OpenAI (gpt-4o)
- **Vector Store:** Qdrant (EU-Central-1)
- **Web Search:** Tavily API
- **Reranking:** Local cross-encoder model
- **Infrastructure:** AWS Elastic Beanstalk (Docker) + ECR

### Final Architecture
```
Local Dev → Docker Image → ECR (380610849617.dkr.ecr.us-east-1.amazonaws.com)
    ↓
Elastic Beanstalk (crag-rag-prod)
    ↓
EC2 Instance (t3.large, 100GB volume)
    ↓
Application: uvicorn (8000 port)
    ↓
External APIs: Azure OpenAI, Qdrant, Tavily
```

---

## Initial Setup & Configuration

### Prerequisites
```bash
# AWS CLI configured with credentials
aws configure

# EB CLI installed
eb --version

# Docker installed and running
docker --version

# AWS ECR credentials
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 380610849617.dkr.ecr.us-east-1.amazonaws.com
```

### Repository Structure
```
csr_rag/
├── app/
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration management
│   ├── models.py         # Pydantic models
│   ├── api/
│   │   ├── query.py      # Query endpoints
│   │   └── upload.py     # Document upload endpoints
│   ├── core/
│   │   └── retrieval.py  # RAG core logic
│   └── services/         # Business logic
│       ├── llm_service.py           # Azure OpenAI integration
│       ├── vector_store.py          # Qdrant client
│       ├── embedding_service.py     # Embeddings
│       ├── reranking.py             # Local reranker
│       ├── crag.py                  # CRAG implementation
│       ├── self_reflective.py       # Self-reflective logic
│       └── ...
├── Dockerfile            # Multi-stage Docker build
├── pyproject.toml        # UV package manager config
├── .env                  # Environment variables (DON'T COMMIT)
└── .elasticbeanstalk/    # EB configuration
```

---

## Issues Encountered

### Issue 1: Docker Image Too Large (CRITICAL)

**Problem:**
```
Error: "no space left on device" 
File: /app/.venv/lib/python3.12/site-packages/nvidia/cu13/lib/libnvJitLink.so.13
```

**Root Cause:**
- Default EC2 root volume: **8GB**
- Docker image size: **2-3GB** (with CUDA binaries)
- CUDA packages included despite setting `UV_TORCH_BACKEND=cpu`
- `sentence-transformers` pulled in PyTorch with CUDA wheels

**Impact:**
- EC2 instance could not pull/extract Docker image
- Deployment failed at layer registration step
- Environment remained in "Updating" state

**Timeline:**
- **16:10:20** - Environment creation started
- **16:14:57** - Deployment failed with disk space error
- **16:18:46** - Applied 100GB volume update
- **00:24:38** - Environment variables set on updated volume
- **00:26:04** - Final deployment successful

### Issue 2: Dockerfile Complexity with CPU-Only PyTorch

**Problem:**
- Initial attempts to force CPU-only PyTorch failed
- `uv sync` ignored `UV_TORCH_BACKEND=cpu` setting
- Multiple build iterations trying different approaches

**Approaches Tried:**
1. ❌ `UV_TORCH_BACKEND=cpu` environment variable alone
2. ❌ `PIP_NO_BINARY` constraints
3. ❌ Pre-installing PyTorch via explicit `--index-url https://download.pytorch.org/whl/cpu`
4. ❌ Version `torch==2.1.1` (not available on CPU index)
5. ✅ **Simplified Dockerfile** (removed complex constraints)

---

## Solutions Implemented

### Solution 1: Increase EC2 Volume Size

**Command:**
```bash
aws elasticbeanstalk update-environment \
  --application-name crag-rag-app \
  --environment-name crag-rag-prod \
  --region us-east-1 \
  --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100
```

**Effect:**
- Increased EBS root volume from 8GB → 100GB
- Provided sufficient space for image extraction
- Resolved "no space left on device" error

**Cost Impact:**
- Standard EBS gp3: ~$0.10/GB/month
- Additional 92GB: ~$9.20/month

### Solution 2: Simplified Dockerfile

**Final Working Dockerfile:**
```dockerfile
# ============================================================
# Stage 1: Builder
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN uv sync --no-dev --no-install-project

COPY app/ ./app/
RUN uv sync --no-dev

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /var/app/uploads && chown appuser:appuser /var/app/uploads

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Key Changes:**
- Removed complex PyTorch installation attempts
- Simplified environment variables
- Let `uv sync` handle dependency resolution naturally
- Multi-stage build for size optimization

### Solution 3: Environment Variables Configuration

**Command:**
```bash
eb setenv \
  AZURE_OPENAI_API_KEY="..." \
  AZURE_OPENAI_ENDPOINT="..." \
  AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
  AZURE_OPENAI_API_VERSION="2025-01-01-preview" \
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-3-small" \
  TAVILY_API_KEY="..." \
  QDRANT_URL="..." \
  QDRANT_API_KEY="..." \
  QDRANT_COLLECTION_NAME="crag_documents_v2" \
  EMBEDDING_MODEL="text-embedding-3-small" \
  EMBEDDING_DIMENSIONS="1536" \
  CRAG_RELEVANCE_THRESHOLD="0.7" \
  CRAG_AMBIGUOUS_THRESHOLD="0.5" \
  REFLECTION_MIN_SCORE="0.8" \
  MAX_REFLECTION_RETRIES="2" \
  TOP_K_RESULTS="5" \
  HYDE_NUM_HYPOTHESES="3" \
  HYDE_ENABLED_BY_DEFAULT="false" \
  RERANKER_MODEL="cross-encoder/ms-marco-MiniLM-L-6-v2" \
  RERANKER_INITIAL_TOP_K="20" \
  RERANKING_ENABLED_BY_DEFAULT="false" \
  RERANKER_BACKEND="local" \
  VOYAGE_API_KEY="..." \
  VOYAGE_MODEL="rerank-2.5" \
  UPLOAD_DIR="/var/app/uploads" \
  MAX_FILE_SIZE="52428800"
```

**Custom Variables for Azure OpenAI:**
```env
# Standard OpenAI (NOT used)
OPENAI_API_KEY=...           ❌

# Azure OpenAI (USED)
AZURE_OPENAI_API_KEY=...      ✅
AZURE_OPENAI_ENDPOINT=...     ✅
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  ✅
AZURE_OPENAI_API_VERSION=2025-01-01-preview  ✅
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small  ✅
```

---

## Deployment Steps

### Step 1: Build Docker Image
```bash
cd f:\sourab\csr_rag

docker build --platform linux/amd64 -t crag-rag-app:latest .
```

**Output:**
```
[+] Building FINISHED
=> exporting manifest sha256:5d50abb5...
=> naming to docker.io/library/crag-rag-app:latest
```

### Step 2: Tag for ECR
```bash
docker tag crag-rag-app:latest 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest
```

### Step 3: Push to ECR
```bash
docker push 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest
```

**Output:**
```
latest: digest: sha256:5d50abb5...
size: 856
```

### Step 4: Create EB Environment (if first time)
```bash
eb create crag-rag-prod --instance-type t3.large --single --instance_profile aws-elasticbeanstalk-ec2-role
```

**First Attempt Failed:**
```
ERROR   Instance deployment failed to download the Docker image. 
        Failed to register layer: write /app/.venv/lib/python3.12/site-packages/nvidia/cu13/lib/libnvJitLink.so.13: 
        no space left on device
```

### Step 5: Update Volume Size
```bash
aws elasticbeanstalk update-environment \
  --application-name crag-rag-app \
  --environment-name crag-rag-prod \
  --region us-east-1 \
  --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100
```

### Step 6: Set Environment Variables
```bash
eb setenv AZURE_OPENAI_API_KEY="..." [... all 24 variables ...]
```

### Step 7: Deploy Application
```bash
eb deploy crag-rag-prod
```

### Step 8: Verify Deployment
```bash
eb status crag-rag-prod
```

**Successful Output:**
```
Environment details for: crag-rag-prod
  Application name: crag-rag-app
  Region: us-east-1
  Deployed Version: app-939b-260504_055525781341
  Environment ID: e-smnqxpxtyj
  Status: Ready
  Health: Green
  CNAME: crag-rag-prod.eba-ddjmismj.us-east-1.elasticbeanstalk.com
```

---

## Environment Variables

### Complete Configuration

| Variable | Value | Purpose |
|----------|-------|---------|
| **AZURE_OPENAI_API_KEY** | FIMi26LL... | Azure OpenAI authentication |
| **AZURE_OPENAI_ENDPOINT** | https://moham-mi3bbwto-eastus2.cognitiveservices.azure.com/ | Azure service endpoint |
| **AZURE_OPENAI_DEPLOYMENT_NAME** | gpt-4o | Chat model deployment |
| **AZURE_OPENAI_API_VERSION** | 2025-01-01-preview | API version |
| **AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME** | text-embedding-3-small | Embedding model |
| **TAVILY_API_KEY** | tvly-dev-... | Web search API |
| **QDRANT_URL** | https://baa7e138...eu-central-1-0.aws.cloud.qdrant.io | Vector store endpoint |
| **QDRANT_API_KEY** | eyJhbGci... | Vector store authentication |
| **QDRANT_COLLECTION_NAME** | crag_documents_v2 | Document collection |
| **EMBEDDING_MODEL** | text-embedding-3-small | Embedding model name |
| **EMBEDDING_DIMENSIONS** | 1536 | Embedding vector size |
| **CRAG_RELEVANCE_THRESHOLD** | 0.7 | Document relevance cutoff |
| **CRAG_AMBIGUOUS_THRESHOLD** | 0.5 | Query ambiguity threshold |
| **REFLECTION_MIN_SCORE** | 0.8 | Self-reflection confidence |
| **MAX_REFLECTION_RETRIES** | 2 | Reflection retry attempts |
| **TOP_K_RESULTS** | 5 | Documents to retrieve |
| **HYDE_NUM_HYPOTHESES** | 3 | Hypothetical document count |
| **HYDE_ENABLED_BY_DEFAULT** | false | Enable HYDE by default |
| **RERANKER_MODEL** | cross-encoder/ms-marco-MiniLM-L-6-v2 | Reranking model |
| **RERANKER_INITIAL_TOP_K** | 20 | Initial retrieval count |
| **RERANKING_ENABLED_BY_DEFAULT** | false | Enable reranking by default |
| **RERANKER_BACKEND** | local | Use local reranker |
| **VOYAGE_API_KEY** | pa-ovN1fMkU... | Voyage AI API key |
| **VOYAGE_MODEL** | rerank-2.5 | Voyage reranking model |
| **UPLOAD_DIR** | /var/app/uploads | Document upload directory |
| **MAX_FILE_SIZE** | 52428800 | Max file size (50MB) |

### Verify Variables
```bash
eb printenv
```

---

## Key Learnings

### 1. Docker Image Size Matters
- **Problem:** CUDA binaries are huge (~1-2GB)
- **Solution:** Use CPU-only wheels or remove GPU dependencies
- **Lesson:** Always check image size before pushing:
  ```bash
  docker images crag-rag-app:latest
  # Look for SIZE column
  ```

### 2. EC2 Storage Planning
- **Problem:** Default 8GB insufficient for large Docker images
- **Solution:** Pre-allocate 50-100GB for production workloads
- **Lesson:** For next deployments, specify volume size during environment creation:
  ```bash
  eb create my-env --instance-type t3.large \
    --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100
  ```

### 3. Environment Variables & Secrets
- **Problem:** Temptation to hardcode secrets in code
- **Solution:** Always use `eb setenv` for sensitive data
- **Lesson:** Never commit `.env` to git (add to `.gitignore`)

### 4. Multi-Stage Docker Builds
- **Benefit:** Reduces final image size significantly
- **Pattern:** Builder stage (compile/install) + Runtime stage (only runtime deps)
- **Example:** Our build went from ~3GB → manageable size

### 5. Azure OpenAI vs OpenAI
- **Key Difference:** Different environment variable names
  - OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`
  - Azure OpenAI: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`
- **Lesson:** Update application code to use correct client:
  ```python
  from openai import AzureOpenAI  # NOT OpenAI
  client = AzureOpenAI(
      api_key=os.getenv("AZURE_OPENAI_API_KEY"),
      api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
      azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
  )
  ```

### 6. Debugging EB Issues
- **Most useful commands:**
  ```bash
  eb status <env>              # Current state
  eb logs <env>                # Stream logs
  eb printenv                  # See all variables
  eb events                     # Recent events
  eb health --refresh          # Health details
  ```

### 7. Patience with Updates
- **Timeline:** 
  - Volume update: ~2-3 minutes
  - Environment variable update: ~1-2 minutes
  - Application deployment: ~5-10 minutes
- **Lesson:** Don't cancel operations mid-update; let them complete fully

---

## Troubleshooting Reference

### Problem: "no space left on device"
```
Error: failed to register layer: write .../nvidia/cu13/lib/libnvJitLink.so.13: 
       no space left on device
```
**Solution:**
```bash
# Increase volume size
aws elasticbeanstalk update-environment \
  --application-name <app> \
  --environment-name <env> \
  --region us-east-1 \
  --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100
```

### Problem: Environment in "Updating" state
```
Status: Updating
Health: Grey
```
**Solution:** Wait for update to complete (5-10 minutes)
```bash
# Monitor progress
watch -n 5 'eb status <env>'  # Linux/Mac
# or manually run periodically
eb status <env>
```

### Problem: Variables not set
```bash
$ eb printenv
# Empty output or missing variables
```
**Solution:** Check if environment update finished
```bash
eb status <env>  # Should show "Ready"
eb events        # Check for errors
```

### Problem: Docker image fails to pull
```
ERROR: Instance deployment failed to download the Docker image
```
**Possible Causes:**
- Image doesn't exist in ECR
- ECR credentials expired
- Network connectivity issue

**Solutions:**
```bash
# Verify image exists in ECR
aws ecr describe-images --repository-name crag-rag-app --region us-east-1

# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 380610849617.dkr.ecr.us-east-1.amazonaws.com

# Push image again
docker push 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest
```

### Problem: Application crashes after deployment
```
Health: Red
```
**Debugging:**
```bash
# Check logs
eb logs <env>

# SSH into instance
eb ssh

# Inside instance:
docker ps                    # Check if container running
docker logs <container-id>   # Application logs
cat /var/log/eb-engine.log   # EB logs
```

### Problem: Azure OpenAI connection fails
```
AuthenticationError: Invalid API key for Azure OpenAI
```
**Check:**
```bash
# Verify environment variables set correctly
eb printenv | grep AZURE

# Verify values:
# - AZURE_OPENAI_API_KEY: non-empty
# - AZURE_OPENAI_ENDPOINT: ends with /
# - AZURE_OPENAI_DEPLOYMENT_NAME: matches deployment name in Azure Portal
# - AZURE_OPENAI_API_VERSION: valid format (YYYY-MM-DD-preview)
```

---

## Commands Cheat Sheet

```bash
# === BUILD & PUSH ===
docker build --platform linux/amd64 -t crag-rag-app:latest .
docker tag crag-rag-app:latest 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest
docker push 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest

# === ELASTIC BEANSTALK ===
eb init                                    # Initialize EB in directory
eb create <env-name>                       # Create new environment
eb deploy <env-name>                       # Deploy application
eb status <env-name>                       # Check status
eb logs <env-name>                         # View logs
eb printenv                                # Show all variables
eb setenv KEY1="value1" KEY2="value2"      # Set variables
eb health --refresh                        # Health details
eb ssh                                     # SSH into instance
eb events                                  # Recent events
eb abort                                   # Cancel ongoing operation

# === AWS CLI ===
aws elasticbeanstalk describe-environments --application-name crag-rag-app --region us-east-1
aws elasticbeanstalk update-environment --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100
aws ecr describe-images --repository-name crag-rag-app --region us-east-1
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 380610849617.dkr.ecr.us-east-1.amazonaws.com

# === DOCKER ===
docker images                              # List images
docker ps                                  # List running containers
docker logs <container-id>                 # View container logs
docker exec -it <container-id> bash        # Shell into container
docker system df                           # Disk usage
docker system prune                        # Clean up
```

---

## For Next Deployment

### Pre-Deployment Checklist
- [ ] Update application code (if needed)
- [ ] Test locally with all dependencies
- [ ] Verify Docker image size: `docker images` (should be < 2GB)
- [ ] Update `.env` file with new credentials
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test Docker build: `docker build -t test:latest .`
- [ ] Check ECR repository exists: `aws ecr describe-repositories`

### Deployment Checklist
- [ ] Build image: `docker build --platform linux/amd64 -t crag-rag-app:latest .`
- [ ] Tag for ECR: `docker tag crag-rag-app:latest 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest`
- [ ] Verify ECR login: `aws ecr get-login-password --region us-east-1 | docker login ...`
- [ ] Push to ECR: `docker push 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest`
- [ ] Set environment variables: `eb setenv KEY="value" ...`
- [ ] Verify variables: `eb printenv`
- [ ] Deploy: `eb deploy <env-name>`
- [ ] Monitor: `eb logs <env-name>`
- [ ] Verify: `eb status <env-name>` (should show "Ready" + "Green")

### Quick Deploy Script (Bash/PowerShell)
```bash
#!/bin/bash
APP_NAME="crag-rag-app"
ENV_NAME="crag-rag-prod"
REGION="us-east-1"
AWS_ACCOUNT="380610849617"

echo "🔨 Building Docker image..."
docker build --platform linux/amd64 -t ${APP_NAME}:latest .

echo "📦 Tagging for ECR..."
docker tag ${APP_NAME}:latest ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}:latest

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com

echo "🚀 Pushing to ECR..."
docker push ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}:latest

echo "📋 Deploying to EB..."
eb deploy ${ENV_NAME}

echo "✅ Deployment complete! Checking status..."
eb status ${ENV_NAME}
```

---

## Contact & Support

**Environment Details:**
- **Application:** crag-rag-app
- **Environment:** crag-rag-prod
- **Region:** us-east-1
- **CNAME:** crag-rag-prod.eba-ddjmismj.us-east-1.elasticbeanstalk.com
- **Instance Type:** t3.large
- **Storage:** 100GB

**Quick Links:**
- AWS Console: https://console.aws.amazon.com/elasticbeanstalk/
- ECR: https://console.aws.amazon.com/ecr/repositories/
- Application: http://crag-rag-prod.eba-ddjmismj.us-east-1.elasticbeanstalk.com

**Important Files:**
- `.env` - Environment variables (LOCAL ONLY, never commit)
- `Dockerfile` - Docker build configuration
- `.elasticbeanstalk/` - EB configuration
- `pyproject.toml` - Python dependencies

---

**Last Updated:** May 4, 2026 00:26 UTC  
**Status:** ✅ Production Ready
