# GenAI Dependency Decision Report

## Conflict Overview

Two different Google Gemini SDKs are used in this application:

| Module | SDK Package | Import Statement | File Location |
|--------|-------------|------------------|---------------|
| CAD Chatbot (Teammate) | `google-genai` | `from google import genai` | `backend/services/genai_service.py` |
| Diabetes Care Navigation (My domain) | `google-generativeai` | `import google.generativeai as genai` | `backend/services/diabetes/genai_service.py` |

## Analysis

### Teammate CAD Module
- Uses the **new** `google-genai` SDK (version 0.1.0+)
- Import pattern: `from google import genai` and `from google.genai import types`
- Located in: `backend/services/genai_service.py`
- This is the newer, recommended SDK from Google

### Diabetes Module
- Uses the **legacy** `google-generativeai` SDK (version 0.3.0+)
- Import pattern: `import google.generativeai as genai`
- Located in `backend/services/diabetes/genai_service.py`
- This SDK is still functional but Google recommends migrating to the new SDK

## Decision

**Both SDKs can coexist** in the same Python environment without conflict because:
1. They use different package names (`google-genai` vs `google-generativeai`)
2. They have separate import paths (`google.genai` vs `google.generativeai`)
3. Both are officially supported by Google

### Recommended Configuration

```env
# .env file
GEMINI_KEY=<your_api_key>  # Used by CAD module
DIABETES_GEMINI_KEY=<your_api_key>  # Can be same key or different
```

The same API key can be used for both modules if desired.

## Migration Option (Future)

If you want to unify to a single SDK, migrate the diabetes module to use `google-genai`:

### Pros of Migration
- Single dependency
- Newer SDK with better features
- Google's recommended approach

### Cons of Migration
- Requires code changes in `backend/services/diabetes/genai_service.py`
- Need to update prompt building and response handling
- Risk of breaking existing functionality

**Recommendation:** Keep both SDKs for now. Consider migration in a future iteration after testing.

## Manual Review Required

- [ ] Verify both SDKs install correctly together
- [ ] Test CAD chatbot functionality with `google-genai`
- [ ] Test diabetes care navigation with `google-generativeai`
- [ ] Decide if API keys should be shared or separate
- [ ] Optional: Plan migration of diabetes module to `google-genai`

## Files Affected

- `backend/services/genai_service.py` - Uses `google-genai` (teammate, DO NOT MODIFY)
- `backend/services/diabetes/genai_service.py` - Uses `google-generativeai` (diabetes module)
- `backend/config.py` - Added `DIABETES_GEMINI_KEY` setting
- `requirements.merged.txt` - Lists both packages

## Conclusion

**Decision:** Preserve teammate's `google-genai` usage AND use `google-generativeai` for diabetes module. Both SDKs can coexist safely. No forced migration required.
