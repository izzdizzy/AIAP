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

  // TASK 3: State variables for dropdown and symptom auto-fill
  const [ageGroup, setAgeGroup] = useState('');
  const [chasTier, setChasTier] = useState('None');
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);

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
    if (file && !loading) {
      handleFileUpload();
    }
  }, [file]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setUploadStatus(null);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSymptomToggle = (symptom) => {
    // Update formData.symptoms
    setFormData(prev => {
      const exists = prev.symptoms.includes(symptom);
      return {
        ...prev,
        symptoms: exists
          ? prev.symptoms.filter(s => s !== symptom)
          : [...prev.symptoms, symptom]
      };
    });

    // Also update selectedSymptoms state for auto-fill tracking
    setSelectedSymptoms(prev => {
      const exists = prev.includes(symptom);
      if (exists) {
        return prev.filter(s => s !== symptom);
      } else {
        return [...prev, symptom];
      }
    });
  };

  /**
   * Handle file upload and parse CSV/XLSX to auto-fill form fields
   * Maps CSV columns to form fields using backend's CSV_TO_MODEL_MAPPING
   */
  const handleFileUpload = async () => {
    if (!file) {
      setUploadStatus({ type: 'error', message: 'Please select a file first.' });
      return;
    }

    try {
      const formDataObj = new FormData();
      formDataObj.append('file', file);

      const response = await fetch('http://localhost:8000/readmission/api/upload', {
        method: 'POST',
        body: formDataObj
      });

      // Strict error handling for non-200 responses
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // TASK 3: Log backend response for debugging
      console.log('Backend Upload Response:', result);

      // Verify response structure before accessing properties
      if (!result) {
        throw new Error('Invalid response from server');
      }

      if (result.success && result.patient_data) {
        const data = result.patient_data;

        // TASK 3: Explicitly map backend response to React state
        // Age group mapping - use age_group key directly from backend
        if (data.age_group) {
          setAgeGroup(data.age_group);
        } else if (data.age_group_display) {
          setAgeGroup(data.age_group_display);
        }

        // CHAS Tier mapping - use chas_tier key directly from backend
        if (data.chas_tier) {
          setChasTier(data.chas_tier);
        }

        // Symptoms mapping - use symptoms array from backend
        const symptomsData = Array.isArray(data.symptoms) ? data.symptoms :
          (Array.isArray(data.symptoms_list) ? data.symptoms_list : []);
        setSelectedSymptoms(symptomsData);

        // Parse symptoms from CSV - handle both string (comma-separated) and array formats
        let parsedSymptoms = symptomsData;
        if (!parsedSymptoms || parsedSymptoms.length === 0) {
          if (data.symptoms && typeof data.symptoms === 'string') {
            // Comma-separated string - parse it
            const symptomStrings = data.symptoms.split(',').map(s => s.trim()).filter(s => s);
            // Map to exact symptom button labels (case-insensitive matching)
            parsedSymptoms = symptomStrings.map(inputSymptom => {
              const normalizedInput = inputSymptom.toLowerCase();
              const match = symptomsList.find(symptom => symptom.toLowerCase() === normalizedInput);
              return match || inputSymptom;
            });
          }
        }

        // Map parsed CSV data to form fields with strict null/undefined checks
        // This mapping aligns with the backend's CSV_TO_MODEL_MAPPING in utils.py
        setFormData(prev => ({
          ...prev,
          // Age mapping: convert numeric age or use age_group_display
          age: data.age_numeric != null ? String(data.age_numeric) : prev.age,
          age_group: data.age_group || data.age_group_display || prev.age_group,

          // Medication count mapping
          num_medications: data.num_medications != null ? String(data.num_medications) :
            (data.total_medications != null ? String(data.total_medications) : prev.num_medications),
          medications: data.total_medications != null ? String(data.total_medications) : prev.medications,

          // Comorbidity mapping
          comorbidity_count: data.comorbidity_count != null ? String(data.comorbidity_count) : prev.comorbidity_count,
          comorbidities: data.comorbidity_count != null ? String(data.comorbidity_count) : prev.comorbidities,

          // Prior admissions / inpatient visits mapping
          prior_admissions: data.prior_admissions != null ? String(data.prior_admissions) :
            (data.total_prior_admissions != null ? String(data.total_prior_admissions) :
              (data.number_inpatient != null ? String(data.number_inpatient) : prev.prior_admissions)),
          number_inpatient: data.number_inpatient != null ? String(data.number_inpatient) :
            (data.prior_admissions != null ? String(data.prior_admissions) : prev.number_inpatient),

          // Hospital stay features
          time_in_hospital: data.time_in_hospital != null ? String(data.time_in_hospital) : prev.time_in_hospital,
          num_lab_procedures: data.num_lab_procedures != null ? String(data.num_lab_procedures) : prev.num_lab_procedures,
          num_procedures: data.num_procedures != null ? String(data.num_procedures) : prev.num_procedures,

          // Visit counts
          number_outpatient: data.number_outpatient != null ? String(data.number_outpatient) : prev.number_outpatient,
          number_emergency: data.number_emergency != null ? String(data.number_emergency) : prev.number_emergency,

          // Diagnosis features
          number_diagnoses: data.number_diagnoses != null ? String(data.number_diagnoses) : prev.number_diagnoses,
          diabetes_diag_count: data.diabetes_diag_count != null ? String(data.diabetes_diag_count) : prev.diabetes_diag_count,

          // Administrative features
          admission_type_id: data.admission_type_id != null ? String(data.admission_type_id) : prev.admission_type_id,
          discharge_disposition_id: data.discharge_disposition_id != null ? String(data.discharge_disposition_id) : prev.discharge_disposition_id,
          admission_source_id: data.admission_source_id != null ? String(data.admission_source_id) : prev.admission_source_id,

          // CHAS Tier mapping
          chas_tier: data.chas_tier != null ? String(data.chas_tier) : prev.chas_tier,

          // Medication flags - ensure boolean conversion is safe
          metformin_encoded: (data.metformin_encoded === 1 || data.metformin_encoded === true) ? true : prev.metformin_encoded,
          insulin_encoded: (data.insulin_encoded === 1 || data.insulin_encoded === true) ? true : prev.insulin_encoded,
          on_insulin: (data.on_insulin === 1 || data.on_insulin === true) ? true : prev.on_insulin,

          // Symptoms from CSV - use parsed array, default to empty array if no symptoms
          symptoms: parsedSymptoms
        }));

        setUploadStatus({
          type: 'success',
          message: `File parsed successfully! ${result.data_completeness_pct != null ? Math.round(result.data_completeness_pct) : 0}% data completeness.`
        });

        // Notify parent component of successful upload
        if (onFileUpload) {
          onFileUpload(result);
        }
      } else {
        // Display error from backend but don't crash
        setUploadStatus({
          type: 'error',
          message: result.error || 'Failed to parse file. Please check the file format.'
        });
      }
    } catch (error) {
      // Catch network errors, parsing errors, etc.
      setUploadStatus({
        type: 'error',
        message: `Upload error: ${error.message || 'An unexpected error occurred'}`
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Ensure formData includes the latest selectedSymptoms and chas_tier
    const enrichedFormData = {
      ...formData,
      symptoms: selectedSymptoms,
      chas_tier: chasTier
    };
    // Submit both form data and file (if present)
    await onSubmit(enrichedFormData, file);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* File Upload Section */}
      <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Upload Patient File (.csv, .xlsx)
        </label>
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          disabled={loading}
          className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm disabled:opacity-50"
        />
        {file && (
          <p className="mt-1 text-xs text-gray-400">
            {loading ? 'Processing...' : `Selected: ${file.name}`}
          </p>
        )}
        {/* Error Alert Box - Red background for errors */}
        {uploadStatus && uploadStatus.type === 'error' && (
          <div className="mt-3 p-3 bg-red-900/40 border border-red-700 rounded-md">
            <p className="text-sm text-red-300 font-medium">Upload Error</p>
            <p className="text-sm text-red-400">{uploadStatus.message}</p>
          </div>
        )}
        {/* Success Message */}
        {uploadStatus && uploadStatus.type === 'success' && (
          <p className="mt-2 text-sm text-green-400">
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
            value={ageGroup || formData.age_group}
            onChange={(e) => {
              setAgeGroup(e.target.value);
              handleInputChange(e);
            }}
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
          value={chasTier || formData.chas_tier}
          onChange={(e) => {
            setChasTier(e.target.value);
            handleInputChange(e);
          }}
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
              className={`px-3 py-1 rounded-full text-sm transition-colors ${selectedSymptoms.includes(symptom) || formData.symptoms.includes(symptom)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                }`}
            >
              {symptom}
            </button>
          ))}
        </div>
        {(selectedSymptoms.length > 0 || formData.symptoms.length > 0) && (
          <p className="mt-1 text-xs text-gray-400">
            Selected: {[...new Set([...selectedSymptoms, ...formData.symptoms])].join(', ')}
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
