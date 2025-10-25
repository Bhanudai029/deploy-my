# 10-Song Limit Enforcement System

## Overview
This system enforces a strict maximum of 10 songs per search/download request to prevent abuse and manage API costs (SerpAPI usage).

## Protection Layers

### 1. **Frontend UI Warning** ✅
- **Location**: `public/index.html`
- **Features**:
  - Prominent yellow warning banner at top of page
  - Warning messages in both AI and manual input sections
  - Clear messaging: "This limit cannot be bypassed"

### 2. **Frontend Validation** ✅
- **Location**: `public/index.html` (JavaScript)
- **Manual Input**: 
  - Counts lines in textarea
  - Rejects if > 10 songs
  - Shows error toast with exact count
- **AI Detection**:
  - Limits detected songs to first 10
  - Shows info toast if more than 10 detected

### 3. **Backend Validation** ✅
- **Location**: `app.py` (line 81-85)
- **Features**:
  - Parses and counts submitted songs
  - Returns 400 error if > 10 songs
  - Error message shows exact count

### 4. **AI Prompt Enforcement** ✅
- **Location**: `groq_service.py` (line 163-171)
- **Features**:
  - System instruction explicitly states 10-item maximum
  - Instructions to detect bypass attempts
  - Auto-caps any request > 10 to 10 items

### 5. **Bypass Detection** ✅ NEW!
- **Location**: `number_parser.py` (NEW FILE)
- **Detects**:
  - Math expressions: "5+5", "10+10", "5 plus 5"
  - Text numbers: "twenty", "fifty", "top fifteen"
  - Mixed formats: "5 plus five"
  - Multiple numbers: "5 and 5"
- **Location**: `groq_service.py` (line 316-323)
- **Features**:
  - Parses user query for numeric bypass attempts
  - Adds warning message if > 10 requested
  - Warning appears in AI response

## Bypass Scenarios Handled

| Bypass Attempt | Detection | Result |
|----------------|-----------|--------|
| "Top 5+5 songs" | ✅ Math parser | Detected as 10, allowed |
| "Top 5+45 songs" | ✅ Math parser | Detected as 50, shows warning, caps at 10 |
| "Top twenty songs" | ✅ Text-to-number | Detected as 20, shows warning, caps at 10 |
| "Top fifty songs" | ✅ Text-to-number | Detected as 50, shows warning, caps at 10 |
| "5 plus 5 songs" | ✅ Mixed parser | Detected as 10, allowed |
| Manual 15 lines | ✅ Frontend count | Rejected with error message |
| Backend 15 songs | ✅ Backend validation | Returns 400 error |

## Warning Messages

### Frontend UI
- **Banner**: "System Limit - Maximum 10 songs per search and download. This limit cannot be bypassed."
- **AI Section**: "⚠️ Requests for more than 10 songs will be automatically limited to 10"
- **Manual Section**: "⚠️ Maximum 10 songs allowed - additional songs will be rejected"

### AI Response (when bypass detected)
```
⚠️ SYSTEM NOTICE: You requested {N} items, but the system is limited to 
maximum 10 searches and downloads per request. Providing 10 items.
```

### Frontend Toast Messages
- **Manual > 10**: "❌ Maximum 10 songs allowed! You entered {N} songs. Please remove {N-10} songs."
- **AI > 10**: "⚠️ Limiting to first 10 songs (detected {N}, max is 10)"

### Backend Error
```json
{
  "error": "Maximum 10 songs allowed. You provided {N} songs. Please limit to 10 songs or less."
}
```

## Technical Implementation

### Dependencies
```
word2number==1.1  # Text number to digit conversion
```

### Key Functions
1. `extract_number_from_text()` - Parses math/text numbers
2. `normalize_query_for_counting()` - Normalizes queries for counting
3. Frontend validation in `startDownload()` and `downloadFromAI()`
4. Backend validation in `/download` endpoint
5. AI prompt enforcement in `build_system_instruction()`

## Testing Bypass Attempts

Try these to verify protection:
- ❌ "Top 5+45 songs" → Should show warning, return 10
- ❌ "Best twenty songs" → Should show warning, return 10  
- ❌ "Top fifty tracks" → Should show warning, return 10
- ✅ "Top 5+5 songs" → Should work (exactly 10)
- ✅ "Top 5 songs" → Should work (under 10)

## Deployment Status

✅ **Frontend**: Deployed to Netlify (https://sonnixmusicsadder.netlify.app/)
⏳ **Backend**: Needs redeployment to Sevalla to activate number parsing

## Next Steps

1. **Redeploy Backend to Sevalla**
   - Backend needs to be redeployed to include `number_parser.py` and updated `groq_service.py`
   - This will activate the bypass detection on the AI side

2. **Test All Scenarios**
   - Test math expressions
   - Test text numbers
   - Test manual input > 10
   - Verify AI responses cap at 10

## Security Notes

- Multiple layers ensure protection even if one fails
- Frontend UX clearly communicates limits
- Backend enforces limits server-side (can't be bypassed by modifying frontend)
- AI has hard-coded limit in system prompt
- Numeric parser caps at 250 to prevent integer overflow attacks
