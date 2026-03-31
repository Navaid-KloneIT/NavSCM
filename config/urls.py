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
    path('demand-planning/', include('apps.demand_planning.urls', namespace='demand_planning')),
    path('manufacturing/', include('apps.manufacturing.urls', namespace='manufacturing')),
    path('qms/', include('apps.qms.urls', namespace='qms')),
    path('returns/', include('apps.returns.urls', namespace='returns')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('contracts/', include('apps.contracts.urls', namespace='contracts')),
    path('assets/', include('apps.assets.urls', namespace='assets')),
    path('labor/', include('apps.labor.urls', namespace='labor')),
    path('', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
