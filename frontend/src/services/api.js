import axios from 'axios';

const API_BASE = '/api';

export const predictPatient = async (data) => {
  const response = await axios.post(`${API_BASE}/predict`, data);
  return response.data;
};

export const uploadPatientFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const sendChatMessage = async (context, query) => {
  const response = await axios.post(`${API_BASE}/chat`, { context, query });
  return response.data;
};

export const getModelInfo = async () => {
  const response = await axios.get(`${API_BASE}/model-info`);
  return response.data;
};
