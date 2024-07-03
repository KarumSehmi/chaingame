from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('game/', include('playergame.urls')),  # Ensure this line is present
]
