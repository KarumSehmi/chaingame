from django.urls import path
from . import views

app_name = 'playergame'

urlpatterns = [
    path('', views.index, name='index'),
    path('suggest_player_names/', views.suggest_player_names, name='suggest_player_names'),
    path('find_link/', views.find_link, name='find_link'),
    path('get_player_data/', views.get_player_data, name='get_player_data'),
    path('chain/', views.chain_index, name='chain_index'),
    path('validate_chain/', views.validate_chain, name='validate_chain'),
]
