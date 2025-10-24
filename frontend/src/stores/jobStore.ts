/**
 * Zustand store for job state management
 */

import { create } from 'zustand';
import type { Job, PresentationStructure } from '../types';

interface JobStore {
  // Current job state
  currentJob: Job | null;
  isEditing: boolean;

  // Actions
  setCurrentJob: (job: Job | null) => void;
  updateJobStatus: (status: string, progress: number, step?: string) => void;
  updateStructure: (structure: PresentationStructure) => void;
  setEditing: (isEditing: boolean) => void;
  reset: () => void;
}

export const useJobStore = create<JobStore>((set) => ({
  currentJob: null,
  isEditing: false,

  setCurrentJob: (job) => set({ currentJob: job }),

  updateJobStatus: (status, progress, step) =>
    set((state) => ({
      currentJob: state.currentJob
        ? {
            ...state.currentJob,
            status: status as Job['status'],
            progress_percentage: progress,
            current_step: step,
          }
        : null,
    })),

  updateStructure: (structure) =>
    set((state) => ({
      currentJob: state.currentJob
        ? { ...state.currentJob, structure }
        : null,
    })),

  setEditing: (isEditing) => set({ isEditing }),

  reset: () => set({ currentJob: null, isEditing: false }),
}));
