# Claude Global Terminal Setup - Quick Start

✅ **Setup Complete!** Claude CLI is installed and ready.

---

## 🚀 Quick Setup (2 Steps)

### **Step 1: Get Your API Key**

1. Go to: https://console.anthropic.com/settings/keys
2. Sign in with your Anthropic account
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-`)

### **Step 2: Set Environment Variable**

**For PowerShell (Permanent):**
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-api-key-here", "User")
```

**For Current Session Only:**
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

**Then restart your terminal** for permanent changes to take effect.

---

## 📍 PATH Already Configured

The Claude CLI is installed at:
```
C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts
```

This directory is already in your PATH (from Gemini/Codex setup), so `claude` command should work immediately after you set your API key!

---

## ✅ Test It Works

```powershell
# Test 1: Check if claude command is available
claude --help

# Test 2: Run a simple query
claude "Say hello in one sentence"

# Test 3: Test script
python test_claude.py
```

---

## 💡 Usage Examples

### **From Terminal:**
```bash
# Basic query
claude "What is PostgreSQL?"

# Code generation
claude "Write a Python function to connect to Neon database"

# Analysis
claude "Analyze this SQL: SELECT * FROM marketing.company_master WHERE email_verified = TRUE"

# Different models
claude --model claude-3-5-haiku-20241022 "Quick question"
claude --model claude-3-opus-20240229 "Complex analysis requiring deep reasoning"

# Multi-line prompts
claude "Create a comprehensive Python class for managing Neon database connections with:
- Connection pooling
- Automatic retry logic
- Query result caching
- Error handling"
```

### **In Python Scripts:**
```python
from anthropic import Anthropic
import os

# Configure
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Use Claude 3.5 Sonnet (default)
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ]
)

print(message.content[0].text)
```

---

## 🎯 Available Models

| Model | Best For | Context | Speed |
|-------|----------|---------|-------|
| `claude-3-5-sonnet-20241022` | General use (default) | 200K tokens | Fast |
| `claude-3-5-haiku-20241022` | Quick responses | 200K tokens | Very Fast |
| `claude-3-opus-20240229` | Complex reasoning | 200K tokens | Slower |
| `claude-3-sonnet-20240229` | Balanced (legacy) | 200K tokens | Fast |

**Default:** `claude-3-5-sonnet-20241022`

---

## 🔧 Troubleshooting

### **"claude: command not found"**
- Make sure you added the Scripts directory to PATH (should already be there)
- Restart your terminal
- Try: `python C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\claude.py "test"`

### **"ANTHROPIC_API_KEY not set"**
- Set the environment variable (see Step 2 above)
- Restart terminal after setting
- Verify: `echo $env:ANTHROPIC_API_KEY` (should show your key)

### **"API key invalid" or "Authentication failed"**
- Get a fresh key from https://console.anthropic.com/settings/keys
- Make sure you copied the entire key (starts with `sk-ant-`)
- Check your Anthropic account has credits/billing set up

### **"Rate limit exceeded"**
- You've hit Anthropic's rate limits
- Wait a few minutes or upgrade your plan
- Use `claude-3-5-haiku` for higher rate limits

---

## 📚 Advanced Usage

### **Streaming Responses:**
```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Your prompt"}]
) as stream:
    for text in stream.text_stream:
        print(text, end='')
```

### **With System Prompts:**
```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    system="You are a PostgreSQL database expert specializing in Neon databases.",
    messages=[
        {"role": "user", "content": "Explain connection pooling"}
    ]
)
```

### **Tool Use (Function Calling):**
```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=[{
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }]
)
```

---

## 🆚 Agent Comparison

| Feature | Claude | Gemini | Codex |
|---------|--------|--------|-------|
| **Best For** | Reasoning, analysis | General AI, free tier | Code generation |
| **Context** | 200K tokens | 1M tokens | 128K tokens |
| **Speed** | Fast | Very Fast | Fast |
| **Cost** | Pay-per-use | Free tier available | Pay-per-use |

**Use Claude for:** Complex reasoning, long analysis, code review  
**Use Gemini for:** Quick questions, free tier usage  
**Use Codex for:** Code generation, refactoring

---

**Setup Date:** 2025-11-03  
**Status:** ✅ Ready to use  
**Location:** `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\claude.py`

