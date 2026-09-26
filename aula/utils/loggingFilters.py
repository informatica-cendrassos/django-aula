import logging

from django.core.exceptions import DisallowedHost


class StopSuspiciousOperation(logging.Filter):
    def filter(self, record):
        if record.exc_info:
            exc_value = record.exc_info[1]
            if isinstance(exc_value, DisallowedHost):
                return False
        if record.name == "django.security.DisallowedHost":
            return False
        return True
