# Complete End-to-End Deployment Guide from Scratch

**Purpose:** Deploy CSR RAG application from scratch with step-by-step commands  
**Audience:** Beginners and experienced developers  
**Status:** Ready for execution  
**Last Updated:** May 4, 2026

---

## 📋 Table of Contents

1. [Prerequisites & Environment Setup](#prerequisites--environment-setup)
2. [Step 1: Verify All Tools Are Installed](#step-1-verify-all-tools-are-installed)
3. [Step 2: Configure AWS Credentials](#step-2-configure-aws-credentials)
4. [Step 3: Prepare Your Application](#step-3-prepare-your-application)
5. [Step 4: Build Docker Image](#step-4-build-docker-image)
6. [Step 5: Push to AWS ECR](#step-5-push-to-aws-ecr)
7. [Step 6: Initialize Elastic Beanstalk](#step-6-initialize-elastic-beanstalk)
8. [Step 7: Create EB Environment](#step-7-create-eb-environment)
9. [Step 8: Set Environment Variables](#step-8-set-environment-variables)
10. [Step 9: Deploy Application](#step-9-deploy-application)
11. [Step 10: Verify Deployment](#step-10-verify-deployment)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Environment Setup

### Required Software
- **Git** (for version control)
- **Docker Desktop** (for containerization)
- **AWS CLI** (for AWS services)
- **EB CLI** (for Elastic Beanstalk)
- **Python 3.12+** (for local development)

### Required AWS Account Resources
- AWS Account with credentials
- S3 bucket for EB deployments (auto-created)
- ECR repository (we'll create this)
- IAM roles (EB will create)

### Required Credentials
- AWS Access Key ID
- AWS Secret Access Key
- Azure OpenAI API Key
- Qdrant API Key
- Tavily API Key
- Voyage API Key

---

## Step 1: Verify All Tools Are Installed

### 1.1 Check Git

**PowerShell:**
```powershell
git --version
# Expected output: git version 2.x.x
```

**CMD:**
```cmd
git --version
```

**Install if missing:** https://git-scm.com/download/win

---

### 1.2 Check Docker

**PowerShell:**
```powershell
docker --version
# Expected output: Docker version 20.x.x, build xxxxx
docker ps
# Expected: Shows list of containers (may be empty)
```

**CMD:**
```cmd
docker --version
docker ps
```

**Install if missing:** https://www.docker.com/products/docker-desktop

---

### 1.3 Check Python

**PowerShell:**
```powershell
python --version
# Expected output: Python 3.12.x (or higher)
pip --version
```

**CMD:**
```cmd
python --version
pip --version
```

**Install if missing:** https://www.python.org/downloads/ (choose 3.12+)

---

### 1.4 Check AWS CLI

**PowerShell:**
```powershell
aws --version
# Expected output: aws-cli/2.x.x ...
```

**CMD:**
```cmd
aws --version
```

**Install if missing:**
```powershell
# PowerShell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Or use pip
pip install --upgrade awscli
```

---

### 1.5 Check EB CLI

**PowerShell:**
```powershell
eb --version
# Expected output: EB CLI x.x.x
```

**CMD:**
```cmd
eb --version
```

**Install if missing:**
```powershell
# PowerShell
pip install awsebcli

# CMD
pip install awsebcli
```

---

## Step 2: Configure AWS Credentials

### 2.1 Get Your AWS Credentials

**In AWS Console:**
1. Go to: https://console.aws.amazon.com/
2. Click your username → **Security Credentials**
3. Under "Access keys" → **Create access key**
4. Copy both:
   - Access Key ID
   - Secret Access Key

⚠️ **IMPORTANT:** Save these securely. Never commit to Git!

---

### 2.2 Configure AWS CLI

**PowerShell:**
```powershell
aws configure
# When prompted, enter:
# AWS Access Key ID: <your_access_key>
# AWS Secret Access Key: <your_secret_key>
# Default region: us-east-1
# Default output format: json
```

**CMD:**
```cmd
aws configure
REM Follow same prompts
```

---

### 2.3 Verify AWS Configuration

**PowerShell:**
```powershell
aws sts get-caller-identity
# Expected output: Shows your AWS Account ID, User ARN
```

**CMD:**
```cmd
aws sts get-caller-identity
```

---

## Step 3: Prepare Your Application

### 3.1 Clone or Navigate to Project

**PowerShell:**
```powershell
# If cloning (first time):
git clone https://github.com/Mmbsaksd/csr_rag.git
cd csr_rag

# Or if already cloned:
cd f:\sourab\csr_rag
```

**CMD:**
```cmd
cd f:\sourab\csr_rag
```

---

### 3.2 Create `.env` File with Your Secrets

**PowerShell (Create file):**
```powershell
# Create .env file
@"
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=<YOUR_AZURE_OPENAI_API_KEY>
AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small

# Tavily Web Search
TAVILY_API_KEY=<YOUR_TAVILY_API_KEY>

# Qdrant Vector Store
QDRANT_URL=https://<your-cluster>.eu-central-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=<YOUR_QDRANT_API_KEY>
QDRANT_COLLECTION_NAME=crag_documents_v2

# Embedding Settings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# CRAG Settings
CRAG_RELEVANCE_THRESHOLD=0.7
CRAG_AMBIGUOUS_THRESHOLD=0.5

# Self-Reflective Settings
REFLECTION_MIN_SCORE=0.8
MAX_REFLECTION_RETRIES=2

# Retrieval
TOP_K_RESULTS=5

# HYDE Settings
HYDE_NUM_HYPOTHESES=3
HYDE_ENABLED_BY_DEFAULT=false

# Reranking Settings
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_INITIAL_TOP_K=20
RERANKING_ENABLED_BY_DEFAULT=false
RERANKER_BACKEND=local

# Voyage Reranking (Alternative)
VOYAGE_API_KEY=<YOUR_VOYAGE_API_KEY>
VOYAGE_MODEL=rerank-2.5

# Upload Settings
UPLOAD_DIR=uploads
MAX_FILE_SIZE=52428800
"@ | Out-File -FilePath ".env" -Encoding UTF8
```

**CMD (Manual):**
```cmd
REM Create .env file with notepad or your editor
notepad .env
REM Then add the above content
```

---

### 3.3 Verify `.env` is in `.gitignore`

**PowerShell:**
```powershell
# Check if .gitignore exists
cat .gitignore | Select-String ".env"
# Should output: .env
```

**CMD:**
```cmd
type .gitignore | find ".env"
```

**If not present, add it:**

**PowerShell:**
```powershell
Add-Content .gitignore ".env"
```

**CMD:**
```cmd
echo .env >> .gitignore
```

---

### 3.4 Pull Latest Code

**PowerShell:**
```powershell
git pull
# Expected: Already up to date (or pulls latest code)
```

**CMD:**
```cmd
git pull
```

---

## Step 4: Build Docker Image

### 4.1 Build Locally

**PowerShell:**
```powershell
Write-Host "Building Docker image..." -ForegroundColor Green
docker build --platform linux/amd64 -t crag-rag-app:latest .
# Expected: Successfully tagged as docker.io/library/crag-rag-app:latest
```

**CMD:**
```cmd
echo Building Docker image...
docker build --platform linux/amd64 -t crag-rag-app:latest .
```

---

### 4.2 Verify Image was Built

**PowerShell:**
```powershell
docker images crag-rag-app:latest
# Expected: Shows image with size (should be < 2GB)
```

**CMD:**
```cmd
docker images crag-rag-app:latest
```

---

### 4.3 (Optional) Test Image Locally

**PowerShell:**
```powershell
# Run image to test
docker run --rm -e AZURE_OPENAI_API_KEY="test" -p 8000:8000 crag-rag-app:latest &

# Wait a moment for startup
Start-Sleep -Seconds 5

# Test endpoint
curl http://localhost:8000/docs
# Should show Swagger UI

# Stop the container
docker stop (docker ps -q)
```

**CMD:**
```cmd
REM Run image to test
docker run --rm -e AZURE_OPENAI_API_KEY="test" -p 8000:8000 crag-rag-app:latest

REM In another terminal, test:
curl http://localhost:8000/docs
```

---

## Step 5: Push to AWS ECR

### 5.1 Get Your AWS Account ID

**PowerShell:**
```powershell
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$AWS_REGION = "us-east-1"
$ECR_REPO = "crag-rag-app"

Write-Host "AWS Account ID: $AWS_ACCOUNT_ID"
Write-Host "Region: $AWS_REGION"
Write-Host "Repository: $ECR_REPO"
```

**CMD:**
```cmd
for /f %i in ('aws sts get-caller-identity --query Account --output text') do set AWS_ACCOUNT_ID=%i
set AWS_REGION=us-east-1
set ECR_REPO=crag-rag-app

echo AWS Account ID: %AWS_ACCOUNT_ID%
echo Region: %AWS_REGION%
echo Repository: %ECR_REPO%
```

---

### 5.2 Create ECR Repository (First Time Only)

**PowerShell:**
```powershell
Write-Host "Creating ECR repository..." -ForegroundColor Yellow

aws ecr create-repository `
  --repository-name $ECR_REPO `
  --region $AWS_REGION `
  --image-scanning-configuration scanOnPush=true

Write-Host "Repository created!" -ForegroundColor Green
```

**CMD:**
```cmd
echo Creating ECR repository...
aws ecr create-repository ^
  --repository-name %ECR_REPO% ^
  --region %AWS_REGION% ^
  --image-scanning-configuration scanOnPush=true
```

**Note:** If repository already exists, you'll see error - that's OK

---

### 5.3 Login to ECR

**PowerShell:**
```powershell
Write-Host "Logging in to ECR..." -ForegroundColor Yellow

aws ecr get-login-password --region $AWS_REGION | `
  docker login --username AWS --password-stdin `
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "Login successful!" -ForegroundColor Green
```

**CMD:**
```cmd
echo Logging in to ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
```

---

### 5.4 Tag Image for ECR

**PowerShell:**
```powershell
$ECR_IMAGE = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO`:latest"

Write-Host "Tagging image for ECR..." -ForegroundColor Yellow
docker tag crag-rag-app:latest $ECR_IMAGE

Write-Host "Tagged as: $ECR_IMAGE" -ForegroundColor Green
```

**CMD:**
```cmd
set ECR_IMAGE=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO%:latest

echo Tagging image for ECR...
docker tag crag-rag-app:latest %ECR_IMAGE%
echo Tagged as: %ECR_IMAGE%
```

---

### 5.5 Push to ECR

**PowerShell:**
```powershell
Write-Host "Pushing to ECR..." -ForegroundColor Yellow
docker push $ECR_IMAGE

Write-Host "Push successful!" -ForegroundColor Green
```

**CMD:**
```cmd
echo Pushing to ECR...
docker push %ECR_IMAGE%
```

---

### 5.6 Verify Image in ECR

**PowerShell:**
```powershell
aws ecr describe-images `
  --repository-name $ECR_REPO `
  --region $AWS_REGION

Write-Host "Image verified in ECR!" -ForegroundColor Green
```

**CMD:**
```cmd
aws ecr describe-images --repository-name %ECR_REPO% --region %AWS_REGION%
```

---

## Step 6: Initialize Elastic Beanstalk

### 6.1 Initialize EB

**PowerShell:**
```powershell
Write-Host "Initializing Elastic Beanstalk..." -ForegroundColor Yellow

eb init -p docker `
  -r $AWS_REGION `
  -a crag-rag-app `
  --keyname my-eb-key

Write-Host "EB initialized!" -ForegroundColor Green
```

**CMD:**
```cmd
echo Initializing Elastic Beanstalk...
eb init -p docker -r %AWS_REGION% -a crag-rag-app --keyname my-eb-key
```

---

### 6.2 Verify EB Configuration

**PowerShell:**
```powershell
cat .elasticbeanstalk\config.yml
```

**CMD:**
```cmd
type .elasticbeanstalk\config.yml
```

---

## Step 7: Create EB Environment

### 7.1 Create Production Environment

**PowerShell:**
```powershell
Write-Host "Creating EB environment..." -ForegroundColor Yellow

eb create crag-rag-prod `
  --instance-type t3.large `
  --single `
  --envvars `
  --option-settings `
  Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100

Write-Host "Environment created! This may take 5-10 minutes..." -ForegroundColor Green
```

**CMD:**
```cmd
echo Creating EB environment...
eb create crag-rag-prod --instance-type t3.large --single
```

---

### 7.2 Monitor Environment Creation

**PowerShell:**
```powershell
Write-Host "Waiting for environment to be ready..." -ForegroundColor Yellow

# Loop until ready (max 20 attempts, 30 seconds each)
$attempts = 0
while ($attempts -lt 20) {
    $status = eb status crag-rag-prod 2>&1 | Select-String "Status:" | Select-Object -First 1
    
    if ($status -match "Ready") {
        Write-Host "Environment is READY!" -ForegroundColor Green
        break
    }
    
    Write-Host "Still updating... ($attempts/20)"
    Start-Sleep -Seconds 30
    $attempts++
}

if ($attempts -ge 20) {
    Write-Host "Timeout waiting for environment. Check with: eb status crag-rag-prod" -ForegroundColor Yellow
}
```

**CMD:**
```cmd
echo Waiting for environment to be ready...
:wait_loop
eb status crag-rag-prod
timeout /t 30
goto wait_loop
REM Press Ctrl+C when status shows "Ready"
```

---

### 7.3 Verify Environment is Ready

**PowerShell:**
```powershell
eb status crag-rag-prod
# Expected: Status: Ready, Health: Green
```

**CMD:**
```cmd
eb status crag-rag-prod
```

---

## Step 8: Set Environment Variables

### 8.1 Create Variables Script (Save and Reuse)

**PowerShell - Create script file:**
```powershell
# Save as: set-env-vars.ps1

$env_vars = @(
    'AZURE_OPENAI_API_KEY=<YOUR_VALUE>'
    'AZURE_OPENAI_ENDPOINT=<YOUR_VALUE>'
    'AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o'
    'AZURE_OPENAI_API_VERSION=2025-01-01-preview'
    'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small'
    'TAVILY_API_KEY=<YOUR_VALUE>'
    'QDRANT_URL=<YOUR_VALUE>'
    'QDRANT_API_KEY=<YOUR_VALUE>'
    'QDRANT_COLLECTION_NAME=crag_documents_v2'
    'EMBEDDING_MODEL=text-embedding-3-small'
    'EMBEDDING_DIMENSIONS=1536'
    'CRAG_RELEVANCE_THRESHOLD=0.7'
    'CRAG_AMBIGUOUS_THRESHOLD=0.5'
    'REFLECTION_MIN_SCORE=0.8'
    'MAX_REFLECTION_RETRIES=2'
    'TOP_K_RESULTS=5'
    'HYDE_NUM_HYPOTHESES=3'
    'HYDE_ENABLED_BY_DEFAULT=false'
    'RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2'
    'RERANKER_INITIAL_TOP_K=20'
    'RERANKING_ENABLED_BY_DEFAULT=false'
    'RERANKER_BACKEND=local'
    'VOYAGE_API_KEY=<YOUR_VALUE>'
    'VOYAGE_MODEL=rerank-2.5'
    'UPLOAD_DIR=/var/app/uploads'
    'MAX_FILE_SIZE=52428800'
)

$env_string = $env_vars -join ' '
Write-Host "Setting environment variables..." -ForegroundColor Yellow
eb setenv $env_string
Write-Host "Environment variables set!" -ForegroundColor Green
```

---

### 8.2 Set Variables (From .env File)

**PowerShell:**
```powershell
# Read from .env and set on EB
Write-Host "Reading .env file..." -ForegroundColor Yellow

$env_vars = Get-Content .env | Where-Object { $_ -and !$_.StartsWith("#") } | ForEach-Object {
    $parts = $_ -split '=', 2
    if ($parts.Count -eq 2) {
        # Quote values with spaces
        if ($parts[1] -match '\s') {
            "$($parts[0])=`"$($parts[1])`""
        } else {
            $_
        }
    }
}

Write-Host "Setting $($env_vars.Count) environment variables..." -ForegroundColor Yellow

$cmd = "eb setenv $($env_vars -join ' ')"
Invoke-Expression $cmd

Write-Host "Environment variables set!" -ForegroundColor Green
```

**CMD:**
```cmd
echo Setting environment variables...
REM Manual approach - use eb setenv command:
eb setenv AZURE_OPENAI_API_KEY="value1" TAVILY_API_KEY="value2" ... (add all 24 variables)
```

---

### 8.3 Verify Variables were Set

**PowerShell:**
```powershell
Write-Host "Verifying environment variables..." -ForegroundColor Yellow
eb printenv

Write-Host "Variables verified!" -ForegroundColor Green
```

**CMD:**
```cmd
eb printenv
```

---

## Step 9: Deploy Application

### 9.1 Deploy to EB

**PowerShell:**
```powershell
Write-Host "Deploying application..." -ForegroundColor Yellow

eb deploy crag-rag-prod

Write-Host "Deployment initiated!" -ForegroundColor Green
```

**CMD:**
```cmd
echo Deploying application...
eb deploy crag-rag-prod
```

---

### 9.2 Monitor Deployment

**PowerShell:**
```powershell
Write-Host "Monitoring deployment..." -ForegroundColor Yellow

# Loop until ready (max 30 attempts, 30 seconds each)
$attempts = 0
while ($attempts -lt 30) {
    $status = eb status crag-rag-prod 2>&1
    
    if ($status -match "Ready" -and $status -match "Green") {
        Write-Host "Deployment COMPLETE!" -ForegroundColor Green
        Write-Host $status
        break
    }
    
    Write-Host "Deployment in progress... ($attempts/30)"
    Start-Sleep -Seconds 30
    $attempts++
}

if ($attempts -ge 30) {
    Write-Host "Timeout waiting for deployment. Check with: eb logs crag-rag-prod" -ForegroundColor Yellow
}
```

**CMD:**
```cmd
:deploy_loop
echo Checking deployment status...
eb status crag-rag-prod
timeout /t 30
goto deploy_loop
REM Press Ctrl+C when status shows "Ready" and "Green"
```

---

### 9.3 View Deployment Logs

**PowerShell:**
```powershell
Write-Host "Fetching deployment logs..." -ForegroundColor Yellow
eb logs crag-rag-prod
```

**CMD:**
```cmd
eb logs crag-rag-prod
```

---

## Step 10: Verify Deployment

### 10.1 Get Application URL

**PowerShell:**
```powershell
$app_url = (eb status crag-rag-prod | Select-String "CNAME" | ForEach-Object { $_ -match "CNAME: (?<url>\S+)"; $matches['url'] })

Write-Host "Application URL: http://$app_url" -ForegroundColor Green
Write-Host "Open in browser: http://$app_url/docs" -ForegroundColor Cyan
```

**CMD:**
```cmd
eb status crag-rag-prod
REM Copy CNAME value and paste into browser: http://cname-value/docs
```

---

### 10.2 Test API Endpoint

**PowerShell:**
```powershell
$CNAME = (eb status crag-rag-prod | Select-String "CNAME:" | ForEach-Object { $_ -replace ".*CNAME: ", "" })

Write-Host "Testing API endpoint..." -ForegroundColor Yellow
Write-Host "URL: http://$CNAME/docs" -ForegroundColor Cyan

# Optional: Use curl to test
curl -s "http://$CNAME/docs" | Select-String "swagger" | Out-Host

Write-Host "If Swagger UI loads, deployment is successful!" -ForegroundColor Green
```

**CMD:**
```cmd
REM Open in browser (manual):
REM http://<cname>/docs
REM You should see FastAPI Swagger UI
```

---

### 10.3 Verify Health Status

**PowerShell:**
```powershell
Write-Host "Checking environment health..." -ForegroundColor Yellow

eb health --refresh
# Expected: Color indicator should be GREEN

Write-Host "Health check complete!" -ForegroundColor Green
```

**CMD:**
```cmd
eb health --refresh
```

---

### 10.4 Check Recent Events

**PowerShell:**
```powershell
Write-Host "Recent deployment events:" -ForegroundColor Yellow
eb events
```

**CMD:**
```cmd
eb events
```

---

## Troubleshooting

### Issue: "no space left on device"

**Error Message:**
```
failed to register layer: write .../nvidia/cu13/lib/libnvJitLink.so.13: no space left on device
```

**Solution:**
```powershell
# Increase volume size
aws elasticbeanstalk update-environment `
  --application-name crag-rag-app `
  --environment-name crag-rag-prod `
  --region us-east-1 `
  --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=100
```

---

### Issue: Environment Stuck in "Updating"

**Solution:**
```powershell
# Wait longer (5-10 minutes total)
# Or abort and start over:
eb abort crag-rag-prod

# Then check status:
eb status crag-rag-prod
```

---

### Issue: Variables Not Set

**Solution:**
```powershell
# Verify they were set:
eb printenv

# If empty, try again:
eb setenv KEY1="value1" KEY2="value2" ...

# Wait for update:
eb status crag-rag-prod
```

---

### Issue: Application Health is Red

**Solution:**
```powershell
# Check logs:
eb logs crag-rag-prod

# SSH into instance:
eb ssh

# Inside instance:
docker ps                    # Check container
docker logs <container-id>   # View logs
```

---

### Issue: "Docker image not found in ECR"

**Solution:**
```powershell
# Verify image in ECR:
aws ecr describe-images --repository-name crag-rag-app --region us-east-1

# If not there, re-push:
docker push $ECR_IMAGE
```

---

## Complete Automated Script

### One PowerShell Script That Does Everything

**Save as: `deploy-from-scratch.ps1`**

```powershell
# ============================================================
# CRAG RAG Complete Deployment Script
# ============================================================
# Run: .\deploy-from-scratch.ps1

param(
    [string]$AppName = "crag-rag-app",
    [string]$EnvName = "crag-rag-prod",
    [string]$AwsRegion = "us-east-1",
    [string]$InstanceType = "t3.large"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CRAG RAG Deployment from Scratch" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Verify Tools
Write-Host "`n[1/10] Verifying tools..." -ForegroundColor Yellow
git --version | Out-Null
docker --version | Out-Null
aws --version | Out-Null
eb --version | Out-Null
Write-Host "✓ All tools verified" -ForegroundColor Green

# Step 2: Configure AWS
Write-Host "`n[2/10] Configuring AWS..." -ForegroundColor Yellow
$AwsAccountId = (aws sts get-caller-identity --query Account --output text)
Write-Host "✓ AWS Account: $AwsAccountId" -ForegroundColor Green

# Step 3: Build Docker Image
Write-Host "`n[3/10] Building Docker image..." -ForegroundColor Yellow
docker build --platform linux/amd64 -t ${AppName}:latest .
Write-Host "✓ Docker image built" -ForegroundColor Green

# Step 4: Setup ECR
Write-Host "`n[4/10] Setting up ECR..." -ForegroundColor Yellow
$EcrImage = "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$AppName`:latest"

# Create repo (may fail if exists, that's OK)
aws ecr create-repository --repository-name $AppName --region $AwsRegion 2>&1 | Out-Null

# Login
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"

# Tag and push
docker tag ${AppName}:latest $EcrImage
docker push $EcrImage
Write-Host "✓ Image pushed to ECR: $EcrImage" -ForegroundColor Green

# Step 5: Initialize EB
Write-Host "`n[5/10] Initializing Elastic Beanstalk..." -ForegroundColor Yellow
eb init -p docker -r $AwsRegion -a $AppName --quiet
Write-Host "✓ EB initialized" -ForegroundColor Green

# Step 6: Create Environment
Write-Host "`n[6/10] Creating EB environment (this takes 5-10 minutes)..." -ForegroundColor Yellow
eb create $EnvName --instance-type $InstanceType --single
Write-Host "✓ EB environment created" -ForegroundColor Green

# Step 7-8: Set Variables and Deploy
Write-Host "`n[7/10] Setting environment variables..." -ForegroundColor Yellow
Write-Host "⚠ Update .env file with your actual credentials first!" -ForegroundColor Red
Write-Host "Then run: eb setenv KEY=VALUE KEY2=VALUE2 ..." -ForegroundColor Yellow

# Step 9: Deploy
Write-Host "`n[8/10] Deploying application..." -ForegroundColor Yellow
eb deploy $EnvName
Write-Host "✓ Application deployed" -ForegroundColor Green

# Step 10: Verify
Write-Host "`n[9/10] Verifying deployment..." -ForegroundColor Yellow
$Status = eb status $EnvName
Write-Host $Status
Write-Host "✓ Deployment complete" -ForegroundColor Green

# Final Status
Write-Host "`n[10/10] Getting final status..." -ForegroundColor Yellow
$Cname = ($Status | Select-String "CNAME:" | ForEach-Object { $_ -replace ".*CNAME: ", "" })
Write-Host "✓ Application running at: http://$Cname" -ForegroundColor Green
Write-Host "✓ Swagger UI at: http://$Cname/docs" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
```

**Run it:**
```powershell
.\deploy-from-scratch.ps1
```

---

## Quick Reference: All Commands at a Glance

### Verify Tools
```powershell
git --version; docker --version; aws --version; eb --version
```

### Setup & Build
```powershell
$AccountId = (aws sts get-caller-identity --query Account --output text)
docker build --platform linux/amd64 -t crag-rag-app:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.us-east-1.amazonaws.com"
docker tag crag-rag-app:latest "$AccountId.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest"
docker push "$AccountId.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest"
```

### EB Setup & Deploy
```powershell
eb init -p docker -r us-east-1 -a crag-rag-app
eb create crag-rag-prod --instance-type t3.large --single
eb setenv AZURE_OPENAI_API_KEY="..." [... more variables ...]
eb deploy crag-rag-prod
eb status crag-rag-prod
```

### Monitor
```powershell
eb health --refresh
eb logs crag-rag-prod
eb events
```

---

## Summary

By following this guide step-by-step, you'll have:

✅ Verified all required tools  
✅ Configured AWS credentials  
✅ Built Docker image locally  
✅ Pushed image to AWS ECR  
✅ Initialized Elastic Beanstalk  
✅ Created production environment  
✅ Set all environment variables  
✅ Deployed application  
✅ Verified it's running  
✅ Got your live URL  

---

**Total Time:** ~20-30 minutes (mostly waiting for AWS to provision)

**You're done!** Your application is now running in production. 🚀

---

**Last Updated:** May 4, 2026  
**Status:** Ready for execution
