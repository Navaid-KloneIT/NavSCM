def tenant_context(request):
    """
    Adds the current tenant to the template context.
    """
    return {
        'current_tenant': getattr(request, 'tenant', None),
    }
