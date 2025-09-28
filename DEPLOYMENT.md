# Deployment Guide for Render

## Prerequisites
1. A Render account (free tier available)
2. Your OpenAI API key
3. Your code pushed to a Git repository (GitHub, GitLab, etc.)

## Deployment Steps

### 1. Prepare Your Repository
Make sure your repository contains all the necessary files:
- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `.streamlit/config.toml` - Streamlit configuration
- `runtime.txt` - Python version specification
- All other supporting files (`parsing.py`, `prompting.py`, `effective_scraper.py`)

### 2. Deploy on Render

#### Option A: Using render.yaml (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Blueprint"
3. Connect your Git repository
4. Render will automatically detect the `render.yaml` file and configure the service
5. Set the environment variable:
   - Go to your service settings
   - Add environment variable: `OPENAI_API_KEY` with your actual API key
6. Deploy!

#### Option B: Manual Configuration
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your Git repository
4. Configure the service:
   - **Name**: `ai-ate-equipment-system`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add environment variable:
   - Key: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
6. Click "Create Web Service"

### 3. Environment Variables
Make sure to set the following environment variable in Render:
- `OPENAI_API_KEY`: Your OpenAI API key

### 4. Deployment Notes
- The app will be available at `https://your-app-name.onrender.com`
- Free tier has limitations: service sleeps after 15 minutes of inactivity
- First request after sleep may take 30-60 seconds to wake up
- Consider upgrading to paid tier for production use

### 5. Troubleshooting
- If deployment fails, check the build logs in Render dashboard
- Ensure all dependencies are listed in `requirements.txt`
- Verify your OpenAI API key is valid and has sufficient credits
- Check that all import paths are correct

### 6. Post-Deployment
- Test all functionality on the deployed app
- Monitor logs for any errors
- Set up custom domain if needed (paid tier)
- Configure auto-scaling if required (paid tier)

## Security Notes
- Never commit API keys to your repository
- Use environment variables for sensitive data
- Consider using Render's secret management for production 