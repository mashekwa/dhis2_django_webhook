from django.urls import path
from .views import webhook_receiver

urlpatterns = [
    path('receive/',webhook_receiver, name='webhook_receiver')
    
]
