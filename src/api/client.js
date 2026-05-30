import axios from 'axios';

// Axios instance — swap VITE_API_URL in .env to point at your real backend
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8005',
});

// Attach JWT from localStorage on every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('wf_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
