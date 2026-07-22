import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const RiskDashboard = ({ prediction }) => {
  if (!prediction) return null;

  const { severity_score, urgency_level, interpretation, shap_values } = prediction;

  const getSeverityColor = (score) => {
    if (score >= 70) return 'bg-red-600';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getUrgencyColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'immediate': return 'text-red-600 font-bold';
      case 'increased': return 'text-yellow-600 font-semibold';
      default: return 'text-green-600';
    }
  };

  const chartData = shap_values
    ? Object.entries(shap_values)
        .map(([feature, value]) => ({ feature, value: Math.abs(value) }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
    : [];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Clinical Severity Score</h3>
        <div className="relative pt-1">
          <div className="flex mb-2 items-center justify-between">
            <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-gray-600 bg-gray-200">
              Risk Level
            </span>
            <span className="text-xs font-semibold inline-block text-gray-600">
              {severity_score}%
            </span>
          </div>
          <div className="overflow-hidden h-4 mb-4 text-xs flex rounded bg-gray-200">
            <div
              style={{ width: `${severity_score}%` }}
              className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${getSeverityColor(severity_score)} transition-all duration-500`}
            ></div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Urgency Level</h3>
        <p className={`text-xl ${getUrgencyColor(urgency_level)}`}>{urgency_level}</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Clinical Interpretation</h3>
        <p className="text-gray-700">{interpretation}</p>
      </div>

      {chartData.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Feature Importance (SHAP)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="feature" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default RiskDashboard;
