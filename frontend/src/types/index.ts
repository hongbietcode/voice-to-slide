/**
 * TypeScript type definitions for Voice-to-Slide
 */

export interface Job {
  job_id: string;
  status: 'pending' | 'transcribing' | 'analyzing' | 'editing' | 'generating' | 'completed' | 'failed';
  progress_percentage: number;
  current_step?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;

  // Available after transcription
  transcription_preview?: string;

  // Available after analysis
  structure?: PresentationStructure;

  // Available after completion
  pptx_file_url?: string;
  total_slides?: number;
  images_fetched?: number;
  processing_time_seconds?: number;

  // Error details
  error_message?: string;
}

export interface PresentationStructure {
  title: string;
  slides: Slide[];
}

export interface Slide {
  title: string;
  bullet_points: string[];
  image_theme?: string;
}

export interface JobCreateRequest {
  theme?: string;
  include_images?: boolean;
  interactive_mode?: boolean;
  save_transcription?: boolean;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message: string;
  estimated_time_seconds: number;
}

export interface Theme {
  name: string;
  description: string;
  preview_url: string;
}

export interface WebSocketMessage {
  type: 'connected' | 'progress' | 'structure_ready' | 'completed' | 'error';
  job_id: string;
  status?: string;
  progress_percentage?: number;
  current_step?: string;
  structure?: PresentationStructure;
  pptx_file_url?: string;
  error_message?: string;
  error_code?: string;
  message?: string;
  timestamp?: string;
}
