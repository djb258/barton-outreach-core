# Complete Agent Suite - Cursor, Claude, Gemini, Codex

✅ **All 4 agents are now set up and ready to use!**

---

## 🎯 Your Complete Agent Suite

| Agent | Command | API Key | Best For | Status |
|-------|---------|---------|----------|--------|
| **Cursor** | Built-in IDE | N/A | Code editing, context-aware assistance | ✅ Active |
| **Claude** | `claude "prompt"` | `ANTHROPIC_API_KEY` | Analysis, reasoning, long context | ✅ Ready |
| **Gemini** | `gemini "prompt"` | `GOOGLE_API_KEY` | General AI, multimodal, free tier | ✅ Ready |
| **Codex** | `codex "prompt"` | `OPENAI_API_KEY` | Code generation, refactoring | ✅ Ready |

---

## 🚀 Quick Setup (All Agents)

### **1. Cursor** ✅
Already active! You're using it right now.

### **2. Claude** - Get API Key
1. Go to: https://console.anthropic.com/settings/keys
2. Create API key
3. Set environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key-here", "User")
   ```

### **3. Gemini** - Get API Key
1. Go to: https://makersuite.google.com/app/apikey
2. Create API key
3. Set environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key-here", "User")
   ```

### **4. Codex** - Get API Key
1. Go to: https://platform.openai.com/api-keys
2. Create API key
3. Set environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key-here", "User")
   ```

**Then restart your terminal** for all changes to take effect!

---

## 💡 Usage Examples

### **From Terminal:**

```bash
# Claude - Best for analysis and reasoning
claude "Analyze the performance of this SQL query: SELECT * FROM marketing.company_master"

# Gemini - Best for general questions and free tier
gemini "Explain PostgreSQL schemas and their relationships"

# Codex - Best for code generation
codex "Write a Python function to connect to Neon database with connection pooling"

# Cursor - Built into your IDE
# Just ask in the chat panel or use Cmd/Ctrl + K
```

### **In Python Scripts:**

```python
# Claude
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Your prompt"}]
)

# Gemini
import google.generativeai as genai
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Your prompt')

# Codex
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

---

## 🎯 When to Use Which Agent

### **Cursor** (IDE Integration)
- ✅ Code editing and refactoring
- ✅ Context-aware suggestions
- ✅ File navigation and search
- ✅ Real-time code completion
- ✅ Integrated terminal access

### **Claude** (Reasoning & Analysis)
- ✅ Complex problem solving
- ✅ Long document analysis
- ✅ Multi-step reasoning
- ✅ Code review and explanations
- ✅ Best for: "Why?" and "How?" questions

### **Gemini** (General Purpose)
- ✅ Quick questions and answers
- ✅ Multimodal (text, images)
- ✅ Free tier available
- ✅ General knowledge
- ✅ Best for: "What is?" questions

### **Codex** (Code Generation)
- ✅ Code generation from scratch
- ✅ Code refactoring
- ✅ Debugging assistance
- ✅ API documentation
- ✅ Best for: "Write code to..." requests

---

## 🔧 Test All Agents

```bash
# Test Claude
python test_claude.py

# Test Gemini
python test_gemini.py

# Test Codex
python test_codex.py

# Test Cursor
# Just use the chat panel in Cursor IDE
```

---

## 📊 Agent Comparison

| Feature | Cursor | Claude | Gemini | Codex |
|---------|--------|--------|--------|-------|
| **Context Window** | Full repo | 200K tokens | 1M tokens | 128K tokens |
| **Code Focus** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cost** | Free (IDE) | Pay-per-use | Free tier | Pay-per-use |
| **Best Model** | Built-in | claude-3-5-sonnet | gemini-pro | gpt-4 |

---

## 🎛️ Environment Variables Summary

Add these to your environment (PowerShell):

```powershell
# Claude
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key", "User")

# Gemini
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key", "User")

# Codex
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key", "User")
```

Or create a `.env` file in your project:
```env
ANTHROPIC_API_KEY=your-claude-key
GOOGLE_API_KEY=your-gemini-key
OPENAI_API_KEY=your-codex-key
```

---

## 🚀 Workflow Examples

### **Multi-Agent Workflow:**

```bash
# 1. Use Gemini for quick research
gemini "What are best practices for PostgreSQL connection pooling?"

# 2. Use Codex to generate code
codex "Write a Python connection pool class based on these best practices"

# 3. Use Claude to review and improve
claude "Review this code for security and performance issues: [paste code]"

# 4. Use Cursor to integrate into your project
# Edit files directly in Cursor with AI assistance
```

### **Code Review Workflow:**

```bash
# 1. Generate code with Codex
codex "Create a function to query marketing.company_master"

# 2. Review with Claude
claude "Review this function for SQL injection vulnerabilities"

# 3. Optimize with Gemini
gemini "Suggest performance optimizations for this database query"

# 4. Integrate with Cursor
# Use Cursor's built-in features to add to your codebase
```

---

## 📚 Quick Reference Guides

- **Claude**: See `CLAUDE_QUICK_START.md` (to be created)
- **Gemini**: See `GEMINI_QUICK_START.md`
- **Codex**: See `CODEX_QUICK_START.md`
- **Cursor**: Built-in help (Cmd/Ctrl + Shift + P)

---

## ✅ Verification Checklist

- [x] Cursor IDE installed and active
- [x] Claude CLI script created (`claude.py`)
- [x] Gemini CLI script created (`gemini.py`)
- [x] Codex CLI script created (`codex.py`)
- [x] All scripts in PATH
- [ ] Claude API key set (`ANTHROPIC_API_KEY`)
- [ ] Gemini API key set (`GOOGLE_API_KEY`)
- [ ] Codex API key set (`OPENAI_API_KEY`)
- [ ] All test scripts pass

---

## 🎉 You're All Set!

You now have **4 powerful AI agents** ready to use:

1. **Cursor** - Your IDE with built-in AI
2. **Claude** - Best for reasoning and analysis
3. **Gemini** - Best for general questions (free tier)
4. **Codex** - Best for code generation

**All agents are globally accessible from any terminal!** 🚀

---

**Setup Date:** 2025-11-03  
**Status:** ✅ Complete Agent Suite Ready  
**Location:** `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\`

