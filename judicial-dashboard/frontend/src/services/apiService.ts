import axios from 'axios';

// Use relative URLs in production (same domain), absolute in dev
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (process.env.NODE_ENV === 'production' ? '' : 'http://127.0.0.1:8010');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Case {
  case_id: string;
  court_id: string;
  location_region: string;
  case_type: string;
  filing_date: string;
  resolution_date: string;
  num_hearings: number;
  num_adjournments: number;
  judge_id_hashed: string;
  outcome_category: string;
  time_to_resolution_days: number;
}

export interface AnalyticsSummary {
  total_cases: number;
  avg_resolution_time: number;
  cases_by_type: Record<string, number>;
  cases_by_region: Record<string, number>;
  avg_hearings: number;
  avg_adjournments: number;
  resolved_cases?: number;
  disposal_rate?: number; // 0..1
}

export interface Predictions {
  model_accuracy: number;
  predicted_avg_resolution: number;
  confidence_interval: number[];
}

export interface TrainResult {
  linear_regression?: { mae: number; r2_score: number; rmse: number };
  random_forest?: { mae: number; r2_score: number; rmse: number; feature_importance?: Record<string, number> };
  training_samples?: number;
  test_samples?: number;
  best_model?: string;
}

export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Get all cases
  async getCases(): Promise<{ cases: Case[]; total: number }> {
    const response = await api.get('/api/cases');
    return response.data;
  },

  // Get specific case
  async getCase(caseId: string): Promise<{ case: Case }> {
    const response = await api.get(`/api/cases/${caseId}`);
    return response.data;
  },

  // Get analytics summary
  async getAnalyticsSummary(): Promise<{ summary: AnalyticsSummary }> {
    const response = await api.get('/api/analytics/summary');
    return response.data;
  },

  async getTimeSeries(params?: { start_date?: string; end_date?: string; region?: string; case_type?: string }): Promise<{ series: Array<{ month: string; cases: number; resolution: number }> }> {
    const response = await api.get('/api/analytics/time-series', { params });
    return response.data;
  },

  async getResolutionDistribution(params?: { start_date?: string; end_date?: string; region?: string; case_type?: string }): Promise<{ distribution: Array<{ category: string; count: number }> }> {
    const response = await api.get('/api/analytics/resolution-distribution', { params });
    return response.data;
  },

  async getCourtPerformance(params?: { start_date?: string; end_date?: string; region?: string; case_type?: string }): Promise<{ performance: Array<{ court: string; rate: number }> }> {
    const response = await api.get('/api/analytics/court-performance', { params });
    return response.data;
  },

  async exportMetricsToReport(): Promise<{ message: string; report_path: string }> {
    const response = await api.post('/api/report/export-metrics');
    return response.data;
  },

  async submitFeedback(payload: { name?: string; role?: string; rating?: number; comments?: string }): Promise<{ message: string }> {
    const response = await api.post('/api/feedback', payload);
    return response.data;
  },

  // Get predictions
  async getPredictions(): Promise<{ predictions: Predictions }> {
    const response = await api.get('/api/analytics/predictions');
    return response.data;
  },

  // Train on current dataset (sample or loaded) on the server
  async trainModels(): Promise<{ training_result: TrainResult }> {
    const response = await api.post('/api/analytics/train-models');
    return response.data;
  },

  // Compare models
  async getModelComparison(): Promise<{ comparison: any }> {
    const response = await api.get('/api/analytics/model-comparison');
    return response.data;
  },

  // Model insights
  async getModelInsights(): Promise<{ insights: any }> {
    const response = await api.get('/api/analytics/model-insights');
    return response.data;
  },

  // Reset all data and models on the backend
  async resetData(): Promise<{ message: string }> {
    const response = await api.post('/api/admin/reset-data');
    return response.data;
  },

  // Get courts
  async getCourts(): Promise<{ courts: any[] }> {
    const response = await api.get('/api/courts');
    return response.data;
  },

  // Upload dataset and train models
  async uploadAndTrain(file: File): Promise<{ training_result: any; saved_path: string; preview?: any[] }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/analytics/upload-and-train', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Train from file path on the server
  async trainFromFilePath(filePath: string): Promise<{ training_result: any }> {
    const form = new FormData();
    form.append('file_path', filePath);
    const response = await api.post('/api/analytics/train-from-file', form);
    return response.data;
  },

  // Upload a PDF file
  async uploadPdf(file: File): Promise<{ message: string; saved_path: string; filename: string; public_url: string }> {
    const form = new FormData();
    form.append('file', file);
    const response = await api.post('/api/files/upload-pdf', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Upload a PDF and train immediately
  async uploadPdfAndTrain(file: File): Promise<{ message: string; rows: number; training_result: TrainResult; preview?: any[] }> {
    const form = new FormData();
    form.append('file', file);
    const response = await api.post('/api/analytics/upload-pdf-and-train', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Upload Excel/CSV and train immediately
  async uploadDataAndTrain(file: File): Promise<{ message: string; saved_path?: string; training_result: TrainResult; preview?: any[] }> {
    const form = new FormData();
    form.append('file', file);
    const response = await api.post('/api/analytics/upload-data-and-train', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export default apiService;
