from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import LocationCheck

def buscar_material(request):
    query=request.GET.get('q','').strip()
    materiales=[]
    if query:
        materiales=(LocationCheck.objects.filter(pn__icontains=query)
                    .values('pn').distinct().order_by('pn'))
    return render(request,"app_inventario/buscar_material.html",{"query":query,"materiales":materiales})

def listado_ubicaciones(request,pn):
    ubicaciones=LocationCheck.objects.filter(pn=pn)
    total=ubicaciones.count()
    revisadas=ubicaciones.filter(is_checked=True).count()
    porcentaje=round(revisadas/total*100,1) if total else 0
    return render(request,"app_inventario/listado_ubicaciones.html",
                  {"pn":pn,"ubicaciones":ubicaciones,"total":total,
                   "revisadas":revisadas,"porcentaje":porcentaje})

def toggle_check(request):
    if request.method=="POST":
        obj=get_object_or_404(LocationCheck,id=request.POST.get('id'))
        checked=request.POST.get('checked')=="true"
        obj.is_checked=checked
        obj.checked_at=timezone.now() if checked else None
        obj.save()
        return JsonResponse({"success":True})
    return JsonResponse({"success":False},status=400)

import csv
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import pandas as pd
from .models import LocationCheck, ResultSnapshot

def informe_avance(request, pn):
    ubicaciones = LocationCheck.objects.filter(pn=pn).order_by("ubicacion")
    total = ubicaciones.count()
    revisadas = ubicaciones.filter(is_checked=True).count()
    porcentaje = round((revisadas / total * 100), 1) if total else 0.0
    snapshots = ResultSnapshot.objects.filter(pn=pn)[:10]  # últimos 10 guardados

    return render(request, "app_inventario/informe_avance.html", {
        "pn": pn,
        "total": total,
        "revisadas": revisadas,
        "pendientes": total - revisadas,
        "porcentaje": porcentaje,
        "ubicaciones": ubicaciones,
        "snapshots": snapshots,
    })

def guardar_informe(request, pn):
    ubicaciones = LocationCheck.objects.filter(pn=pn)
    total = ubicaciones.count()
    revisadas = ubicaciones.filter(is_checked=True).count()
    porcentaje = round((revisadas / total * 100), 1) if total else 0.0

    ResultSnapshot.objects.create(
        pn=pn, total=total, revisadas=revisadas, porcentaje=porcentaje
    )
    messages.success(request, "Informe guardado en el histórico.")
    return HttpResponseRedirect(reverse("informe_avance", args=[pn]))

def export_csv(request, pn):
    """Descarga el detalle del PN en CSV."""
    ubicaciones = LocationCheck.objects.filter(pn=pn).order_by("ubicacion")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="informe_{pn}.csv"'

    writer = csv.writer(response)
    writer.writerow(["PN", "Ubicacion", "Descripcion", "Revisado", "Fecha_revision"])
    for u in ubicaciones:
        writer.writerow([
            u.pn,
            u.ubicacion,
            (u.descripcion or ""),
            "SI" if u.is_checked else "NO",
            u.checked_at.strftime("%Y-%m-%d %H:%M") if u.checked_at else "",
        ])
    return response

# ----- ya listo: buscar_material, listado_ubicaciones, toggle_check, informe_avance, guardar_informe, export_csv -----

def _norm(s: str) -> str:
    if s is None: return ""
    s = str(s).strip().lower()
    s = (s.replace("á","a").replace("é","e").replace("í","i")
             .replace("ó","o").replace("ú","u").replace("ñ","n"))
    for ch in [" ", "\t", "\n", "-", "_", ".", "/"]:
        s = s.replace(ch, "")
    return s

def _import_df(df: pd.DataFrame) -> int:
    cols_map = {_norm(c): c for c in df.columns if isinstance(c, str)}

    def pick(cands):
        for k in cands:
            if k in cols_map: return cols_map[k]
        return None

    col_pn  = pick(["pn","partnumber","material","codigo","codigomaterial","materialcode"])
    col_ubi = pick(["ubicaciones","ubicacion","ubicacionessap","location","ubicacionfisica"])
    col_des = pick(["descripcion","description","desc"])

    if not col_pn or not col_ubi:
        raise ValueError(f"Cabeceras detectadas: {list(df.columns)}. Falta PN y/o Ubicaciones.")

    if not col_des:
        df["__descripcion__"] = ""
        col_des = "__descripcion__"

    df = df[[col_pn, col_ubi, col_des]].rename(columns={col_pn:"pn", col_ubi:"ubicacion", col_des:"descripcion"})
    df["pn"] = df["pn"].astype(str).str.strip()
    df["ubicacion"] = df["ubicacion"].astype(str).str.strip()
    df["descripcion"] = df["descripcion"].astype(str).fillna("").str.strip()
    df = df[(df["pn"]!="") & (df["ubicacion"]!="")].dropna(subset=["pn","ubicacion"])
    df = df.drop_duplicates(subset=["pn","ubicacion"], keep="last")

    objs = [LocationCheck(pn=r["pn"], ubicacion=r["ubicacion"], descripcion=r["descripcion"]) for _,r in df.iterrows()]
    with transaction.atomic():
        # Django 4.1+: upsert por unique_together
        LocationCheck.objects.bulk_create(
            objs, update_conflicts=True,
            unique_fields=["pn","ubicacion"],
            update_fields=["descripcion"],
            batch_size=1000
        )
    return len(objs)

def cargar_excel(request):
    if request.method == "POST" and request.FILES.get("archivo"):
        try:
            df = pd.read_excel(request.FILES["archivo"], engine="openpyxl")
            n = _import_df(df)
            messages.success(request, f"Archivo importado correctamente. Filas procesadas: {n}.")
            return HttpResponseRedirect(reverse("buscar_material"))
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return HttpResponseRedirect(reverse("cargar_excel"))
    return render(request, "app_inventario/cargar_excel.html")
