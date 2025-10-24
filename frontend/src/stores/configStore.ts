/**
 * Zustand store for configuration state
 */

import { create } from 'zustand';
import type { Theme } from '../types';

interface ConfigStore {
  // Configuration
  theme: string;
  includeImages: boolean;
  saveTranscription: boolean;
  interactiveMode: boolean;

  // Available options
  availableThemes: Theme[];

  // Actions
  setTheme: (theme: string) => void;
  toggleImages: () => void;
  toggleInteractive: () => void;
  toggleSaveTranscription: () => void;
  setAvailableThemes: (themes: Theme[]) => void;
}

export const useConfigStore = create<ConfigStore>((set) => ({
  theme: 'Modern Professional',
  includeImages: true,
  saveTranscription: true,
  interactiveMode: false,
  availableThemes: [],

  setTheme: (theme) => set({ theme }),
  toggleImages: () => set((state) => ({ includeImages: !state.includeImages })),
  toggleInteractive: () => set((state) => ({ interactiveMode: !state.interactiveMode })),
  toggleSaveTranscription: () => set((state) => ({ saveTranscription: !state.saveTranscription })),
  setAvailableThemes: (themes) => set({ availableThemes: themes }),
}));
