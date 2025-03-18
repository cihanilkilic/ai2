from django.urls import path
from . import views

app_name="atxaisoft"
urlpatterns = [
    path("", views.home, name="home"),
    path("chat/", views.chat, name="chat"),
    path("speech_to_text/", views.speech_to_text, name="speech_to_text"),
    
]
