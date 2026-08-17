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
    return isChestPainTriageComplete(values);
  }

  return isAnsweredValue(values[fieldName]);
}

export function buildAssessmentPayload(values) {
  const payload = {};

  for (const fieldName of fieldOrder) {
    if (fieldName === 'cp') {
      if (values.cpMode === 'manual') {
        payload.cp = Number(values.cpManual);
      } else if (values.cpPresent === '0') {
        payload.cp = 4;
      } else {
        if (values.cpAssessment === 'manual') {
          payload.cp = Number(values.cpManual);
        }
        else if (values.cpAssessment === 'none') {
          payload.cp = 4;
        }
        else {
          payload.cp = chestPainAnswersToValue(
            getChestPainTriageAnswers(values)
          );
        }
      }
    } else {
      payload[fieldName] = toNumber(values[fieldName]);
    }
  }

  return payload;
}

export function getAnsweredFieldNames(values) {
  return fieldOrder.filter((fieldName) => isFieldAnswered(fieldName, values));
}
