export interface TimezoneOption {
  value: string;
  label: string;
  city: string;
  offset: string;
}

const TIMEZONE_CITIES: Record<string, string> = {
  "America/Bogota": "Bogotá",
  "America/Mexico_City": "Ciudad de México",
  "America/Argentina/Buenos_Aires": "Buenos Aires",
  "America/Santiago": "Santiago",
  "America/Lima": "Lima",
  "America/Caracas": "Caracas",
  "America/Panama": "Panamá",
  "Europe/Madrid": "Madrid",
  "America/New_York": "Nueva York",
};

const TIMEZONE_VALUES = [
  "America/Bogota",
  "America/Mexico_City",
  "America/Argentina/Buenos_Aires",
  "America/Santiago",
  "America/Lima",
  "America/Caracas",
  "America/Panama",
  "Europe/Madrid",
  "America/New_York",
];

function offsetLabel(timeZone: string, date = new Date()): string {
  try {
    return (
      new Intl.DateTimeFormat("en-US", {
        timeZone,
        timeZoneName: "shortOffset",
      })
        .formatToParts(date)
        .find((part) => part.type === "timeZoneName")?.value ?? ""
    );
  } catch {
    return "";
  }
}

export function buildTimezoneOption(value: string): TimezoneOption {
  const city = TIMEZONE_CITIES[value] ?? value;
  const offset = offsetLabel(value);

  return {
    value,
    city,
    offset,
    label: offset ? `${city} (${offset})` : city,
  };
}

export const TIMEZONES: TimezoneOption[] = TIMEZONE_VALUES.map(
  buildTimezoneOption,
);

export function timezoneLabel(value: string): string {
  return (
    TIMEZONES.find((timezone) => timezone.value === value)?.label ??
    buildTimezoneOption(value).label
  );
}
