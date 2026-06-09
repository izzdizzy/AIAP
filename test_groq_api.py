"""
Test script for Groq API integration.
This script verifies your Groq API key and tests the LLM response.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("="*80)
print("GROQ API TEST")
print("="*80)

# Step 1: Check if GROQ_API_KEY is set
groq_api_key = os.environ.get("GROQ_API_KEY")

print("\n[Step 1] Checking GROQ_API_KEY in .env file...")
if groq_api_key:
    print(f"✓ GROQ_API_KEY found: {groq_api_key[:10]}...{groq_api_key[-5:]}")
    if groq_api_key == "your_groq_api_key_here":
        print("❌ ERROR: You need to replace 'your_groq_api_key_here' with your actual Groq API key!")
        print("\n📝 INSTRUCTIONS:")
        print("   1. Go to https://console.groq.com/keys")
        print("   2. Create a new API key (free, no credit card required)")
        print("   3. Copy the API key")
        print("   4. Edit the .env file and replace 'your_groq_api_key_here' with your actual key")
        print("   5. Run this test again")
        exit(1)
    else:
        print("✓ API key appears to be set correctly")
else:
    print("❌ ERROR: GROQ_API_KEY not found in .env file!")
    print("\n📝 INSTRUCTIONS:")
    print("   1. Go to https://console.groq.com/keys")
    print("   2. Create a new API key (free, no credit card required)")
    print("   3. Copy the API key")
    print("   4. Edit the .env file and add: GROQ_API_KEY=your_actual_key_here")
    print("   5. Run this test again")
    exit(1)

# Step 2: Test Groq library import
print("\n[Step 2] Testing Groq library import...")
try:
    from groq import Groq
    print("✓ Groq library imported successfully")
except ImportError as e:
    print(f"❌ ERROR: Failed to import Groq library: {e}")
    print("\n📝 INSTRUCTIONS:")
    print("   Run: pip install groq")
    exit(1)

# Step 3: Initialize Groq client
print("\n[Step 3] Initializing Groq client...")
try:
    client = Groq(api_key=groq_api_key)
    print("✓ Groq client initialized successfully")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Groq client: {e}")
    exit(1)

# Step 4: Make a test API call
print("\n[Step 4] Making test API call to Groq...")
print("   Model: llama-3.1-8b-instant")
print("   Request: Simple test message")

try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Please respond with just 'Groq API test successful!' if you can read this."}
        ],
        max_tokens=50,
        temperature=0.7
    )
    
    answer = response.choices[0].message.content.strip()
    print(f"\n✓ API call successful!")
    print(f"   Response: {answer}")
    
    # Show usage info
    if hasattr(response, 'usage'):
        print(f"   Tokens used: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"\n❌ ERROR during API call: {e}")
    print("\nPossible issues:")
    print("  1. Invalid API key (check for typos)")
    print("  2. API key not activated in Groq Console")
    print("  3. Network connectivity issues")
    print("  4. API quota exceeded")
    print("\n🔗 Check your Groq dashboard: https://console.groq.com/")
    exit(1)

# Step 5: Test with healthcare context (similar to gen_ai_assistant)
print("\n[Step 5] Testing with healthcare context (simulating gen_ai_assistant)...")
try:
    system_prompt = """You are a Care Navigation Assistant for chronic condition patients in Singapore.
Provide clear, empathetic recommendations in plain English (max 100 words)."""

    user_prompt = """PATIENT INFORMATION:
Readmission Risk Score: 0.65 (HIGH RISK)
Age: 72
CHAS Tier: Pioneer Generation
Has Diabetes: Yes
Has Hypertension: Yes

TASK: Provide a personalized care navigation recommendation."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )
    
    recommendation = response.choices[0].message.content.strip()
    print(f"\n✓ Healthcare context test successful!")
    print(f"\nGenerated Recommendation:\n{'-'*80}\n{recommendation}\n{'-'*80}")
    
except Exception as e:
    print(f"\n❌ ERROR during healthcare context test: {e}")
    exit(1)

print("\n" + "="*80)
print("✅ ALL TESTS PASSED!")
print("="*80)
print("\nYour Groq API key is working correctly!")
print("The Gen AI assistant will now use the LLM instead of falling back to rule-based.")
print("\nNext steps:")
print("  1. Run your main application")
print("  2. The gen_ai_assistant will use Groq's llama-3.1-8b-instant model")
print("  3. Enjoy faster responses with generous free tier limits!")
print("\n📊 Groq Free Tier Limits (approximate):")
print("   - llama-3.1-8b-instant: ~30 requests/minute, ~14,400 requests/day")
print("   - No credit card required")
print("   - Very fast inference speeds")
print("\n🔗 Groq Console: https://console.groq.com/")
