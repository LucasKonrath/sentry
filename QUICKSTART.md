# 🚀 Quick Start Guide - On-Demand PR Coverage Analysis

## Ready-to-Deploy Solution

Your PR Coverage Analyzer is now configured for **on-demand execution** whenever PRs are created in targeted repositories. Here are your deployment options:

## 🎯 Option 1: GitHub Actions (Easiest)

### For Single Repository
Copy this workflow to any repository you want to monitor:

```bash
# Copy the template workflow
cp .github/workflows/pr-coverage-template.yml target-repo/.github/workflows/pr-coverage-analysis.yml
```

### Required Secrets in Target Repository:
- `OPENAI_API_KEY` - Your OpenAI API key
- `COVERAGE_ANALYZER_TOKEN` - GitHub token with repo access

### Triggers Automatically When:
- ✅ New PR opened
- ✅ PR updated/synchronized  
- ✅ PR reopened

---

## 🐳 Option 2: Self-Hosted Webhook Server

### Quick Deploy with Docker:
```bash
# 1. Configure environment
cp config/production.env .env
# Edit .env with your tokens

# 2. Deploy with Docker Compose
./deploy.sh compose

# 3. Configure webhook in GitHub repos:
# URL: https://your-server.com/webhook
# Events: Pull requests
# Content-type: application/json
```

### Available Endpoints:
- `GET /health` - Health check
- `POST /webhook` - GitHub webhook handler  
- `GET /repos` - List configured repositories
- `POST /trigger` - Manual analysis trigger

---

## ⚡ Option 3: Serverless (AWS Lambda/Vercel)

Deploy as serverless function for zero-maintenance scaling:

```bash
# AWS Lambda deployment
# See docs/on_demand_setup.md for detailed instructions
```

---

## 🔧 Configuration

### Target Repositories
Edit `config/target_repos.yml`:

```yaml
repositories:
  - owner: myorg
    name: backend-api
    settings:
      coverage_threshold: 85
      languages: [python, javascript]
      
  - owner: myorg
    name: frontend-app  
    settings:
      coverage_threshold: 75
      languages: [typescript, javascript]
```

### Environment Variables
```bash
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk_your_key_here
TARGET_REPOS=myorg/repo1,myorg/repo2
COVERAGE_THRESHOLD=80
```

---

## 🎬 How It Works

1. **PR Created** → Webhook triggered automatically
2. **Analysis Runs** → Coverage analyzed, gaps identified
3. **Tests Generated** → LLM creates comprehensive tests
4. **New PR Created** → Automated PR with generated tests
5. **Results Posted** → Comments added to original PR

---

## 🚀 Deploy Now

### Local Development:
```bash
./deploy.sh development
```

### Production Docker:
```bash  
./deploy.sh production
```

### Test the Setup:
```bash
# Test webhook endpoint
curl -X GET http://localhost:5000/health

# Check configured repos  
curl http://localhost:5000/repos
```

---

## 📊 What You Get

### ✅ **Automatic Monitoring**
- Watches all configured repositories
- Triggers on every PR automatically
- Skips drafts and non-target repos

### 🤖 **Intelligent Analysis**  
- Identifies uncovered functions/methods
- Prioritizes by complexity and importance
- Generates comprehensive test suites

### 📝 **Seamless Integration**
- Creates new PRs with generated tests
- Posts progress comments on original PR
- Provides coverage improvement metrics

### 🔧 **Flexible Configuration**
- Per-repository settings
- Language-specific analysis
- Customizable coverage thresholds

---

## 🆘 Need Help?

- 📚 **Documentation:** `/docs` folder contains detailed guides
- 🐛 **Issues:** Check logs in `/logs` directory  
- ⚙️ **Configuration:** See `/config` for examples
- 🔧 **Customization:** Modify LLM prompts in `/src/generators`

**Your PR Coverage Analyzer is production-ready and waiting to improve your codebase! 🎉**
