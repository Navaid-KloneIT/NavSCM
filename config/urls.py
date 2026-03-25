"""
URL configuration for NavSCM HCM project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('core/', include('apps.core.urls', namespace='core')),
    path('procurement/', include('apps.procurement.urls', namespace='procurement')),
    path('srm/', include('apps.srm.urls', namespace='srm')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('wms/', include('apps.wms.urls', namespace='wms')),
    path('oms/', include('apps.oms.urls', namespace='oms')),
    path('tms/', include('apps.tms.urls', namespace='tms')),
    path('', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
