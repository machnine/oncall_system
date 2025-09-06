"""Constants and configuration for the records app"""

# Assignment Type Configuration - This can be moved to a database table later if needed
ASSIGNMENT_TYPE_CONFIG = {
    "donor": {
        "name": "Donor",
        "color": "success",
        "icon": "bi-person-check",
        "description": "Blood/organ donor assignments",
    },
    "recipient": {
        "name": "Recipient",
        "color": "info",
        "icon": "bi-person-fill",
        "description": "Blood/organ recipient assignments",
    },
    "lab_task": {
        "name": "Lab Task",
        "color": "warning",
        "icon": "bi-thermometer-low",
        "description": "Laboratory task assignments",
    },
}

BOOTSTRAP_COLORS = [
    ("primary", "Primary (Blue)"),
    ("secondary", "Secondary (Gray)"),
    ("success", "Success (Green)"),
    ("danger", "Danger (Red)"),
    ("warning", "Warning (Yellow)"),
    ("info", "Info (Cyan)"),
    ("light", "Light"),
    ("dark", "Dark"),
]