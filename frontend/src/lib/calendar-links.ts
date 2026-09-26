export type CalendarLinks = {
  google: string;
  microsoft: string;
  ics: string;
};

function utcStamp(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return (
    `${date.getUTCFullYear()}${pad(date.getUTCMonth() + 1)}${pad(date.getUTCDate())}` +
    `T${pad(date.getUTCHours())}${pad(date.getUTCMinutes())}${pad(date.getUTCSeconds())}Z`
  );
}

function icsText(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/,/g, "\\,").replace(/;/g, "\\;");
}

export function buildCalendarLinks(input: {
  title: string;
  start: Date;
  end: Date;
  details?: string;
  location?: string;
}): CalendarLinks {
  const title = encodeURIComponent(input.title);
  const details = encodeURIComponent(input.details || "");
  const location = encodeURIComponent(input.location || "");
  const start = utcStamp(input.start);
  const end = utcStamp(input.end);
  const startIso = encodeURIComponent(input.start.toISOString());
  const endIso = encodeURIComponent(input.end.toISOString());

  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//mybooks//frappe-appointment//EN",
    "BEGIN:VEVENT",
    `UID:${start}-${end}@frappe-appointment`,
    `DTSTAMP:${utcStamp(new Date())}`,
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${icsText(input.title)}`,
    `DESCRIPTION:${icsText(input.details || "")}`,
    `LOCATION:${icsText(input.location || "")}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");

  return {
    google: `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${start}/${end}&details=${details}&location=${location}`,
    microsoft: `https://outlook.office.com/calendar/0/deeplink/compose?path=/calendar/action/compose&rru=addevent&startdt=${startIso}&enddt=${endIso}&subject=${title}&body=${details}&location=${location}`,
    ics,
  };
}
