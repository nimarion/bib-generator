import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import type { Runner } from './types';
export const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL as string) || 'https://bib-api.pfingstsportfest.de';

export const DEFAULT_FONTS = [
  "example/BebasNeue-Regular.ttf",
  "example/agency_fb.ttf"
];

export const DEFAULT_HEADERS = [
  "example/globus.png",
  "example/bitburger.png",
  "example/nta.png",
  "header/header.png"
];

export const DEFAULT_FOOTERS = [
  "example/footer.png",
  "footer/footer.png"
];

export const DEFAULT_RUNNERS: Runner[] = [
  {
    firstname: "Usain",
    lastname: "Bolt",
    font: "example/BebasNeue-Regular.ttf",
    header: "example/globus.png",
    footer: "example/footer.png"
  },
  {
    firstname: "Shelly-Ann",
    lastname: "Fraser",
    font: "example/agency_fb.ttf",
    header: "example/bitburger.png",
    footer: "example/footer.png"
  }
];

export const PRESETS: Record<string, [number, number]> = {
  A4: [4960, 3508],
  A5: [3508, 2480],
  A6: [2480, 1748],
  letter: [3300, 2550]
};

export const getFontOptions = (discovered: string[], currentVal: string): string[] => {
  const list = [...DEFAULT_FONTS, ...discovered];
  if (currentVal && !list.includes(currentVal)) list.push(currentVal);
  return Array.from(new Set(list.filter(Boolean)));
};

export const getHeaderOptions = (discovered: string[], currentVal: string): string[] => {
  const list = [...DEFAULT_HEADERS, ...discovered];
  if (currentVal && !list.includes(currentVal)) list.push(currentVal);
  return Array.from(new Set(list.filter(Boolean)));
};

export const getFooterOptions = (discovered: string[], currentVal: string): string[] => {
  const list = [...DEFAULT_FOOTERS, ...discovered];
  if (currentVal && !list.includes(currentVal)) list.push(currentVal);
  return Array.from(new Set(list.filter(Boolean)));
};

export const normalizeHeader = (header: string): keyof Runner | null => {
  const h = header.trim().toLowerCase().replace(/[\s_\-]/g, '');
  if (['firstname', 'first', 'fname', 'givenname', 'vorname'].includes(h)) return 'firstname';
  if (['lastname', 'last', 'lname', 'surname', 'familyname', 'nachname', 'name'].includes(h)) return 'lastname';
  if (['font', 'fontpath', 'ttf', 'otf', 'schrift'].includes(h)) return 'font';
  if (['header', 'headerpath', 'head', 'logo', 'headerlogo'].includes(h)) return 'header';
  if (['footer', 'footerpath', 'foot', 'footerlogo'].includes(h)) return 'footer';
  return null;
};

export const downloadSampleCSV = (): void => {
  const csvContent = "firstname,lastname,font,footer,header\n" +
    "Usain,Bolt,example/BebasNeue-Regular.ttf,example/footer.png,example/globus.png\n" +
    "Shelly-Ann,Fraser,example/agency_fb.ttf,example/footer.png,example/bitburger.png\n" +
    "Joshua,Abuaku,example/agency_fb.ttf,example/footer.png,example/bitburger.png";
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', 'sample_entrants.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const downloadSampleXLSX = (): void => {
  const sampleData = [
    {
      firstname: "Usain",
      lastname: "Bolt",
      font: "example/BebasNeue-Regular.ttf",
      footer: "example/footer.png",
      header: "example/globus.png"
    },
    {
      firstname: "Shelly-Ann",
      lastname: "Fraser",
      font: "example/agency_fb.ttf",
      footer: "example/footer.png",
      header: "example/bitburger.png"
    },
    {
      firstname: "Joshua",
      lastname: "Abuaku",
      font: "example/agency_fb.ttf",
      footer: "example/footer.png",
      header: "example/bitburger.png"
    }
  ];

  const worksheet = XLSX.utils.json_to_sheet(sampleData, {
    header: ["firstname", "lastname", "font", "footer", "header"]
  });
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Entrants");
  XLSX.writeFile(workbook, "sample_entrants.xlsx");
};

export const parseFileToRunners = (
  file: File,
  defaultFont: string,
  defaultHeader: string,
  defaultFooter: string,
  onSuccess: (runners: Runner[], filename: string) => void,
  onError: (msg: string) => void
): void => {
  const name = file.name;
  const lowerName = name.toLowerCase();

  const processRawRows = (rawRows: Record<string, any>[]) => {
    if (!rawRows || rawRows.length === 0) {
      onError(`File "${name}" contains no records.`);
      return;
    }

    const sample = rawRows[0];
    const keys = Object.keys(sample);
    const mapping: Record<string, keyof Runner> = {};

    keys.forEach(key => {
      const norm = normalizeHeader(key);
      if (norm) {
        mapping[key] = norm;
      }
    });

    const parsedRunners: Runner[] = rawRows
      .map(row => {
        const runner: Runner = {
          firstname: '',
          lastname: '',
          font: defaultFont || DEFAULT_FONTS[0],
          header: defaultHeader || DEFAULT_HEADERS[0],
          footer: defaultFooter || DEFAULT_FOOTERS[0]
        };

        Object.entries(mapping).forEach(([origKey, targetKey]) => {
          const val = row[origKey];
          if (val !== undefined && val !== null && String(val).trim() !== '') {
            runner[targetKey] = String(val).trim();
          }
        });

        return runner;
      })
      .filter(r => r.lastname || r.firstname);

    if (parsedRunners.length === 0) {
      onError(`Could not extract runners from "${name}". Ensure pre-defined headers (firstname, lastname, font, footer, header) are used.`);
      return;
    }

    onSuccess(parsedRunners, name);
  };

  if (lowerName.endsWith('.csv') || lowerName.endsWith('.tsv') || lowerName.endsWith('.txt')) {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: false,
      complete: (results) => processRawRows(results.data as Record<string, any>[]),
      error: (err) => onError(`CSV Parsing error: ${err.message}`)
    });
  } else if (lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        const rawJson = XLSX.utils.sheet_to_json<Record<string, any>>(worksheet, { defval: '' });
        processRawRows(rawJson);
      } catch (err: any) {
        onError(`Excel Parsing error: ${err.message}`);
      }
    };
    reader.readAsArrayBuffer(file);
  } else {
    onError('Unsupported file format. Please upload a .csv or .xlsx file.');
  }
};
