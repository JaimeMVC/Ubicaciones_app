from django.contrib import admin
from django.urls import path
from app_inventario import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.buscar_material, name='buscar_material'),

    # Cargar/actualizar Excel base
    path('cargar-excel/', views.cargar_excel, name='cargar_excel'),

    # Trabajo sobre PN
    path('material/<str:pn>/', views.listado_ubicaciones, name='listado_ubicaciones'),
    path('material/<str:pn>/historial/', views.historial_pn, name='historial_pn'),
    path('sesion/<int:session_id>/informe/', views.informe_sesion, name='informe_sesion'),
    path('sesion/<int:session_id>/export-csv/', views.exportar_sesion_csv, name='exportar_sesion_csv'),


    # Ajax del checklist
    path('toggle-check/', views.toggle_check, name='toggle_check'),
]

