<div align="center">
<img src="frappe_appointment/public/frappe-appointment-logo.png" height="128" alt="Frappe Appointment">
<h2>Frappe Appointment</h2>
   Приложение Frappe для записи на встречи и календарей.
</div>

[English](README.md) | **Русский**

<br>
<div align="center">
<img src="frappe_appointment/public/featured-image.png" width="1050" alt="Frappe Appointment">
</div>

## Что нового в этом форке

Запись может идти в календарь Namecheap/cPanel, без Google.

- **Namecheap CalDAV.** В User Appointment Availability календарь — Namecheap CalDAV. Адрес сервера: `https://<domain>:2080`. Ящик — полный адрес почты. События пишутся в `https://<domain>:2080/calendars/<mailbox>/calendar`, ту же коллекцию, что синхронизирует Apple Calendar.
- **Google не обязателен.** В Appointment Settings снимите Enable Google Calendar, если Google не используется. Календарь Namecheap не открывает документ Google Calendar для гостя.
- **Публичная страница.** `/schedule/in/<slug>` открывается без входа в Desk. Читаются только публичные поля профиля.
- **Категория Meeting.** Новая бронь — это Event с категорией Meeting.
- **Настоящее UTC в календаре.** 14:00 Asia/Dubai записывается как 10:00Z. Apple Calendar снова показывает 14:00. Уже сохранённое событие со старой меткой само не сдвинется.
- **Добавить в календарь.** После брони гость получает ссылки Google, Apple (файл `.ics`) и Microsoft Outlook.
- **Телефон.** В форме контактов есть необязательное поле Phone. Номер пишется в Description встречи строкой `Phone: +971 ...`, рядом со ссылкой. Отдельное поле заводить не нужно.
- **Одно время — одна бронь.** Открытая встреча в этом календаре убирает слот. Отмена встречи слот освобождает. Limit Booking Frequency `-1` — это отсутствие дневного лимита, а не разрешение занять то же время второй раз.
- **Пояс в письме.** Подтверждение использует пояс, выбранный на странице записи, например `Tuesday, 29 September 2026 at 02:00 pm (Dubai)`.

## Возможности

- **Google Calendar.** Синхронизация с Google Calendar, чтобы не ставить встречи поверх занятого времени.
- **Отпуска ERPNext.** Слоты закрываются по записям отпусков ERPNext.
- **Zoom и Google Meet.** Ссылки на Zoom и Google Meet создаются при брони.
- **Перенос.** Участник может перенести встречу.

## Установка

```bash
bench get-app git@github.com:roysbike/frappe-appointment.git
bench --site [site-name] install-app frappe_appointment
bench --site [site-name] migrate
bench restart
```

Для локальной разработки: [frappe-manager](https://github.com/rtCamp/Frappe-Manager).  
Если используете `frappe-manager`, после установки может понадобиться `fm restart`, чтобы поднять очереди воркеров.

## Настройка

Подробности: [System Setup](https://github.com/rtCamp/frappe-appointment/wiki/System-Setup) в wiki исходного проекта.

## Документация

[Wiki](https://github.com/rtCamp/frappe-appointment/wiki/) исходного проекта.

## Участие

См. [contribution.md](./CONTRIBUTING.md).

## Лицензия

[AGPLv3](./LICENSE).
