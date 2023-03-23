from django.urls import path
from .views import main_view, ajax_delete_ticker, ajax_update_data, LoginView, LogoutView, register_view


urlpatterns = [
    path('', main_view, name='main'),
    path('delete', ajax_delete_ticker, name='remove'),
    path('update', ajax_update_data, name='update'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('register', register_view, name='register'),
]
