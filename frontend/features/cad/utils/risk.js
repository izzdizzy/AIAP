export function getRiskLevel(probability) {
  if (probability < 0.2) {
    return 'Low';
  }

  if (probability < 0.6) {
    return 'Moderate';
  }

  return 'High';
}

export function formatPercent(probability) {
  return `${Math.round(probability * 1000) / 10}%`;
}

export function getLifestyleAdvice(riskLevel) {
  if (riskLevel === 'High') {
    return [
      'Seek timely review with a clinician, especially if chest discomfort persists.',
      'Keep a short log of symptoms, triggers, and medication use for your next appointment.',
      'Avoid strenuous exertion until a medical professional confirms it is safe.'
    ];
  }

  if (riskLevel === 'Moderate') {
    return [
      'Discuss your symptoms and test results with a clinician when possible.',
      'Focus on consistent walking, diet control, and sleep regularity.',
      'Monitor for worsening chest pain, shortness of breath, or reduced exercise tolerance.'
    ];
  }

  return [
    'Maintain regular activity, balanced meals, and follow-up screenings.',
    'Track blood pressure, cholesterol, and new symptoms over time.',
    'Use this result as a screening aid, not a diagnosis.'
  ];
}

export function describeFactorDirection(direction) {
  return direction === 'increase' ? 'Higher contribution' : 'Lower contribution';
}
