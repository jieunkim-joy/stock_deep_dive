# 🚀 Streamlit Community Cloud Deployment Guide

This guide will help you deploy Stock Deep-Dive AI to Streamlit Community Cloud.

## Prerequisites

- ✅ GitHub account
- ✅ Streamlit Community Cloud account ([Sign up here](https://streamlit.io/cloud))
- ✅ Google Gemini API key (optional, for AI features)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [Streamlit Community Cloud](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click **"New app"** button
4. Fill in the deployment form:
   - **Repository**: Select `jieunkim-joy/stock_deep_dive` (or your repo)
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: (auto-generated, e.g., `stock-deep-dive-ai`)
5. Click **"Deploy"**

### 3. API Key Usage

**Important**: The app does not use Streamlit Secrets for API keys. Users must enter their Gemini API key manually in the sidebar each time they use the app.

- The API key is entered through the sidebar input field
- The key is never stored, hardcoded, or saved anywhere
- Each user must provide their own API key to use AI features

### 4. Access Your App

Your app will be available at:
```
https://[your-app-name].streamlit.app
```

## Project Structure for Cloud

Streamlit Cloud expects:
- ✅ `app.py` in the root directory (✓ Done)
- ✅ `requirements.txt` in the root directory (✓ Done)
- ✅ `packages.txt` (optional, for system packages) (✓ Done)
- ✅ `.streamlit/config.toml` (optional, for configuration) (✓ Done)

## Configuration Files

### `.streamlit/config.toml`
- Theme configuration
- Server settings
- Browser settings

### `requirements.txt`
- All Python dependencies
- Version pinned for stability

### `packages.txt`
- System-level packages (currently empty)
- Add packages like `git` if needed

## API Key Management

**Security-First Approach:**
- API keys are **never** stored in code, environment variables, or secrets
- Users must enter their Gemini API key manually in the sidebar
- The key is only used during the current session and is never persisted
- Each user is responsible for their own API key

## Troubleshooting

### App Won't Deploy

**Issue**: Import errors
- **Solution**: Check that all imports are correct and `requirements.txt` includes all dependencies

**Issue**: Module not found
- **Solution**: Ensure `stock/__init__.py` exists and imports are correctly set up

### API Key Not Working

**Issue**: API key not accepted
- **Solution**: 
  - Verify you've entered the correct API key in the sidebar
  - Ensure there are no extra spaces before/after the key
  - Check that the API key is valid and active
  - Verify you have API quota remaining

### Performance Issues

**Issue**: Slow loading times
- **Solution**:
  - Consider caching data using `@st.cache_data`
  - Reduce data collection period if needed
  - Optimize API calls

## Local Testing Before Deployment

Test your app locally to ensure it works:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Test with secrets (optional)
# Create .streamlit/secrets.toml:
# GEMINI_API_KEY = "your-key-here"
```

## Deployment Checklist

Before deploying, ensure:

- [ ] All dependencies are in `requirements.txt`
- [ ] `app.py` is in the root directory
- [ ] Imports work correctly (tested locally)
- [ ] **No hardcoded API keys in code** ✅ (Users enter manually)
- [ ] `.gitignore` excludes sensitive files
- [ ] README.md has deployment instructions
- [ ] Code is pushed to GitHub

## Post-Deployment

After deployment:

1. **Test the app**: Try different tickers and features
2. **Monitor logs**: Check for any errors in Streamlit Cloud dashboard
3. **Enter API key**: Users must enter their Gemini API key in the sidebar to use AI features
4. **Share your app**: Use the public URL to share with others

## Updating Your App

To update your deployed app:

1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update: description of changes"
   git push origin main
   ```
3. Streamlit Cloud will automatically detect changes and redeploy
4. Check the deployment status in the dashboard

## Support

For Streamlit Cloud specific issues:
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Community Forum](https://discuss.streamlit.io/)

For app-specific issues:
- Check the app logs in Streamlit Cloud dashboard
- Review error messages in the app interface
- Open an issue on GitHub

---

**Happy Deploying! 🎉**

