# Azure OpenAI Configuration Guide

**Purpose:** Document how to configure the RAG application for Azure OpenAI (instead of standard OpenAI)

---

## Key Differences: OpenAI vs Azure OpenAI

### OpenAI API
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",  # Any model name
    messages=[...]
)
```

**Environment Variables:**
```env
OPENAI_API_KEY=sk-...
```

### Azure OpenAI API
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="...",
    api_version="2025-01-01-preview",
    azure_endpoint="https://your-resource.cognitiveservices.azure.com/"
)
response = client.chat.completions.create(
    model="gpt-4o",  # Deployment name (not model name)
    messages=[...]
)
```

**Environment Variables:**
```env
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # Must match deployment in Azure
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

---

## Why Azure OpenAI?

✅ **Advantages:**
- Data residency (EU-Central-1)
- Private endpoints possible
- Better compliance/security
- Integrated with Azure ecosystem
- Cost control via Azure budgets

❌ **Disadvantages:**
- Requires Azure account
- More setup steps
- Different variable names
- Different SDK imports

---

## Configuration Steps

### 1. Create Azure OpenAI Resource

**In Azure Portal:**
1. Go to **Create Resource** → Search "OpenAI"
2. Click **Azure OpenAI**
3. Fill in:
   - **Resource Group:** Create new or select existing
   - **Name:** `moham-mi3bbwto` (example)
   - **Location:** East US 2 (or your preferred)
   - **Pricing Tier:** Standard S0

**Result:**
- **Endpoint:** https://moham-mi3bbwto-eastus2.cognitiveservices.azure.com/
- **API Key:** Found in "Keys and Endpoint" section

### 2. Deploy Models

**In Azure OpenAI Studio:**
1. Go to **Deployments**
2. Create new deployment:
   - **Name:** `gpt-4o`
   - **Model:** `gpt-4o`
   - **Version:** Latest
3. Create second deployment:
   - **Name:** `text-embedding-3-small`
   - **Model:** `text-embedding-3-small`
   - **Version:** Latest

**Why Two Deployments?**
- One for chat/completions (gpt-4o)
- One for embeddings (text-embedding-3-small)
- Each deployment is independent

### 3. Get Credentials

**Location in Azure Portal:**
```
Azure OpenAI Resource → Keys and Endpoint
```

**Copy These:**
```
API Key 1: <YOUR_AZURE_OPENAI_API_KEY>
Endpoint: https://<your-resource-name>.cognitiveservices.azure.com/
```

### 4. Update Application Code

**File: `app/services/llm_service.py`**

```python
import os
from openai import AzureOpenAI

class AzureOpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    def create_chat_completion(self, messages: list, temperature: float = 0.7):
        """Create chat completion using Azure OpenAI"""
        response = self.client.chat.completions.create(
            model=self.deployment_name,  # Use deployment name, not model name
            messages=messages,
            temperature=temperature,
            max_tokens=2048
        )
        return response.choices[0].message.content
```

**File: `app/services/embedding_service.py`**

```python
import os
from openai import AzureOpenAI

class AzureEmbeddingService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    
    def embed_text(self, text: str) -> list:
        """Generate embeddings using Azure OpenAI"""
        response = self.client.embeddings.create(
            model=self.embedding_deployment,  # Deployment name
            input=text
        )
        return response.data[0].embedding
```

### 5. Set Environment Variables on EB

```bash
eb setenv \
    AZURE_OPENAI_API_KEY="<YOUR_AZURE_OPENAI_API_KEY>" \
    AZURE_OPENAI_ENDPOINT="https://<your-resource-name>.cognitiveservices.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2025-01-01-preview" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-3-small"
```

### 6. Update Dependencies

**File: `pyproject.toml`**

```toml
dependencies = [
    "openai>=1.54.0",  # For Azure OpenAI SDK
    # ... other dependencies
]
```

---

## Testing Locally

### Before Deployment

**1. Create `.env` file:**
```env
AZURE_OPENAI_API_KEY=<YOUR_AZURE_OPENAI_API_KEY>
AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small
```

**2. Test chat completion:**
```python
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

**3. Test embeddings:**
```python
response = client.embeddings.create(
    model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
    input="Test text"
)

print(f"Embedding size: {len(response.data[0].embedding)}")  # Should be 1536
```

---

## Troubleshooting

### Issue: AuthenticationError
```
openai.error.AuthenticationError: Invalid credentials for Azure OpenAI
```

**Check:**
```bash
# Verify in EB
eb printenv | grep AZURE

# Verify values:
# - AZURE_OPENAI_API_KEY is not empty
# - AZURE_OPENAI_ENDPOINT ends with / or cognitiveservices.azure.com/
# - AZURE_OPENAI_DEPLOYMENT_NAME matches deployment in Azure Portal
```

### Issue: DeploymentNotFound
```
azure.core.exceptions.ResourceNotFoundError: Invalid deployment id: gpt-4o
```

**Check:**
```
Azure Portal → Azure OpenAI → Deployments

Make sure:
- Deployment name is EXACTLY "gpt-4o"
- Deployment is in same resource as API key
- Deployment is in "Succeeded" state
```

### Issue: APIConnectionError
```
openai.error.APIConnectionError: Failed to establish connection
```

**Check:**
```bash
# Verify endpoint accessible
curl "https://moham-mi3bbwto-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview" \
  -H "api-key: YOUR_KEY"
```

### Issue: InvalidRequestError - Model not found
```
InvalidRequestError: The model `text-embedding-3-small` does not exist
```

**Solution:**
Check that embedding deployment name is set correctly:
```bash
eb setenv AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-3-small"
```

---

## Cost Comparison

### Pricing (as of May 2026)

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| **OpenAI** | gpt-4o | $5/1M | $15/1M |
| **Azure OpenAI** | gpt-4o | $5/1M | $15/1M |
| **Embeddings (OpenAI)** | text-embedding-3-small | $0.02/1M | - |
| **Embeddings (Azure)** | text-embedding-3-small | $0.02/1M | - |

**Same pricing, but:**
- Azure: Pay per month (commitment)
- OpenAI: Pay as you go

---

## API Versions

Azure OpenAI has multiple API versions. Common ones:

```
2025-01-01-preview  (Latest, recommended)
2024-12-01-preview
2024-10-01-preview
2024-08-01-preview
2024-06-01
2024-05-01-preview
```

**When to update:**
- New models released
- New features available
- Current version deprecated

**Check available versions:**
```
Azure Portal → Azure OpenAI → Playground → "View code"
Look for api-version parameter
```

---

## Migration: OpenAI → Azure OpenAI

**If switching from standard OpenAI:**

1. **Update imports:**
   ```python
   # From
   from openai import OpenAI
   # To
   from openai import AzureOpenAI
   ```

2. **Update initialization:**
   ```python
   # From
   client = OpenAI(api_key="sk-...")
   # To
   client = AzureOpenAI(
       api_key="...",
       api_version="2025-01-01-preview",
       azure_endpoint="https://..."
   )
   ```

3. **Update model references:**
   ```python
   # From (model name)
   model="gpt-4o"
   # To (deployment name)
   model="gpt-4o"  # But this is a deployment, not model
   ```

4. **Update environment variables:**
   ```bash
   # Remove
   OPENAI_API_KEY=sk-...
   
   # Add
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_DEPLOYMENT_NAME=...
   AZURE_OPENAI_API_VERSION=...
   ```

---

## Security Best Practices

### Never commit secrets:
```bash
# .gitignore
.env
.env.local
.env.*.local
```

### Use Azure Key Vault (Production):
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

api_key = client.get_secret("AZURE-OPENAI-API-KEY").value
```

### Rotate keys regularly:
```
Azure Portal → Azure OpenAI → Keys and Endpoint → Regenerate Key 1
```

---

## Useful Resources

- **Azure OpenAI Docs:** https://learn.microsoft.com/en-us/azure/ai-services/openai/
- **API Reference:** https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
- **Python SDK:** https://github.com/openai/openai-python
- **Pricing:** https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/

---

**Last Updated:** May 4, 2026  
**Status:** Production Configuration
