import frappe

_REPLACEMENTS = (
    (
        "Your appointment is scheduled for {{ formatted_starts_on.strftime('%A') }}, "
        "{{ formatted_starts_on.strftime('%d %B %Y') }} at "
        '{{ formatted_starts_on.strftime("%I:%M %P") }} IST.',
        "Your appointment is scheduled for {{ appointment_when }}.",
    ),
    (
        "The appointment is scheduled for {{ formatted_starts_on.strftime('%A') }}, "
        "{{ formatted_starts_on.strftime('%d %B %Y') }} at "
        '{{ formatted_starts_on.strftime("%I:%M %P") }} IST.',
        "The appointment is scheduled for {{ appointment_when }}.",
    ),
)


def execute():
    """Use the timezone the guest picked instead of a hardcoded IST label."""
    names = frappe.get_all(
        "Email Template",
        filters={"name": ["in", ["[Default] Appointment Scheduled", "[Default] Appointment Scheduled - Organisers"]]},
        pluck="name",
    )
    for name in names:
        doc = frappe.get_doc("Email Template", name)
        changed = False
        for field in ("response", "response_html"):
            text = doc.get(field) or ""
            updated = text
            for old, new in _REPLACEMENTS:
                updated = updated.replace(old, new)
            if updated != text:
                doc.set(field, updated)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
