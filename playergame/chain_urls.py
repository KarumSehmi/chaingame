from django.urls import path
from . import views

app_name = 'playergame'

urlpatterns = [
    path('', views.chain_index, name='chain_index'),  # Player chain index page
    path('generate_player_chain/', views.generate_player_chain, name='generate_player_chain'),
]

