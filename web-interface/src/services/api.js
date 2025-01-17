import axios from 'axios';

const API_BASE_URL = '/api'; // Update to relative path

export const fetchProblems = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/problems`);
        return response.data;
    } catch (error) {
        console.error('Error fetching problems:', error);
        throw error;
    }
};

export const submitReport = async (reportData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/reports`, reportData);
        return response.data;
    } catch (error) {
        console.error('Error submitting report:', error);
        throw error;
    }
};

export const fetchAnalysisData = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/analysis`);
        return response.data;
    } catch (error) {
        console.error('Error fetching analysis data:', error);
        throw error;
    }
};

export const fetchReports = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/reports`);
        return response.data;
    } catch (error) {
        console.error('Error fetching reports:', error);
        throw error;
    }
};

const api = axios.create({
    baseURL: '',
});


export default api;