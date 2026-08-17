import { useMemo, useState } from 'react';
import {
  assessmentFields,
  createInitialAssessmentValues,
  fieldOrder,
  validateAssessmentValue
} from '../utils/assessmentConfig';
import {
  getAnsweredFieldNames,
  isChestPainTriageComplete
} from '../utils/payload';

export function useAssessmentForm(initialValues = null) {
  const [values, setValues] = useState(() => (
    initialValues
      ? { ...createInitialAssessmentValues(), ...initialValues }
      : createInitialAssessmentValues()
  ));
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const fieldNames = useMemo(() => fieldOrder, []);

  function setFieldValue(fieldName, value) {
    setValues((currentValues) => ({
      ...currentValues,
      [fieldName]: value
    }));
  }

  function handleChange(event) {
    const { name, value } = event.target;
    setFieldValue(name, value);

    if (touched[name]) {
      setErrors((currentErrors) => ({
        ...currentErrors,
        [name]: validateAssessmentValue(name, value)
      }));
    }
  }

  function handleBlur(event) {
    const { name, value } = event.target;
    setTouched((currentTouched) => ({
      ...currentTouched,
      [name]: true
    }));
    setErrors((currentErrors) => ({
      ...currentErrors,
      [name]: validateAssessmentValue(name, value)
    }));
  }

  function validateField(fieldName) {

    // Ignore hidden chest pain fields
    if (fieldName === 'cpManual' && values.cpAssessment !== 'manual') {
      return '';
    }

    if (fieldName === 'cp' && values.cpAssessment !== 'guided') {
      return '';
    }

    // Chest pain triage has custom validation
    if (fieldName === 'cp') {
      return isChestPainTriageComplete(values)
        ? ''
        : 'Please answer all chest pain questions.';
    }

    return validateAssessmentValue(fieldName, values[fieldName]);
  }

  function validateFields(names) {
    const nextErrors = names.reduce((accumulator, fieldName) => {
      const validationError = validateField(fieldName);
      if (validationError) {
        accumulator[fieldName] = validationError;
      }
      return accumulator;
    }, {});

    setErrors((currentErrors) => ({ ...currentErrors, ...nextErrors }));
    setTouched((currentTouched) => (
      names.reduce((accumulator, fieldName) => ({ ...accumulator, [fieldName]: true }), currentTouched)
    ));

    return Object.keys(nextErrors).length === 0;
  }

  function validateAll() {
    return validateFields(fieldNames);
  }

  function resetForm() {
    setValues(createInitialAssessmentValues());
    setErrors({});
    setTouched({});
  }

  function hasError(fieldName) {
    return Boolean(touched[fieldName] && errors[fieldName]);
  }

  function getAnsweredCount() {
    return getAnsweredFieldNames(values).length;
  }

  function getAnsweredNames() {
    return getAnsweredFieldNames(values);
  }

  function getFieldMeta(fieldName) {
    return assessmentFields[fieldName];
  }

  return {
    values,
    errors,
    touched,
    hasError,
    getFieldMeta,
    handleChange,
    handleBlur,
    setFieldValue,
    validateFields,
    validateAll,
    resetForm,
    getAnsweredCount,
    getAnsweredNames
  };
}
