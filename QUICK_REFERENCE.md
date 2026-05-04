# Quick Reference - Deployment Commands

## One-Command Full Deployment (Copy & Paste)

### PowerShell
```powershell
$App = "crag-rag-app"; $Env = "crag-rag-prod"; $Region = "us-east-1"; $Account = "380610849617"; 
Write-Host "Building..." -ForegroundColor Green; 
docker build --platform linux/amd64 -t ${App}:latest . -q; 
Write-Host "Tagging..." -ForegroundColor Green; 
docker tag ${App}:latest ${Account}.dkr.ecr.${Region}.amazonaws.com/${App}:latest; 
Write-Host "Pushing..." -ForegroundColor Green; 
docker push ${Account}.dkr.ecr.${Region}.amazonaws.com/${App}:latest -q; 
Write-Host "Deploying..." -ForegroundColor Green; 
eb deploy ${Env}; 
Write-Host "✅ Done! Checking status..." -ForegroundColor Green; 
eb status ${Env}
```

### Bash
```bash
App="crag-rag-app"; Env="crag-rag-prod"; Region="us-east-1"; Account="380610849617"
echo "Building..." && docker build --platform linux/amd64 -t ${App}:latest . -q
echo "Tagging..." && docker tag ${App}:latest ${Account}.dkr.ecr.${Region}.amazonaws.com/${App}:latest
echo "Pushing..." && docker push ${Account}.dkr.ecr.${Region}.amazonaws.com/${App}:latest -q
echo "Deploying..." && eb deploy ${Env}
echo "✅ Done! Checking status..." && eb status ${Env}
```

---

## Essential Commands

### Build & Push
```bash
# Build
docker build --platform linux/amd64 -t crag-rag-app:latest .

# Tag
docker tag crag-rag-app:latest 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest

# Push
docker push 380610849617.dkr.ecr.us-east-1.amazonaws.com/crag-rag-app:latest
```

### Environment
```bash
# View all variables
eb printenv

# Set variables
eb setenv KEY1="value1" KEY2="value2"

# Delete variable
eb setenv -e KEY1
```

### Status & Monitoring
```bash
# Check environment status
eb status crag-rag-prod

# View logs (real-time)
eb logs crag-rag-prod

# Check health
eb health --refresh

# Recent events
eb events
```

### SSH & Debugging
```bash
# SSH into instance
eb ssh

# Inside instance:
docker ps                              # Running containers
docker logs <container-id>             # Container logs
cat /var/log/eb-engine.log             # EB logs
cat /var/log/eb-engine.log | tail -50  # Last 50 lines
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **"no space left on device"** | Increase volume to 100GB: See DEPLOYMENT_GUIDE.md |
| **Variables not showing** | Wait for env update to complete: `eb status` |
| **Deployment stuck** | Check logs: `eb logs crag-rag-prod` |
| **Red health** | SSH and check Docker: `docker logs <id>` |
| **Connection refused** | Check port 8000 open in security group |
| **Azure OpenAI error** | Verify: `eb printenv \| grep AZURE` |

---

## Pre-Deployment Checklist

- [ ] Code changes tested locally
- [ ] `.env` updated with correct credentials
- [ ] `.env` in `.gitignore`
- [ ] Docker image builds successfully
- [ ] Image size reasonable (< 2GB)
- [ ] ECR credentials valid: `aws ecr describe-repositories --region us-east-1`
- [ ] Environment exists: `eb status crag-rag-prod`

---

## Useful AWS Console Links

- **Elastic Beanstalk:** https://console.aws.amazon.com/elasticbeanstalk/
- **EC2 Instances:** https://console.aws.amazon.com/ec2/
- **ECR Repositories:** https://console.aws.amazon.com/ecr/
- **CloudWatch Logs:** https://console.aws.amazon.com/logs/
- **CloudFormation:** https://console.aws.amazon.com/cloudformation/

---

## Configuration Files Location

| File | Purpose | Location |
|------|---------|----------|
| Dockerfile | Build config | `./Dockerfile` |
| pyproject.toml | Dependencies | `./pyproject.toml` |
| .env | Secrets (LOCAL) | `./`. gitignore` |
| EB Config | Elastic Beanstalk | `./.elasticbeanstalk/config.yml` |

---

## Docker Cleanup (If Needed)

```bash
# Remove dangling images
docker image prune -f

# Remove all unused
docker system prune -f

# View disk usage
docker system df
```

---

## Environment Variables Quick Copy

```bash
# All 24 variables from .env (copy-paste into terminal)
eb setenv \
  AZURE_OPENAI_API_KEY="<value>" \
  AZURE_OPENAI_ENDPOINT="<value>" \
  AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
  AZURE_OPENAI_API_VERSION="2025-01-01-preview" \
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-3-small" \
  TAVILY_API_KEY="<value>" \
  QDRANT_URL="<value>" \
  QDRANT_API_KEY="<value>" \
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
  VOYAGE_API_KEY="<value>" \
  VOYAGE_MODEL="rerank-2.5" \
  UPLOAD_DIR="/var/app/uploads" \
  MAX_FILE_SIZE="52428800"
```

---

## Volume Management (If Storage Issues)

```bash
# Current configuration: 100GB
# To increase to 150GB:
aws elasticbeanstalk update-environment \
  --application-name crag-rag-app \
  --environment-name crag-rag-prod \
  --region us-east-1 \
  --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=RootVolumeSize,Value=150
```

---

**Last Updated:** May 4, 2026  
**Quick Start:** Use one-command deployment above  
**Full Guide:** See DEPLOYMENT_GUIDE.md
