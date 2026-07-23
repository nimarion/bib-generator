export interface Assets {
  fonts: string[];
  headers: string[];
  footers: string[];
  presets: string[];
}

export interface Runner {
  firstname: string;
  lastname: string;
  font: string;
  footer: string;
  header: string;
}

export interface ExportProgress {
  active: boolean;
  current: number;
  total: number;
  percent: number;
  statusText: string;
  startTime: number;
  etaSeconds: number | null;
}

export interface ImportStatus {
  type: 'success' | 'error';
  message: string;
}
