import { useState, useCallback } from 'react';

/**
 * Universal Form Validation and State Management Hook
 * Supports step-by-step validation, custom field rules, and error tracking across assessment forms.
 */
export function useFormValidation({
  initialValues = {},
  validateFieldValue = null,
  fieldOrder = []
} = {}) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const setFieldValue = useCallback((fieldName, value) => {
    setValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  }, []);

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const finalVal = type === 'checkbox' ? checked : value;
    
    setValues(prev => ({
      ...prev,
      [name]: finalVal
    }));

    if (touched[name] && validateFieldValue) {
      const err = validateFieldValue(name, finalVal, values);
      setErrors(prev => ({
        ...prev,
        [name]: err || ''
      }));
    }
  }, [touched, validateFieldValue, values]);

  const handleBlur = useCallback((e) => {
    const { name, value } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    if (validateFieldValue) {
      const err = validateFieldValue(name, value, values);
      setErrors(prev => ({ ...prev, [name]: err || '' }));
    }
  }, [validateFieldValue, values]);

  const validateField = useCallback((fieldName) => {
    if (!validateFieldValue) return '';
    return validateFieldValue(fieldName, values[fieldName], values) || '';
  }, [validateFieldValue, values]);

  const validateFields = useCallback((fieldNames) => {
    if (!validateFieldValue) return true;
    const nextErrors = {};
    let isValid = true;

    fieldNames.forEach(fieldName => {
      const err = validateFieldValue(fieldName, values[fieldName], values);
      if (err) {
        nextErrors[fieldName] = err;
        isValid = false;
      }
    });

    setErrors(prev => ({ ...prev, ...nextErrors }));
    setTouched(prev => {
      const nextTouched = { ...prev };
      fieldNames.forEach(f => { nextTouched[f] = true; });
      return nextTouched;
    });

    return isValid;
  }, [validateFieldValue, values]);

  const validateAll = useCallback(() => {
    const allNames = fieldOrder.length > 0 ? fieldOrder : Object.keys(values);
    return validateFields(allNames);
  }, [fieldOrder, validateFields, values]);

  const resetForm = useCallback((newDefaults = initialValues) => {
    setValues(newDefaults);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return {
    values,
    setValues,
    setFieldValue,
    errors,
    touched,
    handleChange,
    handleBlur,
    validateField,
    validateFields,
    validateAll,
    resetForm
  };
}

export default useFormValidation;
