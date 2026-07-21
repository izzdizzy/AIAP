"""
Gen AI Evaluation Module for Hospital Readmission Predictor
============================================================

This module provides automated scoring functions to evaluate the quality of 
AI-generated care navigation advice based on specific criteria.

Evaluation Criteria (Total: 5 points):
1. Clinical Severity framing (1pt) - Does it use "Clinical Severity Score" terminology?
2. Singapore context mentions like CHAS/Healthier SG (2pts) - Local healthcare references
3. Emergency guidance presence (1pt) - Clear instructions for emergencies
4. Formatting (1pt) - Proper structure without markdown headers

Usage:
    from eval_gen_ai import evaluate_ai_output
    
    score, details = evaluate_ai_output(ai_response_text)
    print(f"Score: {score}/5")
"""

import re
from typing import Dict, Any, Tuple


def evaluate_ai_output(ai_response: str) -> Tuple[float, Dict[str, Any]]:
    """
    Evaluate AI-generated care navigation advice out of 5 points.
    
    Scoring breakdown:
    - Clinical Severity framing: 1 point
    - Singapore context (CHAS/Healthier SG): 2 points  
    - Emergency guidance: 1 point
    - Formatting: 1 point
    
    Args:
        ai_response: The AI-generated response text to evaluate
        
    Returns:
        Tuple of (total_score, details_dict) where details contains breakdown
    """
    if not ai_response or not isinstance(ai_response, str):
        return 0.0, {
            'clinical_severity': 0,
            'singapore_context': 0,
            'emergency_guidance': 0,
            'formatting': 0,
            'total': 0.0,
            'feedback': 'Empty or invalid response'
        }
    
    response_lower = ai_response.lower()
    details = {
        'clinical_severity': 0,
        'singapore_context': 0,
        'emergency_guidance': 0,
        'formatting': 0,
        'total': 0.0,
        'feedback': []
    }
    
    # Criterion 1: Clinical Severity framing (1 point)
    # Check if response uses proper clinical severity terminology
    clinical_keywords = [
        'clinical severity',
        'severity score',
        'out of 100',
        'urgency level',
        'routine monitoring',
        'increased surveillance',
        'immediate intervention'
    ]
    
    clinical_matches = sum(1 for kw in clinical_keywords if kw in response_lower)
    if clinical_matches >= 2:
        details['clinical_severity'] = 1.0
        details['feedback'].append('✓ Uses proper clinical severity framing')
    else:
        details['feedback'].append('✗ Missing clinical severity terminology')
    
    # Criterion 2: Singapore context - CHAS/Healthier SG (2 points)
    # Check for Singapore-specific healthcare references
    singapore_keywords = {
        'chas': ['chas', 'community health assist scheme', 'chas blue', 'chas orange', 'chas green'],
        'healthier_sg': ['healthier sg', 'healthier singapore', 'enroll with a gp', 'family physician'],
        'polyclinic': ['polyclinic', 'polyclinics'],
        'sg_emergency': ['995', 'a&e', 'accident & emergency', 'singapore hospital']
    }
    
    singapore_score = 0.0
    singapore_found = []
    
    for category, keywords in singapore_keywords.items():
        for kw in keywords:
            if kw in response_lower:
                singapore_score += 0.5
                singapore_found.append(category)
                break
    
    # Cap at 2 points
    singapore_score = min(2.0, singapore_score)
    details['singapore_context'] = singapore_score
    
    if singapore_score >= 1.5:
        details['feedback'].append('✓ Strong Singapore healthcare context')
    elif singapore_score >= 0.5:
        details['feedback'].append('~ Some Singapore context present')
    else:
        details['feedback'].append('✗ Missing Singapore healthcare context (CHAS/Healthier SG)')
    
    # Criterion 3: Emergency guidance (1 point)
    # Check for clear emergency instructions
    emergency_keywords = [
        'call 995',
        'emergency',
        'a&e',
        'immediate medical attention',
        'urgent',
        'life-threatening',
        'seek immediate',
        'go to hospital'
    ]
    
    emergency_matches = sum(1 for kw in emergency_keywords if kw in response_lower)
    if emergency_matches >= 1:
        details['emergency_guidance'] = 1.0
        details['feedback'].append('✓ Contains emergency guidance')
    else:
        details['feedback'].append('✗ Missing emergency guidance')
    
    # Criterion 4: Formatting (1 point)
    # Check for proper formatting - no markdown headers, uses bullet points
    has_markdown_headers = bool(re.search(r'^#{1,6}\s+', ai_response, re.MULTILINE))
    has_bullet_points = bool(re.search(r'^[\*\-•]\s+', ai_response, re.MULTILINE))
    has_proper_structure = len(ai_response.split('\n')) >= 3
    
    formatting_score = 0.0
    if not has_markdown_headers:
        formatting_score += 0.5
    if has_bullet_points or has_proper_structure:
        formatting_score += 0.5
    
    details['formatting'] = formatting_score
    
    if formatting_score >= 0.8:
        details['feedback'].append('✓ Good formatting (no headers, readable structure)')
    else:
        details['feedback'].append('✗ Formatting issues detected')
    
    # Calculate total score
    details['total'] = (
        details['clinical_severity'] +
        details['singapore_context'] +
        details['emergency_guidance'] +
        details['formatting']
    )
    
    return details['total'], details


def grade_ai_response(ai_response: str, min_passing_score: float = 3.0) -> Dict[str, Any]:
    """
    Grade an AI response and determine if it passes minimum quality standards.
    
    Args:
        ai_response: The AI-generated response text
        min_passing_score: Minimum score required to pass (default: 3.0/5.0)
        
    Returns:
        Dictionary with grade, passed status, and detailed feedback
    """
    score, details = evaluate_ai_output(ai_response)
    
    passed = score >= min_passing_score
    
    return {
        'score': score,
        'max_score': 5.0,
        'percentage': (score / 5.0) * 100,
        'passed': passed,
        'min_passing_score': min_passing_score,
        'breakdown': {
            'clinical_severity_framing': f"{details['clinical_severity']}/1",
            'singapore_context': f"{details['singapore_context']}/2",
            'emergency_guidance': f"{details['emergency_guidance']}/1",
            'formatting': f"{details['formatting']}/1"
        },
        'feedback': details['feedback']
    }


# Example usage and testing
if __name__ == '__main__':
    # Test with sample responses
    test_good_response = """
    Based on your Clinical Severity Score of 75 out of 100, you require Immediate Intervention.
    
    Here are my recommendations:
    - Seek immediate medical attention at your nearest polyclinic or A&E
    - If symptoms worsen, call 995 for emergency assistance
    - Consider enrolling with a GP under Healthier SG for ongoing management
    - CHAS Blue cardholders can receive subsidized care at participating clinics
    
    Please do not delay seeking medical care.
    """
    
    test_poor_response = """
    Your score is high. You should see a doctor soon.
    Take your medications and eat healthy food.
    """
    
    print("=" * 60)
    print("GOOD RESPONSE EVALUATION:")
    print("=" * 60)
    result = grade_ai_response(test_good_response)
    print(f"Score: {result['score']}/{result['max_score']} ({result['percentage']:.1f}%)")
    print(f"Passed: {result['passed']}")
    print("Breakdown:")
    for criterion, score in result['breakdown'].items():
        print(f"  - {criterion}: {score}")
    print("Feedback:")
    for fb in result['feedback']:
        print(f"  {fb}")
    
    print("\n" + "=" * 60)
    print("POOR RESPONSE EVALUATION:")
    print("=" * 60)
    result = grade_ai_response(test_poor_response)
    print(f"Score: {result['score']}/{result['max_score']} ({result['percentage']:.1f}%)")
    print(f"Passed: {result['passed']}")
    print("Breakdown:")
    for criterion, score in result['breakdown'].items():
        print(f"  - {criterion}: {score}")
    print("Feedback:")
    for fb in result['feedback']:
        print(f"  {fb}")
