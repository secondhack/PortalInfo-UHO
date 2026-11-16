from .models import record


class SecurityAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(('/api/admin/', '/api/me/', '/auth/', '/portal-auth/')):
            response['Cache-Control'] = 'no-store'
        if response.status_code in (401, 403) and request.path.startswith(('/api/', '/auth/', '/portal-auth/')):
            record(request, 'access.denied', request.path)
        return response
