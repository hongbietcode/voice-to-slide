/**
 * API client for Voice-to-Slide backend
 */

import axios from 'axios';
import type { Job, JobResponse, Theme } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  /**
   * Generate a new presentation
   */
  generatePresentation: async (
    audioFile: File,
    options: {
      theme?: string;
      includeImages?: boolean;
      interactiveMode?: boolean;
      saveTranscription?: boolean;
    }
  ): Promise<JobResponse> => {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('theme', options.theme || 'Modern Professional');
    formData.append('include_images', String(options.includeImages !== false));
    formData.append('interactive_mode', String(options.interactiveMode || false));
    formData.append('save_transcription', String(options.saveTranscription !== false));

    const response = await apiClient.post<JobResponse>('/api/v1/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Get job status
   */
  getJobStatus: async (jobId: string): Promise<Job> => {
    const response = await apiClient.get<Job>(`/api/v1/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Edit structure (interactive mode)
   */
  editStructure: async (
    jobId: string,
    feedback: string
  ): Promise<{ updated_structure: any; edit_number: number; message: string }> => {
    const response = await apiClient.post(`/api/v1/jobs/${jobId}/edit-structure`, {
      feedback,
    });
    return response.data;
  },

  /**
   * Confirm generation (interactive mode)
   */
  confirmGeneration: async (jobId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/api/v1/jobs/${jobId}/confirm-generation`);
    return response.data;
  },

  /**
   * Delete job
   */
  deleteJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/v1/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Get available themes
   */
  getThemes: async (): Promise<Theme[]> => {
    const response = await apiClient.get<{ themes: Theme[] }>('/api/v1/themes');
    return response.data.themes;
  },

  /**
   * Get download URL for PPTX
   */
  getDownloadUrl: (jobId: string): string => {
    return `${API_BASE_URL}/api/v1/download/${jobId}`;
  },

  /**
   * Get transcription download URL
   */
  getTranscriptionUrl: (jobId: string): string => {
    return `${API_BASE_URL}/api/v1/download/${jobId}/transcription`;
  },

  /**
   * Get slide preview URL
   */
  getSlidePreviewUrl: (jobId: string, slideNumber: number): string => {
    return `${API_BASE_URL}/api/v1/preview/${jobId}/slide/${slideNumber}`;
  },
};

export default api;
