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
    path('consultant/stats/', consultant_stats, name='consultant-stats'),

    # ----------all cook agreement urls-----------------------
    
    path('cook/create/', cook_create, name='cook-create'),
    path('cook/search/', cook_search, name='cook-search'),
    path('cook/edit-merge/<int:pk>/', cook_edit_merge, name="cook-edit-merge"),
    path('cook/search/viewer/', cook_search_viewer, name='cook_search_viewer'),
    path('cook/stats/', cook_stats, name='cook-stats'),

    # --------all distributer urls-----------------------------------
    path('distributer/create/', distributer_create, name='distributer-create'),
    path('distributer/search/', distributer_search, name='distributer-search'),
    path('distributer/edit-merge/<int:pk>/', distributer_edit_merge, name="distributer-edit-merge"),
    path('distributer/search/viewer/', distributer_search_viewer, name='distributer_search_viewer'),
    path('distributer/stats/', distributer_stats, name='distributer-stats'),

    # ---------all milk_sale urls---------------------------------------
    path('milk_sale/create/', milk_sale_create, name='milk_sale-create'),
    path('milk_sale/search/', milk_sale_search, name='milk_sale-search'),
    path('milk_sale/edit-merge/<int:pk>/', milk_sale_edit_merge, name="milk_sale-edit-merge"),
    path('milk_sale/stats/', milk_sale_stats, name='milk_sale-stats'),
    path('milk_sale/search/viewer/', milk_sale_search_viewer, name='milk_sale_search_viewer'),

    # --------all mcc agreements urls------------------------------------
    path('mcc/create/', mcc_create, name='mcc-create'),
    path('mcc/search/', mcc_search, name='mcc-search'),
    path('mcc/stats/', mcc_stats, name='mcc-stats'),
    path('mcc/edit-merge/<int:pk>/', mcc_edit_merge, name="mcc-edit-merge"),
    path('mcc/search/viewer/', mcc_search_viewer, name='mcc_search_viewer'),

    # -------all mpacs agreement urls------------------------------------
    path('mpacs/create/', mpacs_create, name='mpacs-create'),
    path('mpacs/stats/', mpacs_stats, name='mpacs-stats'),
    path('mpacs/search/', mpacs_search, name='mpacs-search'),
    path('mpacs/edit-merge/<int:pk>/', mpacs_edit_merge, name="mpacs-edit-merge"),
    path('mpacs/search/viewer/', mpacs_search_viewer, name='mpacs_search_viewer'),

    # --------all rta agreement urls-----------------------------------
    path('rta/create/', rta_create, name='rta-create'),
    path('rta/search/', rta_search, name='rta-search'),
    path('rta/edit-merge/<int:pk>/', rta_edit_merge, name="rta-edit-merge"),
    path('rta/search/viewer/', rta_search_viewer, name='rta_search_viewer'),
    path('rta/stats/', rta_stats, name='rta-stats'),

    # --------all godown agreement urls------------------------------
    path('godown/create/', godown_create , name='godown-create'),
    path('godown/search/', godown_search, name='godown-search'),
    path('godown/edit-merge/<int:pk>/', godown_edit_merge, name="godown-edit-merge"),
    path('godown/search/viewer/', godown_search_viewer, name='godown_search_viewer'),
    path('godown/stats/', godown_stats, name='godown-stats'),

    # 

    
    path('milk_sale/stats/', bmc_stats, name='bmc-stats'),
    path('mcc/stats/', bmc_stats, name='bmc-stats'),
    path('mpacs/stats/', bmc_stats, name='bmc-stats'),
    path('rta/stats/', bmc_stats, name='bmc-stats'),
    path('mpp_sahayak/stats/', bmc_stats, name='bmc-stats'),
    path('godown/stats/', bmc_stats, name='bmc-stats'), 
    path('office_lease/stats/', bmc_stats, name='bmc-stats'), 
    path('guest_house/stats/', bmc_stats, name='bmc-stats'), 
    path("logout/", logout_view, name="logout"),
     path('password-reset/', password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<uidb64>/<token>/', 
     password_reset_confirm, 
     name='password_reset_confirm'),
    path('password-reset/complete/',password_reset_complete, 
         name='password_reset_complete'),
    path("viewer_page/", viewer_page, name="viewer"),
    path("data_entry/", data_entry_page, name="data-entry"),
    path('download-incomplete-excel/', download_incomplete_excel, name='download_incomplete_excel')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)