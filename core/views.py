from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce, TruncMonth

from .models import Cuenta, Categoria, Subcategoria, Registro 
from decimal import Decimal, InvalidOperation
from datetime import datetime

import csv, json

# Cuentas
@login_required
def lista_cuentas(request):
    cuentas = (
        Cuenta.objects
        .filter(usuario=request.user)
        .annotate(
            saldo_actual=Coalesce(
                Sum('registro__importe'),
                Decimal('0.00')
            ) + F('saldo_inicial')
        )
    )

    return render(request, 'core/lista_cuentas.html', {'cuentas': cuentas})

@login_required
def crear_cuenta(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        saldo_raw = request.POST.get('saldo', '')
        saldo = Decimal(saldo_raw) if saldo_raw else Decimal('0.00')
        Cuenta.objects.create(nombre=nombre, saldo_inicial=saldo, usuario=request.user)
        return redirect('lista_cuentas')
    return render(request, 'core/crear_cuenta.html')

@login_required
def editar_cuenta(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    if request.method == 'POST':
        cuenta.nombre = request.POST.get('nombre')
        saldo_raw = request.POST.get('saldo', '')
        cuenta.saldo_inicial = Decimal(saldo_raw) if saldo_raw else Decimal('0.00')
        cuenta.save()
        return redirect('lista_cuentas')
    return render(request, 'core/editar_cuenta.html', {'cuenta': cuenta})

@login_required
def eliminar_cuenta(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    if request.method == 'POST':
        cuenta.delete()
        return redirect('lista_cuentas')
    return render(request, 'core/eliminar_cuenta.html', {'cuenta': cuenta})

# Categorias
@login_required
def lista_categorias(request):
    categorias = Categoria.objects.filter(usuario=request.user)
    return render(request, 'core/lista_categorias.html', {'categorias': categorias})

@login_required
def crear_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        Categoria.objects.create(nombre=nombre, tipo=tipo, usuario=request.user)
        return redirect('lista_categorias')
    return render(request, 'core/crear_categoria.html')

@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk, usuario=request.user)
    if request.method == 'POST':
        categoria.nombre = request.POST.get('nombre')
        categoria.tipo = request.POST.get('tipo')
        categoria.save()
        return redirect('lista_categorias')
    return render(request, 'core/editar_categoria.html', {'categoria': categoria})

@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk, usuario=request.user)
    if request.method == 'POST':
        categoria.delete()
        return redirect('lista_categorias')
    return render(request, 'core/eliminar_categoria.html', {'categoria': categoria})

# Subcategorias
@login_required
def lista_subcategorias(request):
    subcategorias = Subcategoria.objects.filter(usuario=request.user)
    return render(request, 'core/lista_subcategorias.html', {'subcategorias': subcategorias})

@login_required
def crear_subcategoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, pk=categoria_id, usuario=request.user)
        Subcategoria.objects.create(nombre=nombre, tipo=tipo, categoria=categoria, usuario=request.user)
        return redirect('lista_subcategorias')
    categorias = Categoria.objects.filter(usuario=request.user)
    return render(request, 'core/crear_subcategoria.html', {'categorias': categorias})

@login_required
def editar_subcategoria(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk, usuario=request.user)
    if request.method == 'POST':
        subcategoria.nombre = request.POST.get('nombre')
        subcategoria.tipo = request.POST.get('tipo')
        categoria_id = request.POST.get('categoria')
        subcategoria.categoria = get_object_or_404(Categoria, pk=categoria_id, usuario=request.user)
        subcategoria.save()
        return redirect('lista_subcategorias')
    categorias = Categoria.objects.filter(usuario=request.user)
    return render(request, 'core/editar_subcategoria.html', {'subcategoria': subcategoria, 'categorias': categorias})

@login_required
def eliminar_subcategoria(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk, usuario=request.user)
    if request.method == 'POST':
        subcategoria.delete()
        return redirect('lista_subcategorias')
    return render(request, 'core/eliminar_subcategoria.html', {'subcategoria': subcategoria})

# Registros

@login_required
def lista_registros(request):
    # ----------------------
    # QUERY BASE
    # ----------------------
    registros = Registro.objects.filter(usuario=request.user).select_related('cuenta', 'categoria', 'subcategoria')

    # ----------------------
    # FILTROS
    # ----------------------
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cuenta = request.GET.get('cuenta')
    tipo = request.GET.get('tipo')
    categoria = request.GET.get('categoria')
    metodo_pago = request.GET.get('metodo_pago')

    if fecha_desde:
        registros = registros.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        registros = registros.filter(fecha__lte=fecha_hasta)
    if cuenta:
        registros = registros.filter(cuenta_id=cuenta)
    if tipo:
        registros = registros.filter(tipo=tipo)
    if categoria:
        registros = registros.filter(categoria_id=categoria)
    if metodo_pago:
        registros = registros.filter(metodo_pago__icontains=metodo_pago)

    # ----------------------
    # ORDENACIÓN
    # ----------------------
    ordenar = request.GET.get('ordenar', '-fecha')
    campos_validos = [
        'fecha', '-fecha',
        'importe', '-importe',
        'tipo', '-tipo',
        'metodo_pago', '-metodo_pago',
        'concepto', '-concepto',
        'cuenta__nombre', '-cuenta__nombre',
        'categoria__nombre', '-categoria__nombre',
        'subcategoria__nombre', '-subcategoria__nombre',
    ]
    if ordenar not in campos_validos:
        ordenar = '-fecha'
    registros = registros.order_by(ordenar)

    # ----------------------
    # PAGINACIÓN
    # ----------------------
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # ----------------------
    # FILTROS PARA EL TEMPLATE
    # ----------------------
    filtros = {
        "fecha_desde": fecha_desde or "",
        "fecha_hasta": fecha_hasta or "",
        "cuenta": cuenta or "",
        "tipo": tipo or "",
        "categoria": categoria or "",
        "metodo_pago": metodo_pago or "",
    }

    # ----------------------
    # LISTAS PARA SELECTS
    # ----------------------
    cuentas = Cuenta.objects.filter(usuario=request.user)
    categorias = Categoria.objects.filter(usuario=request.user)

    # ----------------------
    # COLUMNAS ORDENABLES
    # ----------------------
    columnas = [
        ("Fecha", "fecha"),
        ("Importe", "importe"),
        ("Cuenta", "cuenta__nombre"),
        ("Tipo", "tipo"),
        ("Método de Pago", "metodo_pago"),
        ("Categoría", "categoria__nombre"),
        ("Subcategoría", "subcategoria__nombre"),
        ("Concepto", "concepto"),
    ]

    # ----------------------
    # CONTEXTO
    # ----------------------
    context = {
        "page_obj": page_obj,
        "columnas": columnas,
        "cuentas": cuentas,
        "categorias": categorias,
        "filtros": filtros,
    }

    return render(request, 'core/lista_registros.html', context)

@login_required
def crear_registro(request):
    cuentas = Cuenta.objects.filter(usuario=request.user)
    categorias = Categoria.objects.filter(usuario=request.user)
    subcategorias = Subcategoria.objects.filter(usuario=request.user)

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        importe_raw = request.POST.get('importe', '').strip()
        try:
            importe = Decimal(importe_raw) if importe_raw else Decimal('0.00')
        except InvalidOperation:
            importe = Decimal('0.00')

        cuenta_id = request.POST.get('cuenta')
        tipo = request.POST.get('tipo')
        metodo_pago = request.POST.get('metodo_pago')
        categoria_id = request.POST.get('categoria')
        subcategoria_id = request.POST.get('subcategoria')
        concepto = request.POST.get('concepto', '')
        notas = request.POST.get('notas', '')

        # Validaciones
        if not cuenta_id or not categoria_id or not subcategoria_id:
            messages.error(request, "Debes seleccionar cuenta, categoría y subcategoría.")
            return redirect('crear_registro')

        cuenta = get_object_or_404(Cuenta, pk=cuenta_id, usuario=request.user)
        categoria = get_object_or_404(Categoria, pk=categoria_id, usuario=request.user, tipo=tipo)
        subcategoria = get_object_or_404(Subcategoria, pk=subcategoria_id, usuario=request.user, tipo=tipo, categoria=categoria)

        Registro.objects.create(
            fecha=fecha,
            importe=importe,
            cuenta=cuenta,
            tipo=tipo,
            metodo_pago=metodo_pago,
            categoria=categoria,
            subcategoria=subcategoria,
            concepto=concepto,
            notas=notas,
            usuario=request.user
        )
        return redirect('lista_registros')

    return render(request, 'core/crear_registro.html', {
        'cuentas': cuentas,
        'categorias': categorias,
        'subcategorias': subcategorias,
    })



@login_required
def editar_registro(request, pk):
    registro = get_object_or_404(Registro, pk=pk, usuario=request.user)
    cuentas = Cuenta.objects.filter(usuario=request.user)
    categorias = Categoria.objects.filter(usuario=request.user)
    subcategorias = Subcategoria.objects.filter(usuario=request.user)

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        importe_raw = request.POST.get('importe', '0')
        registro.importe = Decimal(importe_raw) if importe_raw else Decimal('0.00')
        registro.fecha = fecha
        registro.cuenta = get_object_or_404(Cuenta, pk=request.POST.get('cuenta'), usuario=request.user)
        registro.tipo = request.POST.get('tipo')
        registro.metodo_pago = request.POST.get('metodo_pago')
        registro.categoria = get_object_or_404(Categoria, pk=request.POST.get('categoria'), usuario=request.user, tipo=registro.tipo)
        registro.subcategoria = get_object_or_404(Subcategoria, pk=request.POST.get('subcategoria'), usuario=request.user, tipo=registro.tipo, categoria=registro.categoria)
        registro.concepto = request.POST.get('concepto', '')
        registro.notas = request.POST.get('notas', '')
        registro.save()
        return redirect('lista_registros')

    return render(request, 'core/editar_registro.html', {
        'registro': registro,
        'cuentas': cuentas,
        'categorias': categorias,
        'subcategorias': subcategorias,
    })

@login_required
def eliminar_registro(request, pk):
    registro = get_object_or_404(Registro, pk=pk, usuario=request.user)
    if request.method == 'POST':
        registro.delete()
        return redirect('lista_registros')
    return render(request, 'core/eliminar_registro.html', {'registro': registro})

# Exportar CSV
@login_required
def exportar_registros_csv(request):
    registros = Registro.objects.filter(usuario=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registros.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Fecha',
        'Tipo',
        'Cuenta',
        'Categoria',
        'Subcategoria',
        'Metodo Pago',
        'Importe',
        'Concepto',
        'Notas'
    ])

    for r in registros:
        writer.writerow([
            r.fecha,
            r.tipo,
            r.cuenta.nombre,
            r.categoria.nombre,
            r.subcategoria.nombre if r.subcategoria else '',
            r.metodo_pago,
            str(r.importe).replace('.', ','),
            r.concepto,
            r.notas
        ])

    return response

# Importar CSV
@login_required
def importar_registros_csv(request):
    if request.method == 'POST':
        # Borrar registros previos del usuario
        Registro.objects.filter(usuario=request.user).delete()

        archivo = request.FILES['archivo']
        decoded_file = archivo.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file, delimiter=';')

        # Caches para no repetir consultas
        cuentas_cache = {c.nombre: c for c in Cuenta.objects.filter(usuario=request.user)}
        categorias_cache = {c.nombre: c for c in Categoria.objects.filter(usuario=request.user)}
        subcategorias_cache = {
            (s.nombre, s.categoria_id): s for s in Subcategoria.objects.filter(usuario=request.user)
        }

        registros_a_insertar = []

        for row in reader:
            # print para depuración
            print("Fila leída:", row)

            cuenta_nombre = row.get('Cuenta', '').strip()
            categoria_nombre = row.get('Categoria', '').strip()
            subcategoria_nombre = row.get('Subcategoria', '').strip()

            if not cuenta_nombre or not categoria_nombre:
                continue  # fila inválida

            # -------------------- CUENTA --------------------
            cuenta = cuentas_cache.get(cuenta_nombre)
            if not cuenta:
                cuenta = Cuenta.objects.create(nombre=cuenta_nombre, usuario=request.user)
                cuentas_cache[cuenta_nombre] = cuenta

            # -------------------- CATEGORÍA --------------------
            categoria = categorias_cache.get(categoria_nombre)
            if not categoria:
                categoria_tipo = row.get('Tipo', 'Gasto')  # por defecto
                categoria = Categoria.objects.create(nombre=categoria_nombre,
                                                     usuario=request.user,
                                                     tipo=categoria_tipo)
                categorias_cache[categoria_nombre] = categoria

            # -------------------- SUBCATEGORÍA --------------------
            subcategoria = None
            if subcategoria_nombre:
                key = (subcategoria_nombre, categoria.id)
                subcategoria = subcategorias_cache.get(key)
                if not subcategoria:
                    subcategoria_tipo = row.get('Tipo', 'Gasto')
                    subcategoria = Subcategoria.objects.create(
                        nombre=subcategoria_nombre,
                        usuario=request.user,
                        categoria=categoria,
                        tipo=subcategoria_tipo
                    )
                    subcategorias_cache[key] = subcategoria

            # -------------------- FECHA --------------------
            fecha_str = row.get('Fecha', '').replace('“','').replace('”','').strip()
            fecha = None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    fecha = datetime.strptime(fecha_str, fmt).date()
                    break
                except ValueError:
                    continue
            if not fecha:
                print("Fecha inválida, fila saltada:", fecha_str)
                continue

            # -------------------- IMPORTE --------------------
            importe_str = row.get('Importe', '').replace('"','').replace(',','.')
            try:
                importe = Decimal(importe_str)
            except InvalidOperation:
                print("Importe inválido, fila saltada:", importe_str)
                continue

            # -------------------- REGISTRO --------------------
            registro = Registro(
                fecha=fecha,
                tipo=row.get('Tipo'),
                cuenta=cuenta,
                categoria=categoria,
                subcategoria=subcategoria,
                metodo_pago=row.get('Metodo Pago', '').strip(),
                importe=importe,
                concepto=row.get('Concepto', '').strip(),
                notas=row.get('Notas', '').strip(),
                usuario=request.user
            )
            registros_a_insertar.append(registro)

        # Guardar todos los registros de golpe
        with transaction.atomic():
            Registro.objects.bulk_create(registros_a_insertar)

        return redirect('lista_registros')

    return render(request, 'core/importar_registros.html')

# Dashboard
@login_required
def dashboard(request):
    registros = Registro.objects.filter(usuario=request.user)

    # Totales
    total_ingresos = registros.filter(tipo="Ingreso").aggregate(
        total=Coalesce(Sum("importe"), Decimal("0.00"))
    )["total"]

    total_gastos = registros.filter(tipo="Gasto").aggregate(
        total=Coalesce(Sum("importe"), Decimal("0.00"))
    )["total"]

    # Gastos por categoría
    gastos_categoria = (
        registros.filter(tipo="Gasto")
        .values("categoria__nombre")
        .annotate(total=Sum("importe"))
        .order_by("-total")
    )

    categorias_labels = [g["categoria__nombre"] for g in gastos_categoria]
    categorias_data = [float(g["total"]) for g in gastos_categoria]

    # Evolución mensual
    evolucion = (
        registros
        .annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(
            ingresos=Sum("importe", filter=Q(tipo="Ingreso")),
            gastos=Sum("importe", filter=Q(tipo="Gasto")),
        )
        .order_by("mes")
    )

    meses = [e["mes"].strftime("%Y-%m") for e in evolucion]
    ingresos_mensuales = [float(e["ingresos"] or 0) for e in evolucion]
    gastos_mensuales = [float(e["gastos"] or 0) for e in evolucion]

    context = {
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "categorias_labels": json.dumps(categorias_labels),
        "categorias_data": json.dumps(categorias_data),
        "meses": json.dumps(meses),
        "ingresos_mensuales": json.dumps(ingresos_mensuales),
        "gastos_mensuales": json.dumps(gastos_mensuales),
    }

    return render(request, "core/dashboard.html", context)

# Toggle Modo
@login_required
def toggle_mode(request):
    # Guardamos en sesión el modo
    mode = request.session.get('mode', 'light')
    request.session['mode'] = 'dark' if mode == 'light' else 'light'
    # Redirige a la página anterior o al dashboard
    return redirect(request.META.get('HTTP_REFERER', '/'))