import React, { useState, useEffect } from 'react';

// Comprehensive symptoms list matching UCI Diabetes dataset and clinical relevance
const symptomsList = [
  'Fatigue', 'Frequent urination', 'Excessive thirst', 'Blurred vision',
  'Slow-healing sores', 'Tingling in hands/feet', 'Increased hunger',
  'Unexplained weight loss', 'Dry skin', 'Frequent infections',
  'Irritability', 'Nausea', 'Chest Pain', 'Shortness of Breath',
  'Dizziness', 'Palpitations', 'Edema', 'Cough', 'Fever', 'Headache'
];

const chasTiers = ['Blue', 'Orange', 'Pioneer', 'Merdeka', 'None'];

// Age group options matching UCI dataset schema
const ageGroups = [
  '0-10', '10-20', '20-30', '30-40', '40-50',
  '50-60', '60-70', '70-80', '80-90', '90-100'
];

/**
 * PatientForm Component
 * 
 * Handles patient data input with support for:
 * - Manual form entry
 * - CSV/XLSX file upload with auto-fill mapping
 * - Data completeness validation
 * 
 * The form fields are mapped to UCI Diabetes 130-US dataset schema columns:
 * - age_numeric (from age group selection)
 * - num_medications / total_medications
 * - comorbidity_count
 * - number_inpatient / prior_admissions
 * - time_in_hospital
 * - number_diagnoses
 * - admission_type_id, discharge_disposition_id, admission_source_id
 * - num_lab_procedures, num_procedures
 * - diabetes_diag_count
 * - Various medication encoding fields (metformin_encoded, insulin_encoded, etc.)
 */
const PatientForm = ({ onSubmit, loading, onFileUpload }) => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success'|'error', message: string }
  
  // Form state with comprehensive UCI Diabetes dataset fields
  const [formData, setFormData] = useState({
    // Core clinical features
    prior_admissions: '',
    comorbidities: '',
    comorbidity_count: '',
    age: '',
    age_group: '',
    medications: '',
    num_medications: '',
    chas_tier: 'None',
    symptoms: [],
    
    // Hospital stay features
    time_in_hospital: '',
    num_lab_procedures: '',
    num_procedures: '',
    
    // Visit counts
    number_outpatient: '',
    number_emergency: '',
    number_inpatient: '',
    
    // Diagnosis features
    number_diagnoses: '',
    diabetes_diag_count: '',
    
    // Administrative features
    admission_type_id: '',
    discharge_disposition_id: '',
    admission_source_id: '',
    
    // Medication flags
    metformin_encoded: false,
    insulin_encoded: false,
    on_insulin: false
  });

  // Update form data when file is uploaded and parsed
  useEffect(() => {
    if (onFileUpload && file) {
      // File upload handling is done via handleFileUpload callback
    }
  }, [file, onFileUpload]);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setUploadStatus(null);
    
    // Automatically upload and parse file when selected
    if (selectedFile) {
      await handleFileUpload(selectedFile);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSymptomToggle = (symptom) => {
    setFormData(prev => {
      const exists = prev.symptoms.includes(symptom);
      return {
        ...prev,
        symptoms: exists
          ? prev.symptoms.filter(s => s !== symptom)
          : [...prev.symptoms, symptom]
      };
    });
  };

  /**
   * Handle file upload and parse CSV/XLSX to auto-fill form fields
   * Maps CSV columns to form fields using backend's CSV_TO_MODEL_MAPPING
   * @param {File} fileToUpload - Optional file parameter for automatic upload
   */
  const handleFileUpload = async (fileToUpload = null) => {
    const fileForUpload = fileToUpload || file;
    
    if (!fileForUpload) {
      setUploadStatus({ type: 'error', message: 'Please select a file first.' });
      return;
    }

    try {
      const formDataObj = new FormData();
      formDataObj.append('file', fileForUpload);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formDataObj
      });

      const result = await response.json();

      if (result.success && result.patient_data) {
        const data = result.patient_data;
        
        // Map parsed CSV data to form fields
        // This mapping aligns with the backend's CSV_TO_MODEL_MAPPING in utils.py
        setFormData(prev => ({
          ...prev,
          // Age mapping: convert numeric age or use age_group_display
          age: data.age_numeric?.toString() || prev.age,
          age_group: data.age_group_display || prev.age_group,
          
          // Medication count mapping
          num_medications: data.num_medications?.toString() || 
                          data.total_medications?.toString() || prev.num_medications,
          medications: data.total_medications?.toString() || prev.medications,
          
          // Comorbidity mapping
          comorbidity_count: data.comorbidity_count?.toString() || prev.comorbidity_count,
          comorbidities: data.comorbidity_count?.toString() || prev.comorbidities,
          
          // Prior admissions / inpatient visits mapping
          prior_admissions: data.prior_admissions?.toString() || 
                           data.total_prior_admissions?.toString() || 
                           data.number_inpatient?.toString() || prev.prior_admissions,
          number_inpatient: data.number_inpatient?.toString() || 
                           data.prior_admissions?.toString() || prev.number_inpatient,
          
          // Hospital stay features
          time_in_hospital: data.time_in_hospital?.toString() || prev.time_in_hospital,
          num_lab_procedures: data.num_lab_procedures?.toString() || prev.num_lab_procedures,
          num_procedures: data.num_procedures?.toString() || prev.num_procedures,
          
          // Visit counts
          number_outpatient: data.number_outpatient?.toString() || prev.number_outpatient,
          number_emergency: data.number_emergency?.toString() || prev.number_emergency,
          
          // Diagnosis features
          number_diagnoses: data.number_diagnoses?.toString() || prev.number_diagnoses,
          diabetes_diag_count: data.diabetes_diag_count?.toString() || prev.diabetes_diag_count,
          
          // Administrative features
          admission_type_id: data.admission_type_id?.toString() || prev.admission_type_id,
          discharge_disposition_id: data.discharge_disposition_id?.toString() || prev.discharge_disposition_id,
          admission_source_id: data.admission_source_id?.toString() || prev.admission_source_id,
          
          // Medication flags
          metformin_encoded: data.metformin_encoded === 1 || data.metformin_encoded === true || prev.metformin_encoded,
          insulin_encoded: data.insulin_encoded === 1 || data.insulin_encoded === true || prev.insulin_encoded,
          on_insulin: data.on_insulin === 1 || data.on_insulin === true || prev.on_insulin,
          
          // Symptoms from CSV (if provided as comma-separated list)
          symptoms: data.symptoms_list || data.symptoms || prev.symptoms
        }));

        setUploadStatus({
          type: 'success',
          message: `File parsed successfully! ${result.data_completeness_pct?.toFixed(0) || 0}% data completeness.`
        });

        // Notify parent component of successful upload
        if (onFileUpload) {
          onFileUpload(result);
        }
      } else {
        setUploadStatus({
          type: 'error',
          message: result.error || 'Failed to parse file.'
        });
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: `Upload error: ${error.message}`
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Submit both form data and file (if present)
    await onSubmit(formData, file);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* File Upload Section - Auto-uploads on file selection */}
      <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Upload Patient File (.csv, .xlsx) - Auto-parses on selection
        </label>
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          disabled={loading}
          className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm disabled:opacity-50"
        />
        {file && (
          <p className="mt-1 text-xs text-gray-400">Selected: {file.name}</p>
        )}
        {uploadStatus && (
          <p className={`mt-2 text-sm ${
            uploadStatus.type === 'success' ? 'text-green-400' : 'text-red-400'
          }`}>
            {uploadStatus.message}
          </p>
        )}
      </div>

      {/* Demographics Section */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Age (years)</label>
          <input
            type="number"
            name="age"
            value={formData.age}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 65"
            min="0"
            max="100"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Age Group</label>
          <select
            name="age_group"
            value={formData.age_group}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select...</option>
            {ageGroups.map(group => (
              <option key={group} value={group}>{group}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">CHAS Tier</label>
        <select
          name="chas_tier"
          value={formData.chas_tier}
          onChange={handleInputChange}
          className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
        >
          {chasTiers.map(tier => (
            <option key={tier} value={tier}>{tier}</option>
          ))}
        </select>
      </div>

      {/* Clinical Features Section */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Prior Admissions</label>
          <input
            type="number"
            name="prior_admissions"
            value={formData.prior_admissions}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 2"
            min="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Comorbidity Count</label>
          <input
            type="number"
            name="comorbidity_count"
            value={formData.comorbidity_count}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 3"
            min="0"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Comorbidities (text description)</label>
        <input
          type="text"
          name="comorbidities"
          value={formData.comorbidities}
          onChange={handleInputChange}
          className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
          placeholder="e.g., Diabetes, Hypertension"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Medication Count</label>
          <input
            type="number"
            name="num_medications"
            value={formData.num_medications}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 8"
            min="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Time in Hospital (days)</label>
          <input
            type="number"
            name="time_in_hospital"
            value={formData.time_in_hospital}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 5"
            min="0"
          />
        </div>
      </div>

      {/* Advanced Clinical Features (Collapsible) */}
      <details className="bg-gray-700/30 p-4 rounded-lg border border-gray-600">
        <summary className="cursor-pointer text-sm font-medium text-gray-300 mb-3">
          Advanced Clinical Features (Optional)
        </summary>
        
        <div className="grid grid-cols-2 gap-4 mt-3">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Outpatient Visits</label>
            <input
              type="number"
              name="number_outpatient"
              value={formData.number_outpatient}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., 4"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Emergency Visits</label>
            <input
              type="number"
              name="number_emergency"
              value={formData.number_emergency}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., 2"
              min="0"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-3">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Inpatient Visits</label>
            <input
              type="number"
              name="number_inpatient"
              value={formData.number_inpatient}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., 1"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Number of Diagnoses</label>
            <input
              type="number"
              name="number_diagnoses"
              value={formData.number_diagnoses}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., 5"
              min="0"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-3">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Lab Procedures</label>
            <input
              type="number"
              name="num_lab_procedures"
              value={formData.num_lab_procedures}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., 30"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Procedures</label>
            <input
              type="number"
              name="num_procedures"
              value={formData.num_procedures}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., 3"
              min="0"
            />
          </div>
        </div>
      </details>

      {/* Symptoms Section */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Symptoms</label>
        <div className="flex flex-wrap gap-2">
          {symptomsList.map(symptom => (
            <button
              key={symptom}
              type="button"
              onClick={() => handleSymptomToggle(symptom)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                formData.symptoms.includes(symptom)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
              }`}
            >
              {symptom}
            </button>
          ))}
        </div>
        {formData.symptoms.length > 0 && (
          <p className="mt-1 text-xs text-gray-400">
            Selected: {formData.symptoms.join(', ')}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors font-medium"
      >
        {loading ? 'Analyzing...' : 'Assess Risk'}
      </button>
    </form>
  );
};

export default PatientForm;
