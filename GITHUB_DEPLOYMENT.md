# GitHub Deployment Guide
# SmartLead Variant Performance Analyzer

This guide walks you through deploying the SmartLead Variant Performance Analyzer to GitHub and Streamlit Community Cloud.

## Prerequisites

Before starting deployment, ensure you have:
- GitHub account with appropriate permissions
- Streamlit Community Cloud account (sign up at https://streamlit.io/cloud)
- SmartLead API key (available from your SmartLead dashboard)
- Git installed on your local machine

## Step 1: Create GitHub Repository

### Option A: Using GitHub Web Interface

1. Go to https://github.com/new
2. Configure your repository:
   - **Repository name**: `smartlead-variant-analyzer` (or your preferred name)
   - **Description**: SmartLead Variant Performance Analyzer - Analyze email campaign performance
   - **Visibility**: Private (recommended) or Public
   - **Initialize with**: DO NOT check any options (README, .gitignore, or license)
3. Click "Create repository"

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Create repository
gh repo create smartlead-variant-analyzer --private --description "SmartLead Variant Performance Analyzer" --source=.
```

## Step 2: Push Code to GitHub

### If you just created the repository:

```bash
# Navigate to your project directory
cd /home/ubuntu/variant-performance-analyzer

# Add the remote repository (replace with your actual repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Rename branch to 'main' (optional but recommended)
git branch -M main

# Push to GitHub
git push -u origin main
```

### If the repository already exists:

```bash
# Just push the code
git push -u origin main
```

## Step 3: Deploy to Streamlit Community Cloud

### 3.1 Connect Your GitHub Repository

1. Go to https://share.streamlit.io
2. Click "Sign in" and authenticate with your GitHub account
3. Click "New app" button
4. Configure your app:
   - **Repository**: Select your `smartlead-variant-analyzer` repository
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click "Deploy"

### 3.2 Configure Environment Secrets

During deployment, you'll be prompted to configure secrets. Add the following:

1. In the "Secrets" section, click "Add secret"
2. Add your SmartLead API key:
   - **Secret name**: `SMARTLEAD_API_KEY`
   - **Value**: Your actual SmartLead API key
   - Click "Add"

### 3.3 Complete Deployment

1. Review your configuration
2. Click "Deploy" button
3. Wait for Streamlit to build and deploy (typically 1-2 minutes)
4. Your app will be available at: `https://your-app-name.streamlit.app`

## Step 4: Post-Deployment Verification

### 4.1 Basic Functionality Check

Once deployed, verify the following:

1. **App Loads Successfully**
   - Visit your Streamlit app URL
   - The app should display the main interface without errors

2. **API Connection Works**
   - Enter a campaign ID in the input field
   - Click "Load Campaign Data"
   - Verify no API authentication errors appear

3. **Data Display**
   - Campaign summary should display correctly
   - Variant comparison table should appear
   - Charts should render properly

### 4.2 Performance Verification

1. Load a campaign with multiple variants
2. Verify all metrics are calculated correctly
3. Check that charts render without errors
4. Test the CSV download functionality

### 4.3 Common Deployment Issues

#### Issue: "Module not found" errors
- **Solution**: Verify `requirements.txt` is in the repository root
- **Check**: All dependencies are listed in requirements.txt

#### Issue: API authentication errors
- **Solution**: Verify `SMARTLEAD_API_KEY` secret is set correctly in Streamlit Cloud
- **Check**: The secret name matches exactly (case-sensitive)

#### Issue: App won't load
- **Solution**: Check deployment logs in Streamlit Cloud dashboard
- **Check**: Verify `app.py` is in the repository root

#### Issue: Charts not displaying
- **Solution**: Verify plotly is in requirements.txt
- **Check**: Browser console for JavaScript errors

## Step 5: Maintenance and Updates

### Updating Your Application

1. Make changes locally
2. Commit changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```
3. Push to GitHub:
   ```bash
   git push
   ```
4. Streamlit Cloud will automatically redeploy

### Updating API Keys

If you need to update your API key:
1. Go to your Streamlit Cloud app dashboard
2. Navigate to "Settings" > "Secrets"
3. Update the `SMARTLEAD_API_KEY` value
4. Your app will automatically restart with the new key

### Monitoring Deployment Logs

1. Go to your Streamlit Cloud app dashboard
2. Click on your app
3. Navigate to "Logs" tab
4. Monitor for errors or warnings

## Security Best Practices

1. **Never Commit Secrets**: The `.gitignore` file excludes `.streamlit/secrets.toml` to prevent accidentally committing API keys
2. **Use Environment Variables**: Always use Streamlit Cloud secrets for sensitive data
3. **Private Repository**: Keep your repository private if it contains any sensitive configuration
4. **Regular Updates**: Keep dependencies updated for security patches
5. **API Key Rotation**: Periodically rotate your SmartLead API key

## Troubleshooting

### Check Deployment Status

```bash
# Verify git status
git status

# View recent commits
git log --oneline -5

# Check remote configuration
git remote -v
```

### Verify Repository Contents

```bash
# List all tracked files
git ls-files

# Verify .gitignore is working
git check-ignore -v .streamlit/secrets.toml
```

### Streamlit Cloud Deployment Logs

Access logs through:
1. Streamlit Cloud dashboard
2. Your app > "Logs" tab
3. Filter by: "Manager", "User", or "All"

## Additional Resources

- **Streamlit Documentation**: https://docs.streamlit.io
- **Streamlit Cloud Guide**: https://docs.streamlit.io/streamlit-cloud
- **SmartLead API Documentation**: Check your SmartLead dashboard
- **GitHub Documentation**: https://docs.github.com

## Next Steps

After successful deployment:

1. **Share Your App**: Share the Streamlit app URL with your team
2. **Monitor Usage**: Use Streamlit Cloud's built-in analytics
3. **Collect Feedback**: Gather user feedback for improvements
4. **Plan Enhancements**: Review the development plan for future features

## Support

If you encounter issues during deployment:

1. Check the troubleshooting section above
2. Review Streamlit Cloud deployment logs
3. Verify all secrets are configured correctly
4. Ensure all dependencies are in requirements.txt

---

**Deployment Status**: Ready for deployment
**Last Updated**: 2026-01-29
**Version**: 1.0.0
