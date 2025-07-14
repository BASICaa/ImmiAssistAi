from django.urls import path
from . import views

urlpatterns = [
   path('', views.chat_interface, name='home'),
   path('chat/', views.chat_interface, name='chat_interface'),
   path('task_result/<str:task_id>/', views.get_task_result, name='get_task_result'),
   path('profile/', views.profile_creation_view, name='profile_creation'),
]