import React from 'react';

const symptomsList = [
  'Chest Pain', 'Shortness of Breath', 'Fatigue', 'Dizziness',
  'Palpitations', 'Edema', 'Cough', 'Fever', 'Nausea', 'Headache'
];

const chasTiers = ['Blue', 'Orange', 'Pioneer', 'Merdeka', 'None'];

const PatientForm = ({ onSubmit, loading }) => {
  const [file, setFile] = React.useState(null);
  const [formData, setFormData] = React.useState({
    prior_admissions: '',
    comorbidities: '',
    age: '',
    medications: '',
    chas_tier: 'None',
    symptoms: []
  });

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (file) {
      await onSubmit(formData, file);
    } else {
      await onSubmit(formData, null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Upload Patient File (.csv, .xlsx)
        </label>
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
          <input
            type="number"
            name="age"
            value={formData.age}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="e.g., 65"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">CHAS Tier</label>
          <select
            name="chas_tier"
            value={formData.chas_tier}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            {chasTiers.map(tier => (
              <option key={tier} value={tier}>{tier}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Prior Admissions</label>
        <input
          type="number"
          name="prior_admissions"
          value={formData.prior_admissions}
          onChange={handleInputChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="e.g., 2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Comorbidities</label>
        <input
          type="text"
          name="comorbidities"
          value={formData.comorbidities}
          onChange={handleInputChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="e.g., Diabetes, Hypertension"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Medications</label>
        <input
          type="text"
          name="medications"
          value={formData.medications}
          onChange={handleInputChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="e.g., Metformin, Lisinopril"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Symptoms</label>
        <div className="flex flex-wrap gap-2">
          {symptomsList.map(symptom => (
            <button
              key={symptom}
              type="button"
              onClick={() => handleSymptomToggle(symptom)}
              className={`px-3 py-1 rounded-full text-sm ${
                formData.symptoms.includes(symptom)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              {symptom}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
      >
        {loading ? 'Analyzing...' : 'Assess Risk'}
      </button>
    </form>
  );
};

export default PatientForm;
