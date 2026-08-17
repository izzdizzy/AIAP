export default function FormField({ field, value, values, error, onChange, onBlur }) {
  const id = `field-${field.name}`;
  const showHelperAbove = field.inputType === 'radio';
  const helperText = field.required
    ? field.helper
    : `${field.helper} Leave blank if unknown.`;

  return (
    <label className={`form-field${field.kind === 'triage' ? ' form-field--wide' : ''}`} htmlFor={id}>
      {showHelperAbove ? (
        <span className="form-field__help">{helperText}</span>
      ) : null}

      <span className="form-field__label">
        {field.label}
        {field.required ? (
          <span className="form-field__required">Required</span>
        ) : (
          <span className="form-field__optional">Optional</span>
        )}
      </span>

      {field.kind === 'triage' && field.inputType === 'radio' ? (
        <div className="triage-group">
          {field.options.map((question) => (
            <div key={question.id} className="triage-question">
              <span className="triage-question__label">{question.label}</span>
              <div className="radio-options">
                {question.options.map((option) => (
                  <label key={option.value} className="radio-option">
                    <input
                      type="radio"
                      name={`${field.name}-${question.id}`}
                      value={option.value}
                      checked={
                        String(values[`cp-${question.id}`] ?? '') ===
                        String(option.value)
                      }
                      onChange={onChange}
                      onBlur={onBlur}
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : field.kind === 'select' && field.inputType === 'radio' ? (
        <div className="radio-group">
          {field.options.map((option) => (
            <label key={option.value} className="radio-option">
              <input
                type="radio"
                id={`${id}-${option.value}`}
                name={field.name}
                value={option.value}
                checked={String(value) === String(option.value)}
                onChange={onChange}
                onBlur={onBlur}
                aria-invalid={Boolean(error)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      ) : field.kind === 'select' ? (
        <select id={id} name={field.name} value={value} onChange={onChange} onBlur={onBlur} aria-invalid={Boolean(error)}>
          <option value="">{field.optionalLabel ?? 'Select an option'}</option>
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          name={field.name}
          type={field.inputType}
          min={field.min}
          max={field.max}
          step={field.step}
          placeholder={field.placeholder}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          inputMode={field.inputType === 'number' ? 'decimal' : undefined}
          aria-invalid={Boolean(error)}
        />
      )}

      {error ? <span className="form-field__error">{error}</span> : null}
    </label>
  );
}
