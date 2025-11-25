# Gemini Global Terminal Setup - Quick Start

✅ **Setup Complete!** Gemini CLI is installed and ready.

---

## 🚀 Quick Setup (2 Steps)

### **Step 1: Get Your API Key**

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### **Step 2: Set Environment Variable**

**For PowerShell (Permanent):**
```powershell
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-api-key-here", "User")
```

**For Current Session Only:**
```powershell
$env:GOOGLE_API_KEY="your-api-key-here"
```

**Then restart your terminal** for permanent changes to take effect.

---

## 📍 Add Script to PATH

The Gemini CLI is installed at:
```
C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts
```

**To use `gemini` command globally, add to PATH:**

**PowerShell (Permanent):**
```powershell
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$newPath = "$currentPath;C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts"
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")
```

**Or manually:**
1. Press `Win + R` → type `sysdm.cpl` → Enter
2. Go to "Advanced" tab → "Environment Variables"
3. Under "User variables", find "Path" → Edit
4. Click "New" → Add: `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts`
5. Click OK on all dialogs
6. **Restart terminal**

---

## ✅ Test It Works

```powershell
# Test 1: Check if gemini command is available
gemini --help

# Test 2: Run a simple query
gemini "Say hello in one sentence"

# Test 3: Test script
python test_gemini.py
```

---

## 💡 Usage Examples

### **From Terminal:**
```bash
# Basic query
gemini "What is PostgreSQL?"

# Code generation
gemini "Write a Python function to connect to Neon database"

# Analysis
gemini "Explain this SQL: SELECT * FROM marketing.company_master"

# Multi-line prompts (use quotes)
gemini "Analyze the barton-outreach-core repository structure and suggest improvements"
```

### **In Python Scripts:**
```python
import os
import google.generativeai as genai

# Configure
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Use
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Your prompt here')
print(response.text)
```

---

## 🔧 Troubleshooting

### **"gemini: command not found"**
- Make sure you added the Scripts directory to PATH
- Restart your terminal after adding to PATH
- Try: `python C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\gemini.py "test"`

### **"GOOGLE_API_KEY not set"**
- Set the environment variable (see Step 2 above)
- Restart terminal after setting
- Verify: `echo $env:GOOGLE_API_KEY` (should show your key)

### **"API key invalid"**
- Get a fresh key from https://makersuite.google.com/app/apikey
- Make sure you copied the entire key (no spaces)

---

## 📚 Advanced Usage

### **Different Models:**
```python
# Gemini Pro (default)
model = genai.GenerativeModel('gemini-pro')

# Gemini Pro Vision (for images)
model = genai.GenerativeModel('gemini-pro-vision')

# Gemini 1.5 Flash (faster, cheaper)
model = genai.GenerativeModel('gemini-1.5-flash')
```

### **Streaming Responses:**
```python
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Your prompt', stream=True)

for chunk in response:
    print(chunk.text, end='')
```

### **With Context/History:**
```python
chat = model.start_chat(history=[])
response = chat.send_message("Hello!")
response = chat.send_message("What did I just say?")
```

---

**Setup Date:** 2025-11-03  
**Status:** ✅ Ready to use  
**Location:** `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\gemini.py`

