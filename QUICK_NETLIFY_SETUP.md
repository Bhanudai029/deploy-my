# 🚀 Quick Netlify Setup (5 Minutes!)

## Step 1: Go to Netlify
Visit: **https://app.netlify.com**

## Step 2: Deploy Your Site

### Option A: Drag & Drop (Fastest!)
1. Click "Add new site" → "Deploy manually"
2. Drag the **`public`** folder from your project
3. Done! Your site is live! 🎉

### Option B: Connect GitHub (Auto-Deploy)
1. Click "Add new site" → "Import an existing project"
2. Choose "GitHub"
3. Select repository: **`Bhanudai029/deploy-my`**
4. Configure:
   - **Build command**: `mkdir -p public && cp templates/index.html public/index.html`
   - **Publish directory**: `public`
5. Click "Deploy site"
6. Wait ~1 minute
7. Your site is live! 🎉

## Step 3: Get Your Netlify URL
You'll get a URL like: **`https://magical-unicorn-123abc.netlify.app`**

## Step 4: Update Sevalla Backend (IMPORTANT!)
1. Go to Sevalla dashboard
2. Add environment variable or update `app.py` CORS to include your Netlify URL:
   ```python
   "origins": ["https://magical-unicorn-123abc.netlify.app", "https://*.netlify.app"]
   ```
3. Redeploy Sevalla

## Step 5: Test!
Visit your Netlify URL and:
- ✅ Paste some songs
- ✅ Click "Start Download"
- ✅ Watch the magic happen!

## 🎨 Custom Domain (Optional)
1. In Netlify: "Domain settings" → "Add custom domain"
2. Follow DNS setup instructions
3. Your site will be at `yourdomain.com` 🔥

## 🔄 Auto-Updates
When you push to GitHub:
1. Sevalla auto-redeploys backend
2. Netlify auto-redeploys frontend
3. Everything stays in sync! ✨

---

**That's it!** Your frontend is now blazing fast on Netlify's global CDN while your backend runs securely on Sevalla! 🚀

