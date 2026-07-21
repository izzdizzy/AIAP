"""
Gen AI Evaluation Script for Hospital Readmission Predictor
============================================================

This script evaluates the Gen AI Care Navigation Assistant by testing it against
20 sample patient scenarios with varying risk levels and symptoms. It prints the
prompt vs response to evaluate quality, relevance, and Singapore-context adherence.

Usage:
    python eval_gen_ai.py

Note: Requires GEMINI_API_KEY environment variable to be set. If API is unavailable,
      the script will demonstrate the fallback templates instead.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

from gen_ai import CareNavigationAssistant


# =============================================================================
# SAMPLE PATIENT SCENARIOS FOR EVALUATION
# =============================================================================

SAMPLE_SCENARIOS = [
    # LOW RISK SCENARIOS (Score < 0.33)
    {
        "id": 1,
        "risk_score": 0.15,
        "symptoms": ["Fatigue"],
        "question": "What should I do for follow-up?",
        "expected_context": "Routine monitoring, Healthier SG GP, CHAS clinic"
    },
    {
        "id": 2,
        "risk_score": 0.20,
        "symptoms": ["Frequent urination", "Excessive thirst"],
        "question": "Are these symptoms normal for diabetes?",
        "expected_context": "Standard diabetes management, routine care"
    },
    {
        "id": 3,
        "risk_score": 0.25,
        "symptoms": ["Blurred vision"],
        "question": "Should I see a specialist?",
        "expected_context": "Routine eye exam, GP referral if persistent"
    },
    {
        "id": 4,
        "risk_score": 0.30,
        "symptoms": ["Dry skin", "Slow-healing sores"],
        "question": "How do I manage these skin issues?",
        "expected_context": "Skin care tips, monitor for infection, GP visit"
    },
    {
        "id": 5,
        "risk_score": 0.18,
        "symptoms": [],
        "question": "I feel fine. Do I still need check-ups?",
        "expected_context": "Preventive care importance, regular screening"
    },
    
    # MODERATE RISK SCENARIOS (Score 0.33-0.66)
    {
        "id": 6,
        "risk_score": 0.40,
        "symptoms": ["Fatigue", "Tingling in hands/feet"],
        "question": "My hands feel numb sometimes. Is this serious?",
        "expected_context": "Increased surveillance, polyclinic review, neuropathy check"
    },
    {
        "id": 7,
        "risk_score": 0.45,
        "symptoms": ["Frequent infections", "Slow-healing sores"],
        "question": "I keep getting infections. What should I do?",
        "expected_context": "Earlier appointment, medication review, wound care"
    },
    {
        "id": 8,
        "risk_score": 0.50,
        "symptoms": ["Increased hunger", "Unexplained weight loss"],
        "question": "Why am I losing weight despite eating more?",
        "expected_context": "Care plan review, blood glucose monitoring, GP consultation"
    },
    {
        "id": 9,
        "risk_score": 0.55,
        "symptoms": ["Nausea", "Dizziness"],
        "question": "I feel dizzy and nauseous frequently.",
        "expected_context": "Prompt medical attention, possible medication adjustment"
    },
    {
        "id": 10,
        "risk_score": 0.60,
        "symptoms": ["Shortness of breath", "Swelling in legs"],
        "question": "My legs are swollen and I'm short of breath.",
        "expected_context": "Polyclinic visit, cardiovascular assessment"
    },
    {
        "id": 11,
        "risk_score": 0.35,
        "symptoms": ["Headache", "Vision changes"],
        "question": "I have headaches and my vision seems blurry.",
        "expected_context": "Blood pressure check, eye examination, GP follow-up"
    },
    {
        "id": 12,
        "risk_score": 0.65,
        "symptoms": ["Chest pain", "Shortness of breath"],
        "question": "I have chest discomfort when walking.",
        "expected_context": "Urgent medical evaluation, cardiac assessment"
    },
    
    # HIGH RISK SCENARIOS (Score > 0.66)
    {
        "id": 13,
        "risk_score": 0.75,
        "symptoms": ["Chest pain", "Shortness of breath", "Dizziness"],
        "question": "I have chest pain and trouble breathing. What should I do?",
        "expected_context": "Immediate intervention, A&E or 995, urgent care"
    },
    {
        "id": 14,
        "risk_score": 0.80,
        "symptoms": ["Confusion", "Severe fatigue", "Vomiting"],
        "question": "I feel confused and very sick.",
        "expected_context": "Emergency care, possible diabetic ketoacidosis"
    },
    {
        "id": 15,
        "risk_score": 0.85,
        "symptoms": ["Slow-healing sores", "Vision changes", "Tingling in hands/feet"],
        "question": "Multiple complications - what's the priority?",
        "expected_context": "Urgent comprehensive assessment, specialist referrals"
    },
    {
        "id": 16,
        "risk_score": 0.90,
        "symptoms": ["Chest pain", "Loss of consciousness history"],
        "question": "I fainted yesterday and have chest pain.",
        "expected_context": "Call 995 immediately, life-threatening emergency"
    },
    {
        "id": 17,
        "risk_score": 0.70,
        "symptoms": ["Persistent vomiting", "Abdominal pain"],
        "question": "Can't keep food down, stomach hurts badly.",
        "expected_context": "Urgent care, possible diabetic ketoacidosis screening"
    },
    {
        "id": 18,
        "risk_score": 0.95,
        "symptoms": ["Difficulty breathing", "Confusion", "Chest pain"],
        "question": "Having trouble breathing and thinking clearly.",
        "expected_context": "Call 995 now, critical emergency"
    },
    
    # EDGE CASES
    {
        "id": 19,
        "risk_score": 0.50,
        "symptoms": ["Irritability", "Headache"],
        "question": "Just feeling irritable lately. Could it be diabetes?",
        "expected_context": "Blood glucose monitoring, stress management, GP discussion"
    },
    {
        "id": 20,
        "risk_score": 0.33,
        "symptoms": ["Frequent urination"],
        "question": "Only symptom is frequent urination. Should I worry?",
        "expected_context": "Common diabetes symptom, schedule GP appointment for testing"
    },
]


def evaluate_gen_ai():
    """
    Evaluate the Gen AI assistant against all sample scenarios.
    Prints prompt, response, and evaluation notes for each scenario.
    """
    print("=" * 80)
    print("GEN AI CARE NAVIGATION ASSISTANT - EVALUATION REPORT")
    print("=" * 80)
    print(f"\nTotal Scenarios: {len(SAMPLE_SCENARIOS)}")
    print(f"API Key Available: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("\n⚠️  WARNING: GEMINI_API_KEY not found. Testing FALLBACK TEMPLATES only.")
        print("=" * 80)
    
    # Initialize assistant (will use fallback if API key missing)
    try:
        if api_key:
            assistant = CareNavigationAssistant(api_key=api_key)
            print(f"\n✓ CareNavigationAssistant initialized with Gemini API")
        else:
            # Create a mock assistant that uses only fallbacks
            class FallbackAssistant:
                def generate_advice(self, patient_symptoms, ml_risk_score, risk_category=None, **kwargs):
                    # Simulate the fallback behavior
                    severity_score = int(ml_risk_score * 100)
                    if ml_risk_score < 0.33:
                        category = "Low"
                    elif ml_risk_score < 0.66:
                        category = "Moderate"
                    else:
                        category = "High"
                    
                    fallback_templates = {
                        "Low": (
                            "Based on your Clinical Severity Score of {} out of 100 (Routine Monitoring), "
                            "your condition appears stable. Continue your current diabetes management plan: "
                            "1) Take medications as prescribed, 2) Monitor blood glucose regularly, "
                            "3) Maintain a balanced diet low in refined carbohydrates, 4) Engage in 150 minutes "
                            "of moderate exercise weekly. Schedule routine follow-ups with your Healthier SG GP. "
                            "Visit a CHAS clinic for subsidized care. Seek immediate help if you experience "
                            "chest pain, severe shortness of breath, or confusion."
                        ),
                        "Moderate": (
                            "Based on your Clinical Severity Score of {} out of 100 (Increased Surveillance), "
                            "you should schedule an earlier follow-up appointment to review your care plan. "
                            "Pay close attention to medication adherence and monitor for symptom changes. "
                            "Consider visiting a polyclinic for enhanced monitoring and medication review. "
                            "Under Healthier SG, you can enroll with a dedicated GP for coordinated care. "
                            "If symptoms worsen (persistent vomiting, vision changes, slow-healing sores), "
                            "seek medical attention promptly."
                        ),
                        "High": (
                            "Based on your Clinical Severity Score of {} out of 100 (Immediate Intervention), "
                            "you require urgent medical attention. Do not delay—visit a polyclinic or A&E immediately. "
                            "Your symptoms and severity level indicate potential complications that need prompt assessment. "
                            "Bring your medication list and recent health records. Call 995 if you experience "
                            "life-threatening symptoms like chest pain, difficulty breathing, or loss of consciousness. "
                            "After stabilization, follow up with your GP under Healthier SG for ongoing management."
                        )
                    }
                    return fallback_templates.get(category, fallback_templates["Moderate"]).format(severity_score)
            
            assistant = FallbackAssistant()
            print(f"\n✓ Using FallbackAssistant (API unavailable)")
    
    except Exception as e:
        print(f"\n✗ Failed to initialize assistant: {e}")
        return
    
    # Evaluation metrics
    results_summary = {
        "low_risk_count": 0,
        "moderate_risk_count": 0,
        "high_risk_count": 0,
        "singapore_context_mentions": 0,
        "emergency_guidance_present": 0,
    }
    
    print("\n" + "=" * 80)
    print("DETAILED EVALUATION RESULTS")
    print("=" * 80)
    
    for scenario in SAMPLE_SCENARIOS:
        print(f"\n{'='*80}")
        print(f"SCENARIO #{scenario['id']}")
        print(f"{'='*80}")
        
        # Determine risk category
        if scenario['risk_score'] < 0.33:
            risk_category = "Low"
            results_summary["low_risk_count"] += 1
        elif scenario['risk_score'] < 0.66:
            risk_category = "Moderate"
            results_summary["moderate_risk_count"] += 1
        else:
            risk_category = "High"
            results_summary["high_risk_count"] += 1
        
        print(f"\n[INPUT]")
        print(f"  Risk Score: {scenario['risk_score']} ({risk_category} Risk)")
        print(f"  Symptoms: {', '.join(scenario['symptoms']) if scenario['symptoms'] else 'None'}")
        print(f"  Patient Question: {scenario['question']}")
        print(f"  Expected Context: {scenario['expected_context']}")
        
        # Generate advice
        try:
            response = assistant.generate_advice(
                patient_symptoms=scenario['symptoms'],
                ml_risk_score=scenario['risk_score'],
                risk_category=risk_category,
                user_question=scenario['question']
            )
            
            print(f"\n[OUTPUT]")
            print(f"  Response Length: {len(response)} characters")
            print(f"\n  Generated Advice:\n  {'-'*76}")
            # Word wrap for readability
            words = response.split()
            line = "  "
            for word in words:
                if len(line) + len(word) > 78:
                    print(line)
                    line = "  " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)
            print(f"  {'-'*76}")
            
            # Check for Singapore context
            singapore_keywords = ["CHAS", "Healthier SG", "polyclinic", "GP", "995", "A&E", "Singapore"]
            has_singapore_context = any(kw.lower() in response.lower() for kw in singapore_keywords)
            if has_singapore_context:
                results_summary["singapore_context_mentions"] += 1
            
            # Check for emergency guidance (for high risk)
            if risk_category == "High":
                emergency_keywords = ["immediate", "urgent", "A&E", "995", "emergency", "now"]
                has_emergency_guidance = any(kw.lower() in response.lower() for kw in emergency_keywords)
                if has_emergency_guidance:
                    results_summary["emergency_guidance_present"] += 1
            
            print(f"\n[EVALUATION]")
            print(f"  ✓ Singapore Context: {'Yes' if has_singapore_context else 'No'}")
            if risk_category == "High":
                print(f"  ✓ Emergency Guidance: {'Yes' if has_emergency_guidance else 'No'}")
            print(f"  ✓ Clinical Severity Framing: {'Yes' if 'out of 100' in response else 'No'}")
            
        except Exception as e:
            print(f"\n[ERROR]")
            print(f"  ✗ Failed to generate advice: {e}")
    
    # Summary Report
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"\nScenario Distribution:")
    print(f"  - Low Risk: {results_summary['low_risk_count']} scenarios")
    print(f"  - Moderate Risk: {results_summary['moderate_risk_count']} scenarios")
    print(f"  - High Risk: {results_summary['high_risk_count']} scenarios")
    print(f"\nQuality Metrics:")
    print(f"  - Singapore Context Mentions: {results_summary['singapore_context_mentions']}/{len(SAMPLE_SCENARIOS)}")
    print(f"  - Emergency Guidance (High Risk): {results_summary['emergency_guidance_present']}/{results_summary['high_risk_count']}")
    
    if api_key:
        print(f"\n✓ Evaluation completed with LIVE Gemini API responses")
    else:
        print(f"\n✓ Evaluation completed with FALLBACK TEMPLATES (API unavailable)")
    
    print("\n" + "=" * 80)
    print("END OF EVALUATION REPORT")
    print("=" * 80)


if __name__ == "__main__":
    evaluate_gen_ai()
