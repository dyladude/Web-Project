import time
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Service


class Command(BaseCommand):
    help = "Run pull-based health checks for all public pull services"

    def handle(self, *args, **options):
        services = Service.objects.filter(
            check_type=Service.CHECK_PULL,
            is_public=True,
        )

        results = []

        for service in services:
            start = time.monotonic()
            status = Service.STATUS_DOWN
            response_time_ms = None

            try:
                with urllib.request.urlopen(service.url, timeout=5) as response:
                    elapsed = (time.monotonic() - start) * 1000
                    response_time_ms = int(elapsed)

                    if 200 <= response.status < 400:
                        status = Service.STATUS_UP
                    service.last_error = None  # clear previous error if successful
            except (urllib.error.URLError, ValueError) as e:
                status = Service.STATUS_DOWN
                service.last_error = str(e)

            service.last_status = status
            service.last_checked = timezone.now()
            service.response_time_ms = response_time_ms
            service.save(update_fields=["last_status", "last_checked", "response_time_ms", "last_error"])

            results.append(f"{service.name}: {status}")

        self.stdout.write(self.style.SUCCESS(f"Checked {len(results)} service(s)."))
        for line in results:
            self.stdout.write(line)