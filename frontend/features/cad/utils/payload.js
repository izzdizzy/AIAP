import { fieldOrder, chestPainTriageToValue, assessmentFields } from './assessmentConfig';

export function toNumber(value) {
  return value === '' || value === null || value === undefined ? null : Number(value);
}

export function isAnsweredValue(value) {
  return value !== '' && value !== null && value !== undefined;
}

export function getTriageAnswerKey(value) {
  if (value === 1 || value === '1') {
    return 'yes';
  }
  if (value === 0 || value === '0') {
    return 'no';
  }
  return null;
}

export function getChestPainTriageAnswers(values) {
  const cpField = assessmentFields.cp;
  const questionIds = cpField.options.filter((question) => question.required).map((question) => question.id);
  const answers = {};

  for (const questionId of questionIds) {
    const answerKey = getTriageAnswerKey(values[`cp-${questionId}`]);
    if (answerKey) {
      answers[questionId] = answerKey;
    }
  }

  return answers;
}

export function isChestPainTriageComplete(values) {
  const cpField = assessmentFields.cp;
  const questionIds = cpField.options.filter((question) => question.required).map((question) => question.id);
  return questionIds.every((questionId) => getTriageAnswerKey(values[`cp-${questionId}`]) !== null);
}

export function chestPainAnswersToValue(answers) {
  const cpField = assessmentFields.cp;
  const questionIds = cpField.options.filter((question) => question.required).map((question) => question.id);
  const lookupKey = questionIds.map((questionId) => answers[questionId]).filter(Boolean).join('-');
  return chestPainTriageToValue[lookupKey] ?? chestPainTriageToValue.default ?? 4;
}

export function isFieldAnswered(fieldName, values) {
  if (fieldName === 'cp') {
    if (values.cpAssessment === 'none') {
      return true;
    }
    if (values.cpAssessment === 'manual') {
      return isAnsweredValue(values.cpManual);
    }
    if (values.cpAssessment === 'guided') {
      return isChestPainTriageComplete(values);
    }
    return false;
  }

  return isAnsweredValue(values[fieldName]);
}

export function buildAssessmentPayload(values) {
  const payload = {};

  for (const fieldName of fieldOrder) {
    if (fieldName === 'cp') {
      // Chest pain classification
      switch (values.cpAssessment) {
        case 'manual':
          payload.cp = Number(values.cpManual);
          break;

        case 'none':
          payload.cp = 4;
          break;

        case 'guided':
        default:
          payload.cp = chestPainAnswersToValue(
            getChestPainTriageAnswers(values)
          );
          break;
      }
    } else {
      payload[fieldName] = toNumber(values[fieldName]);
    }
  }

  return payload;
}

export function getAnsweredFieldNames(values) {
  const answered = [];
  if (isAnsweredValue(values.age)) answered.push('age');
  if (isAnsweredValue(values.sex)) answered.push('sex');
  if (isAnsweredValue(values.cpAssessment)) answered.push('cpAssessment');
  if (values.cpAssessment === 'manual' && isAnsweredValue(values.cpManual)) answered.push('cpManual');
  if (values.cpAssessment === 'guided' && isChestPainTriageComplete(values)) answered.push('cp');
  if (isAnsweredValue(values.exang)) answered.push('exang');
  if (isAnsweredValue(values.trestbps)) answered.push('trestbps');
  if (isAnsweredValue(values.chol)) answered.push('chol');
  if (isAnsweredValue(values.fbs)) answered.push('fbs');
  if (isAnsweredValue(values.restecg)) answered.push('restecg');
  if (isAnsweredValue(values.thalach)) answered.push('thalach');
  if (isAnsweredValue(values.oldpeak)) answered.push('oldpeak');
  if (isAnsweredValue(values.slope)) answered.push('slope');
  if (isAnsweredValue(values.ca)) answered.push('ca');
  if (isAnsweredValue(values.thal)) answered.push('thal');
  return answered;
}
