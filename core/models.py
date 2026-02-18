from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
class Cuenta(models.Model):
    nombre = models.CharField(max_length=100)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
    
class Categoria(models.Model):
    TIPO_CHOICES = [
        ('Gasto', 'Gasto'),
        ('Ingreso', 'Ingreso'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"
    
class Subcategoria(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=Categoria.TIPO_CHOICES)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
    def clean(self):
     # Subcategoría debe pertenecer a la categoría seleccionada
      if self.categoria and self.tipo != self.categoria.tipo:
        raise ValidationError("El tipo de la subcategoría debe coincidir con el tipo de su categoría.")
  

class Registro(models.Model):
    METODO_CHOICES = [
        ('Bizum', 'Bizum'),
        ('Traspaso', 'Traspaso'),
        ('Transferencia', 'Transferencia'),
        ('Traspaso', 'Traspaso'),
        ('Tarjeta', 'Tarjeta'),
        ('Efectivo', 'Efectivo'),
    ]

    fecha = models.DateField()
    importe = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=Categoria.TIPO_CHOICES)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    metodo_pago = models.CharField(max_length=50, choices=METODO_CHOICES)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, null=True, blank=True)
    concepto = models.CharField(max_length=255, blank=True)
    notas = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.fecha} - {self.importe}"
    def clean(self):
      # Tipo debe coincidir con categoría
      if self.categoria and self.tipo != self.categoria.tipo:
          raise ValidationError("El tipo del registro no coincide con el tipo de la categoría.")
      # Tipo debe coincidir con subcategoría
      if self.subcategoria and self.tipo != self.subcategoria.tipo:
          raise ValidationError("El tipo del registro no coincide con el tipo de la subcategoría.")
       # Subcategoría debe pertenecer a la categoría seleccionada
      if self.subcategoria and self.subcategoria.categoria != self.categoria:
        raise ValidationError("La subcategoría no pertenece a la categoría seleccionada.")