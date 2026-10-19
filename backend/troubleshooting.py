"""Deterministic keyword-based troubleshooting rules.

This module intentionally uses transparent rules rather than a remote AI API.
"""

RULES = [
    {
        "category": "network",
        "title": "Network connectivity",
        "keywords": (
            "wifi", "wi-fi", "internet", "network", "no connection",
            "can't connect", "cannot connect", "connectivity", "offline"
        ),
        "answer": "Try these checks in order:",
        "steps": [
            "Check whether Wi-Fi is enabled and airplane mode is off.",
            "Confirm whether other devices can connect to the same network.",
            "If you are authorized to do so, restart the router and wait for it to reconnect.",
            "Disconnect and reconnect to the network, then retry the task."
        ],
        "follow_up": "Do you see an error message, or is the network not visible at all?"
    },
    {
        "category": "login",
        "title": "Login or authentication",
        "keywords": (
            "login", "log in", "sign in", "signin", "password",
            "locked out", "authentication", "account access", "otp"
        ),
        "answer": "Check the account and authentication steps:",
        "steps": [
            "Check that the username and the selected account are correct.",
            "Verify that Caps Lock and the keyboard layout are correct before re-entering the password.",
            "Use the official password-reset or account-recovery flow if needed.",
            "If multi-factor authentication fails, check the device time and use the official recovery option."
        ],
        "follow_up": "Is the password rejected, or does the failure happen during OTP or multi-factor verification?"
    },
    {
        "category": "performance",
        "title": "Slow device or application",
        "keywords": (
            "slow", "lag", "lagging", "freezing", "freeze", "takes too long",
            "performance", "hang", "hanging", "unresponsive"
        ),
        "answer": "Try these basic performance checks:",
        "steps": [
            "Save your work before making changes.",
            "Close unused applications and browser tabs.",
            "Check available storage and whether system updates are pending.",
            "Restart the device if it is safe to do so, then check whether the issue continues."
        ],
        "follow_up": "Is the whole device slow, or only one application or website?"
    },
    {
        "category": "application",
        "title": "Application error or crash",
        "keywords": (
            "application", "app", "software", "crash", "crashing",
            "error", "not opening", "won't open", "wont open",
            "not working", "failed to launch"
        ),
        "answer": "Use these checks to narrow down the application issue:",
        "steps": [
            "Record the exact error message and the action that caused it.",
            "Close and reopen the application, after saving any available work.",
            "Check whether an update is available from the official source.",
            "If the problem persists, collect the steps to reproduce it and report the error to support."
        ],
        "follow_up": "What is the application name, and what exact error message appears?"
    },
    {
        "category": "printer",
        "title": "Printer or print-job issue",
        "keywords": (
            "printer", "printing", "print job", "paper jam",
            "not printing", "printer offline", "ink"
        ),
        "answer": "Check the printer and print queue:",
        "steps": [
            "Confirm the printer is powered on and shows no paper or ink warning.",
            "Check the cable or network connection and confirm the correct printer is selected.",
            "Review the print queue for paused or stuck jobs.",
            "Print a test page if permitted by your device or workplace policy."
        ],
        "follow_up": "Does the printer show as offline, or does the job remain stuck in the queue?"
    },
]


def diagnose(message: str) -> dict:
    """Return the first matching rule, or a safe fallback response."""
    normalized = " ".join(message.lower().strip().split())

    for rule in RULES:
        if any(keyword in normalized for keyword in rule["keywords"]):
            return {
                "category": rule["category"],
                "title": rule["title"],
                "answer": rule["answer"],
                "steps": list(rule["steps"]),
                "follow_up": rule["follow_up"],
            }

    return {
        "category": "unknown",
        "title": "More information needed",
        "answer": (
            "I don't have a matching troubleshooting guide for that issue yet. "
            "I can currently help with network, login, performance, application, and printer problems."
        ),
        "steps": [
            "Describe what you were trying to do.",
            "Include the device or application involved.",
            "Share the exact error message, but do not include passwords, OTPs, or other secrets."
        ],
        "follow_up": "Which device or application is affected, and what happens when you try?"
    }
