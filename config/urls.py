from django.contrib import admin
from django.urls import path
from app_inventario import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.buscar_material, name='buscar_material'),
    path('material/<str:pn>/', views.listado_ubicaciones, name='listado_ubicaciones'),
    path('material/<str:pn>/informe/', views.informe_avance, name='informe_avance'),
    path('material/<str:pn>/guardar-informe/', views.guardar_informe, name='guardar_informe'),
    path('material/<str:pn>/export-csv/', views.export_csv, name='export_csv'),
    path('toggle-check/', views.toggle_check, name='toggle_check'),
    path('cargar-excel/', views.cargar_excel, name='cargar_excel'),

]
