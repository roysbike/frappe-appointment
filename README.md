<div align="center">
<img src="frappe_appointment/public/frappe-appointment-logo.png" height="128" alt="Frappe Appointment">
<h2>Frappe Appointment</h2>
   Frappe app designed to streamline meeting scheduling with smart integrations.
</div>

**English** | [Русский](README.ru.md)
<br>
<div align="center">
<img src="frappe_appointment/public/featured-image.png" width="1050" alt="Frappe Appointment">
</div>

## What's new in this fork

Scheduling can use a Namecheap/cPanel calendar instead of Google.

- **Namecheap CalDAV.** On User Appointment Availability set Calendar to Namecheap CalDAV. Server URL is `https://<domain>:2080`. The mailbox is the full address. Events are written to `https://<domain>:2080/calendars/<mailbox>/calendar`, the same collection Apple Calendar syncs.
- **Google is optional.** In Appointment Settings, uncheck Enable Google Calendar when it is not used. A Namecheap calendar does not open the Google Calendar document for a guest.
- **Public booking page.** `/schedule/in/<slug>` loads for a guest. The page reads the public profile only.
- **Meeting, not a generic event.** A new booking is an Event with category Meeting.
- **Real UTC on the calendar.** 14:00 in Asia/Dubai is written as 10:00Z. Apple Calendar shows 14:00 again. An event already stored with the old stamp does not move.
- **Add to calendar.** After booking, the guest gets Google, Apple (`.ics` download), and Microsoft Outlook links.
- **Phone.** The contact form has an optional Phone field. The number is stored in the Event description as `Phone: +971 ...`, next to the meet link. No extra field is required.
- **One booking owns that time.** An open meeting on that calendar removes the slot. Cancelling the meeting frees it. Limit Booking Frequency `-1` means no daily cap. It does not allow a second booking of the same time.
- **Email timezone.** The confirmation uses the timezone selected on the booking page, for example `Tuesday, 29 September 2026 at 02:00 pm (Dubai)`.

## Key Features

- **Google Calendar Integration**: Syncs with Google Calendar to prevent scheduling conflicts.
- **ERPNext Leave Integration**: Blocks time slots based on ERPNext leave records.
- **Zoom & Google Meet Integration**: Auto-generates meeting links for Zoom and Google Meet.
- **Rescheduling Support**: Enables participants to reschedule meetings easily.


## Installation

Run the following command to install the app.

```bash
bench get-app git@github.com:roysbike/frappe-appointment.git
bench --site [site-name] install-app frappe_appointment
bench --site [site-name] migrate
bench restart
```

For local development, check out our dev-tool for seamlessly building Frappe apps: [frappe-manager](https://github.com/rtCamp/Frappe-Manager)  
NOTE: If using `frappe-manager`, you might require to `fm restart` to provision the worker queues.

## System Setup
Visit the detailed [System Setup Guide](https://github.com/rtCamp/frappe-appointment/wiki/System-Setup) on wiki.

## Documentation

Please refer to our [Wiki](https://github.com/rtCamp/frappe-appointment/wiki/) for details.

## Contribution Guide

Please read [contribution.md](./CONTRIBUTING.md) for details.

## License

This project is licensed under the [AGPLv3 License](./LICENSE).
