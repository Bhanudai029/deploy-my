# 🚀 Quick Start Guide

## Installation & Testing

### Step 1: Install Dependencies
```bash
cd "C:\Users\baral\OneDrive\Desktop\yt final"
pip install groq==0.11.0
```

### Step 2: Start the Server
```bash
python app_web.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

### Step 3: Open in Browser
Navigate to: **http://localhost:5000**

---

## Testing the AI Integration

### Test 1: AI Music Discovery ✨

1. **Click** the "🤖 AI Music Discovery" tab
2. **Type** in the input: `Top 5 phonk songs`
3. **Click** "Ask AI" or press Enter
4. **Wait** for AI response (5-10 seconds)
5. **Observe:**
   - AI response appears with song list
   - Badge shows "5 songs detected"
   - Green download button appears
6. **Click** "🎧 Start Downloading These Songs"
7. **Result:** 
   - Automatically switches to Manual Search tab
   - Shows formatted song list
   - Searches YouTube for all songs
   - Displays video URLs

### Test 2: Content Filter 🛡️

1. **Try a non-music query:** `How to cook pasta`
2. **Expected:** AI rejects with message:
   > "I'm Sonnix, your music AI assistant! I can only help with music-related questions..."

### Test 3: Manual Search (Original Feature) 📝

1. **Click** "📝 Manual Search" tab
2. **Paste** in textarea:
   ```
   1. Shape of You
   2. See You Again
   3. Dream
   ```
3. **Click** "Search YouTube"
4. **Result:** Shows YouTube video URLs for each song

---

## Example Queries to Try

### Music Queries (Will Work):
- `Top 5 phonk songs`
- `Best Taylor Swift albums`
- `Recommend some 90s rock music`
- `Latest Ed Sheeran songs`
- `Top 10 jazz tracks`
- `Popular anime openings`

### Non-Music Queries (Will Be Rejected):
- `How to code in Python`
- `Best workout routines`
- `Healthy recipes`

---

## What to Look For

### ✅ Success Indicators:
- AI responds within 10 seconds
- Song format: "Song Name by Artist Name"
- Download button appears
- Song count badge shows correct number
- YouTube search finds videos

### ⚠️ Troubleshooting:

**If AI doesn't respond:**
```bash
# Check if groq is installed
pip show groq

# Check console for errors
# Look for error messages in terminal
```

**If songs aren't detected:**
- AI response must use "by" keyword
- Example: "Shape of You by Ed Sheeran"
- Check browser console (F12) for errors

**If SerpAPI fails:**
- AI will still work, just without current web info
- You have 250 searches/month limit
- Check: https://serpapi.com/dashboard

---

## File Structure

```
yt final/
├── groq_service.py          # NEW: AI service
├── song_parser.py            # NEW: Pattern recognition
├── app_web.py                # MODIFIED: Added AI endpoints
├── requirements.txt          # MODIFIED: Added groq
├── templates/
│   ├── index_with_ai.html   # NEW: AI-integrated UI
│   └── index_web.html       # OLD: Original UI (still available)
└── AI_INTEGRATION_README.md # NEW: Full documentation
```

---

## Quick Commands

### Test song parser independently:
```bash
python song_parser.py
```

### Check if APIs are accessible:
```bash
python -c "from groq_service import fetch_music_query_response; print('✅ Groq service loaded')"
```

### View app logs:
```bash
# Just run app_web.py and watch terminal output
python app_web.py
```

---

## Next Steps

1. ✅ **Test locally** - Follow the tests above
2. 🚀 **Deploy to production** - Update your Netlify/hosting
3. 📊 **Monitor usage** - Keep track of SerpAPI calls
4. 🎨 **Customize** - Adjust colors, add features

---

## Need Help?

Check `AI_INTEGRATION_README.md` for:
- Full architecture explanation
- API endpoint documentation
- Detailed troubleshooting guide
- Pattern recognition examples

---

**Happy testing! 🎵✨**
