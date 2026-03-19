class TenantMiddleware:
    """
    Middleware that attaches the current tenant to the request object
    based on the authenticated user's tenant foreign key.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None

        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                tenant = request.user.tenant
                if tenant and tenant.is_active:
                    request.tenant = tenant
            except AttributeError:
                pass

        response = self.get_response(request)
        return response
