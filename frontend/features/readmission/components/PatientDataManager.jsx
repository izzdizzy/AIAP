import React, { useState, useEffect } from 'react';

/**
 * PatientDataManager Component - Manage Patient Data Tab
 * 
 * Dedicated UI section for uploading, viewing, and updating patient CSV files.
 * Provides:
 * - File upload interface for CSV/XLSX patient data
 * - Display of current patient profile summary
 * - Option to clear or replace patient data
 * 
 * @param {Object} props
 * @param {Function} props.onFileUpload - Callback when file is successfully uploaded
 * @param {Object} props.patientData - Current patient data (from form or CSV)
 * @param {Function} props.onClearData - Callback to clear patient data
 */
const PatientDataManager = ({ onFileUpload, patientData, onClearData }) => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  
  // Auto-upload when file is selected
  useEffect(() => {
    if (file && !isUploading) {
      handleUpload();
    }
  }, [file]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setUploadStatus(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus({ type: 'error', message: 'Please select a file first.' });
      return;
    }

    setIsUploading(true);
    try {
      const formDataObj = new FormData();
      formDataObj.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formDataObj
      });

      const result = await response.json();

      if (result.success && result.patient_data) {
        setUploadStatus({
          type: 'success',
          message: `File parsed successfully! ${result.data_completeness_pct?.toFixed(0) || 0}% data completeness.`
        });
        
        // Notify parent component
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
    } finally {
      setIsUploading(false);
    }
  };

  const getPatientSummary = () => {
    if (!patientData || !patientData.form) return null;
    
    const { form, prediction } = patientData;
    const items = [];
    
    if (form.age) items.push(`Age: ${form.age}`);
    if (form.chas_tier) items.push(`CHAS Tier: ${form.chas_tier}`);
    if (form.num_medications) items.push(`Medications: ${form.num_medications}`);
    if (form.prior_admissions) items.push(`Prior Admissions: ${form.prior_admissions}`);
    if (form.comorbidity_count) items.push(`Comorbidities: ${form.comorbidity_count}`);
    if (prediction?.clinical_severity_score !== undefined) {
      items.push(`Severity Score: ${prediction.clinical_severity_score}/100`);
    }
    
    return items.join(' | ');
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">Upload Patient Data</h3>
        <p className="text-sm text-gray-400 mb-4">
          Upload a CSV or Excel file containing patient information. The system will automatically
          parse the file and populate the risk assessment form with the extracted data.
        </p>
        
        <div className="flex gap-2 items-center">
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={handleFileChange}
            disabled={isUploading}
            className="flex-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:ring-blue-500 focus:border-blue-500 text-sm disabled:opacity-50"
          />
        </div>
        
        {file && (
          <p className="mt-2 text-xs text-gray-400">
            {isUploading ? 'Processing...' : `Selected: ${file.name}`}
          </p>
        )}
        
        {uploadStatus && (
          <p className={`mt-3 text-sm ${
            uploadStatus.type === 'success' ? 'text-green-400' : 'text-red-400'
          }`}>
            {uploadStatus.message}
          </p>
        )}
      </div>

      {/* Current Patient Summary */}
      {patientData && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-100">Current Patient Profile</h3>
            <button
              onClick={onClearData}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Clear Data
            </button>
          </div>
          
          <div className="bg-gray-700/50 rounded-md p-4">
            <p className="text-sm text-gray-300">{getPatientSummary()}</p>
          </div>
          
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-700/30 rounded-md p-3">
              <p className="text-xs text-gray-400">Age</p>
              <p className="text-lg font-medium text-gray-100">{patientData.form?.age || '-'}</p>
            </div>
            <div className="bg-gray-700/30 rounded-md p-3">
              <p className="text-xs text-gray-400">CHAS Tier</p>
              <p className="text-lg font-medium text-gray-100">{patientData.form?.chas_tier || '-'}</p>
            </div>
            <div className="bg-gray-700/30 rounded-md p-3">
              <p className="text-xs text-gray-400">Medications</p>
              <p className="text-lg font-medium text-gray-100">{patientData.form?.num_medications || '-'}</p>
            </div>
            <div className="bg-gray-700/30 rounded-md p-3">
              <p className="text-xs text-gray-400">Risk Score</p>
              <p className={`text-lg font-medium ${
                patientData.prediction?.clinical_severity_score >= 70 ? 'text-red-400' :
                patientData.prediction?.clinical_severity_score >= 40 ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {patientData.prediction?.clinical_severity_score !== undefined 
                  ? `${patientData.prediction.clinical_severity_score}/100` 
                  : '-'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
        <h4 className="text-sm font-semibold text-gray-300 mb-3">Expected CSV Format</h4>
        <p className="text-xs text-gray-400 mb-2">
          Your CSV file should contain columns that map to the UCI Diabetes 130-US dataset schema:
        </p>
        <ul className="text-xs text-gray-500 space-y-1 list-disc list-inside">
          <li><code className="text-gray-400">age_numeric</code> or <code className="text-gray-400">age</code> - Patient age in years</li>
          <li><code className="text-gray-400">num_medications</code> or <code className="text-gray-400">total_medications</code> - Number of medications</li>
          <li><code className="text-gray-400">comorbidity_count</code> - Number of comorbidities</li>
          <li><code className="text-gray-400">number_inpatient</code> or <code className="text-gray-400">prior_admissions</code> - Prior hospital admissions</li>
          <li><code className="text-gray-400">time_in_hospital</code> - Days spent in hospital</li>
          <li><code className="text-gray-400">number_diagnoses</code> - Number of diagnoses</li>
          <li><code className="text-gray-400">admission_type_id</code>, <code className="text-gray-400">discharge_disposition_id</code>, <code className="text-gray-400">admission_source_id</code></li>
          <li><code className="text-gray-400">num_lab_procedures</code>, <code className="text-gray-400">num_procedures</code></li>
          <li><code className="text-gray-400">metformin_encoded</code>, <code className="text-gray-400">insulin_encoded</code> - Medication flags (0/1)</li>
        </ul>
      </div>
    </div>
  );
};

export default PatientDataManager;
