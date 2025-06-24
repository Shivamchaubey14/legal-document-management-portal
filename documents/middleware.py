# logs/middleware.py
import json
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from documents.models import UserActionLog


class ActionLoggingMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.user.is_authenticated and not request.path.startswith(('/admin', '/static', '/media')):
            try:
                if request.method in ['POST', 'PUT', 'PATCH']:
                    content_type = request.META.get("CONTENT_TYPE", "")
                    if "application/json" in content_type:
                        try:
                            data = json.loads(request.body.decode('utf-8'))
                        except:
                            data = {}
                    else:
                        data = request.POST.dict()
                else:
                    data = request.GET.dict()

                # Save the log
                UserActionLog.objects.create(
                    user=request.user,
                    path=request.path,
                    method=request.method,
                    timestamp=now(),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    data=json.dumps(data, indent=2),  # Store raw data
                    changes=", ".join([f"{k}: {v}" for k, v in data.items()]) or "No data submitted"
                )
            except Exception as e:
                print(f"[Logging Error] {e}")

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get("REMOTE_ADDR")
