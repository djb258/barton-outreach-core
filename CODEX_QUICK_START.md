# Codex Global Terminal Setup - Quick Start

✅ **Setup Complete!** Codex CLI is installed and ready.

---

## 🚀 Quick Setup (2 Steps)

### **Step 1: Get Your API Key**

1. Go to: https://platform.openai.com/api-keys
2. Sign in with your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### **Step 2: Set Environment Variable**

**For PowerShell (Permanent):**
```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key-here", "User")
```

**For Current Session Only:**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Then restart your terminal** for permanent changes to take effect.

---

## 📍 PATH Already Configured

The Codex CLI is installed at:
```
C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts
```

This directory is already in your PATH (from Gemini setup), so `codex` command should work immediately after you set your API key!

---

## ✅ Test It Works

```powershell
# Test 1: Check if codex command is available
codex --help

# Test 2: Run a simple query
codex "Say hello in one sentence"

# Test 3: Test script
python test_codex.py
```

---

## 💡 Usage Examples

### **From Terminal:**
```bash
# Code generation
codex "Write a Python function to connect to PostgreSQL"

# Code explanation
codex "Explain this SQL: SELECT * FROM marketing.company_master WHERE email_verified = TRUE"

# Code refactoring
codex "Refactor this function to use async/await"

# Different models
codex --model gpt-4-turbo "Generate a REST API endpoint"
codex --model gpt-3.5-turbo "Simple utility function"

# Multi-line prompts
codex "Create a Python class for managing Neon database connections with connection pooling"
```

### **In Python Scripts:**
```python
from openai import OpenAI
import os

# Configure
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Use GPT-4
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a function to query Neon database"}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(response.choices[0].message.content)
```

---

## 🎯 Available Models

| Model | Best For | Cost |
|-------|----------|------|
| `gpt-4` | Complex code, analysis | Higher |
| `gpt-4-turbo` | Fast GPT-4 performance | Medium |
| `gpt-3.5-turbo` | Simple tasks, quick responses | Lower |
| `code-davinci-002` | Legacy Codex (deprecated) | - |

**Default:** `gpt-4`

---

## 🔧 Troubleshooting

### **"codex: command not found"**
- Make sure you added the Scripts directory to PATH (should already be there from Gemini)
- Restart your terminal
- Try: `python C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\codex.py "test"`

### **"OPENAI_API_KEY not set"**
- Set the environment variable (see Step 2 above)
- Restart terminal after setting
- Verify: `echo $env:OPENAI_API_KEY` (should show your key)

### **"API key invalid" or "Incorrect API key"**
- Get a fresh key from https://platform.openai.com/api-keys
- Make sure you copied the entire key (starts with `sk-`)
- Check your OpenAI account has credits/billing set up

### **"Rate limit exceeded"**
- You've hit OpenAI's rate limits
- Wait a few minutes or upgrade your plan
- Use `gpt-3.5-turbo` for higher rate limits

---

## 📚 Advanced Usage

### **Streaming Responses:**
```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Write a long function"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### **With Function Calling:**
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }]
)
```

### **Code Completion:**
```python
# For code completion (legacy Codex)
response = client.completions.create(
    model="code-davinci-002",
    prompt="def fibonacci(n):",
    max_tokens=200,
    temperature=0
)
```

---

## 🆚 Gemini vs Codex

| Feature | Gemini | Codex |
|---------|--------|-------|
| **Command** | `gemini` | `codex` |
| **API Key** | `GOOGLE_API_KEY` | `OPENAI_API_KEY` |
| **Best For** | General AI, analysis | Code generation, refactoring |
| **Models** | gemini-pro, gemini-pro-vision | gpt-4, gpt-3.5-turbo |
| **Cost** | Free tier available | Pay-per-use |

**Use both!** Gemini for analysis and general tasks, Codex for code-specific work.

---

**Setup Date:** 2025-11-03  
**Status:** ✅ Ready to use  
**Location:** `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\codex.py`

