"""
Test script to verify Google Gemini API key and LLM response.
Run this after updating .env with your actual API key.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def test_gemini_api():
    """Test the Gemini API connection and generate a sample response."""
    
    # Get API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    print("=" * 60)
    print("GEMINI API KEY TEST")
    print("=" * 60)
    
    # Check if API key exists
    if not api_key:
        print("\n❌ ERROR: GOOGLE_API_KEY not found in .env file")
        print("Please update the .env file with your actual API key.")
        return False
    
    # Check if it's still the placeholder
    if api_key == "your_google_api_key_here":
        print("\n❌ ERROR: API key is still the placeholder value")
        print("Please replace 'your_google_api_key_here' in .env with your actual key.")
        return False
    
    print(f"\n✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
    print(f"  Key length: {len(api_key)} characters")
    
    # Try to import google.genai
    try:
        from google import genai
        from google.genai import types
        print("\n✓ Google GenAI library imported successfully")
    except ImportError as e:
        print(f"\n❌ ERROR: Failed to import google.genai: {e}")
        print("Try installing: pip install google-genai")
        return False
    
    # Initialize client
    try:
        client = genai.Client(api_key=api_key)
        print("✓ Gemini client initialized successfully")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize Gemini client: {e}")
        return False
    
    # Test API call
    print("\n" + "-" * 60)
    print("TESTING API CALL...")
    print("-" * 60)
    
    try:
        # Using 'gemini-2.5-flash-native-audio-dialog' as it shows 'Unlimited' quota in your console
        # Standard models are returning RESOURCE_EXHAUSTED due to depleted credits
        response = client.models.generate_content(
            model="gemini-2.5-flash-native-audio-dialog",
            contents="Hello! This is a test message to verify the Gemini API is working. Please respond with 'API TEST SUCCESSFUL' and the current date."
        )
        
        if response and response.text:
            print("\n✓ API CALL SUCCESSFUL!")
            print("\nModel Response:")
            print("-" * 40)
            print(response.text)
            print("-" * 40)
            
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED - GEMINI API IS WORKING!")
            print("=" * 60)
            return True
        else:
            print("\n❌ ERROR: Empty response from API")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR during API call: {e}")
        print("\nPossible issues:")
        print("  1. Invalid API key (check for typos)")
        print("  2. API key not activated in Google Cloud Console")
        print("  3. Network connectivity issues")
        print("  4. API quota exceeded")
        return False


if __name__ == "__main__":
    success = test_gemini_api()
    exit(0 if success else 1)
