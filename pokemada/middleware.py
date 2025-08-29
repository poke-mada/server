# app/middleware.py
from django.utils import timezone
from zoneinfo import ZoneInfo

class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.session.get("django_timezone")
        if tzname:
            try:
                timezone.activate(ZoneInfo(tzname))
            except Exception:
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)
