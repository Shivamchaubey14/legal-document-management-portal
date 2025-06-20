from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from .views import *
urlpatterns = [
    path("", login, name="login"),
    path("", login, name="login"),

    # --------all amc agreement urls------------
    path('amc/edit-merge/<int:pk>/', amc_edit_merge, name='amc-edit-merge'),
    path('amc/create/', amc_create, name="amc-create"),
    path('amc/search/', amc_search, name='amc-search'),
    path('amc/search/viewer/', amc_search_viewer, name='amc_search_viewer'),
    path('amc/stats/', amc_stats, name='amc-stats'),

    # ---------all bmc agreement urls-------------
    path('bmc/edit-merge/<int:pk>/', bmc_edit_merge, name='bmc-edit-merge'),
    path('bmc/create', bmc_create, name="bmc-create"),
    path('bmc/search/', bmc_search, name='bmc-search'),
    path('bmc/search/viewer/', bmc_search_viewer, name='bmc-search-viewer'),
    path('bmc/stats/', bmc_stats, name='bmc-stats'),

    # ----------all input services agreement urls------------
    path('input_services/create/', input_services_create, name="input_services-create"),
    path('input_services/edit-merge/<int:pk>/', input_services_edit_merge, name='input_services-edit-merge'),
    path('input_services/search/', input_services_search, name='input_services-search'),
    path('input_services/stats/', input_services_stats, name='input_services-stats'),
    path('input-service/search/viewer/', input_services_search_viewer, name='input_services_search_viewer'),

    # ----------all consultant agreement urls-----------------

    path('consultant/create/', consultant_create, name="consultant-create"),
    path('consultant/search/', consultant_search, name='consultant-search'),
    path('consultant/edit-merge/<int:pk>/', consultant_edit_merge, name="consultant-edit-merge"),
    path('consultant/search/viewer/', consultant_search_viewer, name='consultant_search_viewer'),
    path('consultant/stats/', bmc_stats, name='bmc-stats'),

    # ----------all cook agreement ulrs-----------------------
    
    path('cook/create/', cook_create, name='cook-create'),
    path('cook/search/', cook_search, name='cook-search'),
    path('cook/stats/', bmc_stats, name='bmc-stats'),

    
    path('distributer/stats/', bmc_stats, name='bmc-stats'),
    path('milk_sale/stats/', bmc_stats, name='bmc-stats'),
    path('mcc/stats/', bmc_stats, name='bmc-stats'),
    path('mpacs/stats/', bmc_stats, name='bmc-stats'),
    path('rta/stats/', bmc_stats, name='bmc-stats'),
    path('mpp_sahayak/stats/', bmc_stats, name='bmc-stats'),
    path('godown/stats/', bmc_stats, name='bmc-stats'), 
    path('office_lease/stats/', bmc_stats, name='bmc-stats'), 
    path('guest_house/stats/', bmc_stats, name='bmc-stats'), 
    path("logout/", logout_view, name="logout"),
    path("viewer_page/", viewer_page, name="viewer"),
    path("data_entry/", data_entry_page, name="data-entry")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)