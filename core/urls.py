from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #Login Logout
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Cuentas
    path('cuentas/', views.lista_cuentas, name='lista_cuentas'),
    path('cuentas/crear/', views.crear_cuenta, name='crear_cuenta'),
    path('cuentas/<int:pk>/editar/', views.editar_cuenta, name='editar_cuenta'),
    path('cuentas/<int:pk>/eliminar/', views.eliminar_cuenta, name='eliminar_cuenta'),

    # Categorias
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),

    # Subcategorias
    path('subcategorias/', views.lista_subcategorias, name='lista_subcategorias'),
    path('subcategorias/crear/', views.crear_subcategoria, name='crear_subcategoria'),
    path('subcategorias/<int:pk>/editar/', views.editar_subcategoria, name='editar_subcategoria'),
    path('subcategorias/<int:pk>/eliminar/', views.eliminar_subcategoria, name='eliminar_subcategoria'),

    # Registros
    path('registros/', views.lista_registros, name='lista_registros'),
    path('registros/crear/', views.crear_registro, name='crear_registro'),
    path('registros/<int:pk>/editar/', views.editar_registro, name='editar_registro'),
    path('registros/<int:pk>/eliminar/', views.eliminar_registro, name='eliminar_registro'),

    # Exportar registros
    path('registros/exportar/', views.exportar_registros_csv, name='exportar_registros'),

    # Importar registros
    path('registros/importar/', views.importar_registros_csv, name='importar_registros'),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Toggle modo oscuro
    path('toggle-mode/', views.toggle_mode, name='toggle_mode'),
]
