from django.urls import path
from .views import main_view, ajax_delete_ticker, ajax_update_data


urlpatterns = [
    path('', main_view, name='main'),
    path('delete', ajax_delete_ticker, name='remove'),
    path('update', ajax_update_data, name='update'),
]
