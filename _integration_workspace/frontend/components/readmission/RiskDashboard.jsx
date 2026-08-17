import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const RiskDashboard = ({ prediction }) => {
  if (!prediction) return null;

  const { 
    clinical_severity_score, 
    urgency_level, 
    raw_probability,
    risk_category,
    prediction_label,
    shap_values 
  } = prediction;

  const getSeverityColor = (score) => {
    if (score >= 70) return 'bg-red-600';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getUrgencyColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'immediate intervention': return 'text-red-400 font-bold';
      case 'increased surveillance': return 'text-yellow-400 font-semibold';
      default: return 'text-green-400';
    }
  };

  const chartData = shap_values
    ? shap_values.map(({ feature, importance }) => ({ feature, value: Math.abs(importance || 0) }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
    : [];

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">Clinical Severity Score</h3>
        <div className="relative pt-1">
          <div className="flex mb-2 items-center justify-between">
            <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-gray-300 bg-gray-700">
              Risk Level
            </span>
            <span className="text-xs font-semibold inline-block text-gray-300">
              {clinical_severity_score}%
            </span>
          </div>
          <div className="overflow-hidden h-4 mb-4 text-xs flex rounded bg-gray-700">
            <div
              style={{ width: `${clinical_severity_score}%` }}
              className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${getSeverityColor(clinical_severity_score)} transition-all duration-500`}
            ></div>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-gray-100 mb-2">Urgency Level</h3>
        <p className={`text-xl ${getUrgencyColor(urgency_level)}`}>{urgency_level}</p>
        <p className="text-sm text-gray-400 mt-1">Risk Category: {risk_category}</p>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-gray-100 mb-2">Prediction</h3>
        <p className="text-gray-300">{prediction_label}</p>
        <p className="text-sm text-gray-400 mt-1">Raw Probability: {(raw_probability * 100).toFixed(1)}%</p>
      </div>

      {chartData.length > 0 && (
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-100 mb-4">Feature Importance (SHAP)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" stroke="#9CA3AF" />
              <YAxis dataKey="feature" type="category" width={100} stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                itemStyle={{ color: '#F3F4F6' }}
              />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default RiskDashboard;
