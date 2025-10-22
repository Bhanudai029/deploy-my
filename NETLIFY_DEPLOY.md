# Deploy Frontend to Netlify

This guide shows you how to deploy the YouTube Auto Downloader frontend to Netlify while keeping the backend on Sevalla.

## Architecture

- **Frontend (Netlify)**: Static HTML/CSS/JS served from `public/index.html`
- **Backend (Sevalla)**: Flask API running at `https://deploy-my-pro-840rq.sevalla.app`

## Deployment Steps

### 1. Push to GitHub

```bash
git add netlify.toml public/
git commit -m "Add Netlify frontend deployment"
git push origin main
```

### 2. Deploy to Netlify

#### Option A: Netlify CLI (Recommended)
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
netlify deploy --prod
```

#### Option B: Netlify Dashboard
1. Go to [https://app.netlify.com](https://app.netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Connect your GitHub repository
4. Configure build settings:
   - **Build command**: `mkdir -p public && cp templates/index.html public/index.html`
   - **Publish directory**: `public`
5. Click "Deploy site"

### 3. Update Backend CORS (Already Done!)

The Flask backend (`app.py`) already has CORS enabled for Netlify:

```python
CORS(app, resources={
    r"/*": {
        "origins": ["https://*.netlify.app", "http://localhost:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 4. Test Your Deployment

Once deployed, your Netlify URL will look like: `https://your-site-name.netlify.app`

Test the following:
- ✅ Download songs
- ✅ View progress
- ✅ List files from Supabase
- ✅ Delete files

## How It Works

1. **Frontend**: Netlify serves the static `index.html` 
2. **API Calls**: JavaScript makes requests to `https://deploy-my-pro-840rq.sevalla.app`
3. **CORS**: Backend allows requests from `*.netlify.app` domains
4. **Backend**: Sevalla processes downloads and uploads to Supabase

## Environment Variables

No environment variables needed on Netlify since it's just static HTML!

All secrets (YouTube API key, Supabase credentials) remain secure on your Sevalla backend.

## Benefits

✅ **Lightning Fast**: Netlify's global CDN serves your frontend  
✅ **Free Hosting**: Netlify free tier is generous  
✅ **Automatic HTTPS**: SSL certificates included  
✅ **Zero Config**: Just deploy and go  
✅ **Secure**: API keys stay on backend only

## Updating Frontend

When you update the UI:

```bash
# Edit templates/index.html
# Then copy to public/
cp templates/index.html public/index.html

# Push to GitHub
git add public/index.html
git commit -m "Update UI"
git push origin main

# Netlify auto-deploys from GitHub!
```

## Custom Domain (Optional)

In Netlify dashboard:
1. Go to "Domain settings"
2. Add custom domain
3. Update DNS records as instructed
4. Done! Your site will be at `yourdomain.com`

