import pandas as pd
from django.core.management.base import BaseCommand
from app_inventario.models import LocationCheck

def _norm(s: str) -> str:
    """Normaliza nombres de columnas: minúsculas, sin espacios, sin tildes."""
    if s is None:
        return ""
    s = str(s).strip().lower()
    # quitar tildes comunes sin depender de paquetes extra
    s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
             .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    # quitar espacios y signos
    for ch in [" ", "\t", "\n", "-", "_", ".", "/"]:
        s = s.replace(ch, "")
    return s

class Command(BaseCommand):
    help = "Importa datos desde Excel (PN, Ubicaciones, Descripcion). Acepta nombres con y sin acento."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Ruta al archivo Excel')

    def handle(self, *args, **options):
        file_path = options['file_path']
        self.stdout.write(self.style.WARNING(f"Leyendo archivo: {file_path}"))

        df = pd.read_excel(file_path)  # primera hoja, header=0

        # Mapear cabeceras normalizadas -> originales
        cols_map = { _norm(c): c for c in df.columns if isinstance(c, str) }

        # Posibles alias de cada campo
        PN_ALIASES = ['pn', 'partnumber', 'material', 'codigo', 'codigomaterial', 'materialcode']
        UBI_ALIASES = ['ubicaciones', 'ubicacion', 'ubicacionessap', 'location', 'ubicacionfisica']
        DESC_ALIASES = ['descripcion', 'description', 'desc']

        def pick(cols_map, candidates):
            for key in candidates:
                if key in cols_map:
                    return cols_map[key]
            return None

        col_pn  = pick(cols_map, PN_ALIASES)
        col_ubi = pick(cols_map, UBI_ALIASES)
        col_des = pick(cols_map, DESC_ALIASES)

        if not col_pn or not col_ubi:
            self.stdout.write(self.style.ERROR(
                f"No se encontraron columnas obligatorias.\n"
                f"Cabeceras leídas: {list(df.columns)}\n"
                f"Necesito al menos PN y Ubicaciones (con cualquiera de estos nombres o variantes)."
            ))
            return

        # Si no hay descripción, creamos columna vacía
        if not col_des:
            df['__descripcion__'] = ""
            col_des = '__descripcion__'

        # Nos quedamos con estas 3
        df = df[[col_pn, col_ubi, col_des]].rename(columns={
            col_pn:  'pn',
            col_ubi: 'ubicacion',
            col_des: 'descripcion'
        })

        # Limpieza básica
        df['pn'] = df['pn'].astype(str).str.strip()
        df['ubicacion'] = df['ubicacion'].astype(str).str.strip()
        df['descripcion'] = df['descripcion'].astype(str).fillna("").str.strip()

        # Drop filas sin PN o sin ubicación
        df = df[(df['pn'] != "") & (df['ubicacion'] != "")]
        df = df.dropna(subset=['pn', 'ubicacion'])

        total = 0
        for _, row in df.iterrows():
            LocationCheck.objects.update_or_create(
                pn=row['pn'],
                ubicacion=row['ubicacion'],
                defaults={'descripcion': row['descripcion']}
            )
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Importadas/actualizadas {total} filas"))
