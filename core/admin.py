from django.contrib import admin
from .models import Cuenta, Categoria, Subcategoria, Registro

admin.site.register(Cuenta)
admin.site.register(Categoria)
admin.site.register(Subcategoria)
admin.site.register(Registro)
