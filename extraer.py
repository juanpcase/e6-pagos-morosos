
#!/usr/bin/env python3
"""
Extrae todas las filas de la API de datos.gov.co, página por página.
Comprueba que no falte ninguna y guarda el archivo JSON con fecha.

API:
https://www.datos.gov.co/resource/rvii-eis8.json

Filtro:
Registros que presentan valores mayores que cero en cualquiera
de las columnas de cartera vencida.

Uso:
    python3 extraer.py

Resultado:
    data/raw/rvii-eis8_FECHA.json
    conteos.csv

Solo utiliza bibliotecas estándar de Python.
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


# --------------------------------------------------
# 1. CONFIGURACIÓN DE LA API Y DEL FILTRO
# --------------------------------------------------

API_URL = "https://www.datos.gov.co/resource/rvii-eis8.json"

API_FILTRO = (
    "$where=_3_vencida_1_2_meses > 0 "
    "OR _4_vencida_2_3_meses > 0 "
    "OR _5_vencida_1_3_meses > 0 "
    "OR _6_vencida_3_4_meses > 0 "
    "OR _7_vencida_de_4_meses > 0 "
    "OR _8_vencida_3_6_meses > 0 "
    "OR _9_vencida_6_meses > 0 "
    "OR _10_vencida_1_4_meses > 0 "
    "OR _11_vencida_4_6_meses > 0 "
    "OR _12_vencida_6_12_meses > 0 "
    "OR _13_vencida_12_18_meses > 0 "
    "OR _14_vencida_12_meses > 0 "
    "OR _15_vencida_18_meses > 0"
)

COLOMBIA = timezone(timedelta(hours=-5))
REINTENTOS = 3


# --------------------------------------------------
# 2. CARGAR CONFIGURACIÓN DEL ARCHIVO .env
# --------------------------------------------------

def cargar_env(ruta=".env"):
    """Lee KEY=VALOR de .env sin pisar variables existentes."""

    if not os.path.exists(ruta):
        return

    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            if not linea or linea.startswith("#") or "=" not in linea:
                continue

            clave, valor = linea.split("=", 1)

            os.environ.setdefault(
                clave.strip(),
                valor.strip().strip('"').strip("'")
            )


def miles(n):
    return f"{n:,}".replace(",", ".")


class FallaAPI(Exception):
    pass


# --------------------------------------------------
# 3. CONSULTAR LA API
# --------------------------------------------------

def pedir(base, params, token, simular_error=False):
    """Realiza una petición GET con reintentos ante errores temporales."""

    url = base + "?" + urllib.parse.urlencode(params)

    headers = {
        "Accept": "application/json",
        "User-Agent": "estudia-extraer/1.0"
    }

    if token:
        headers["X-App-Token"] = token

    ultimo = ""

    for intento in range(1, REINTENTOS + 1):

        try:

            if simular_error:
                raise urllib.error.HTTPError(
                    url,
                    503,
                    "Service Unavailable (simulado)",
                    None,
                    None
                )

            solicitud = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
                return json.loads(respuesta.read().decode("utf-8"))

        except urllib.error.HTTPError as e:

            ultimo = f"HTTP {e.code} {e.reason}"

            if e.code == 429:
                espera = min(
                    int(e.headers.get("Retry-After", "10"))
                    if e.headers else 10,
                    60
                )

            elif e.code >= 500:
                espera = 2 ** intento

            else:
                cuerpo = ""

                try:
                    cuerpo = e.read().decode("utf-8")[:200]
                except Exception:
                    pass

                raise FallaAPI(f"{ultimo}. {cuerpo}".strip())

        except (urllib.error.URLError, TimeoutError) as e:

            ultimo = f"sin respuesta ({e})"
            espera = 2 ** intento

        if intento < REINTENTOS:
            print(
                f"  {ultimo}: espero {espera} segundos "
                f"y reintento ({intento}/{REINTENTOS - 1})"
            )
            time.sleep(espera)

    raise FallaAPI(f"{ultimo} después de {REINTENTOS} intentos")


# --------------------------------------------------
# 4. REGISTRAR LOS RESULTADOS
# --------------------------------------------------

def registrar(fila, ruta="conteos.csv"):

    nuevo = not os.path.exists(ruta)

    with open(ruta, "a", newline="", encoding="utf-8") as f:

        w = csv.writer(f)

        if nuevo:
            w.writerow([
                "fecha",
                "conjunto",
                "filtro",
                "esperadas",
                "traidas",
                "ids_unicos",
                "paginas",
                "estado",
                "archivo",
                "detalle"
            ])

        w.writerow(fila)


# --------------------------------------------------
# 5. REVISAR EL ARCHIVO .gitignore
# --------------------------------------------------

def revisar_gitignore():

    if os.path.exists(".gitignore"):

        with open(".gitignore", encoding="utf-8") as f:
            lineas = [l.strip() for l in f]

        if "data/" not in lineas and "data" not in lineas:
            print(
                "OJO: agrega la línea data/ a .gitignore. "
                "El archivo bruto no se sube al repositorio."
            )


# --------------------------------------------------
# 6. PROCESO PRINCIPAL DE EXTRACCIÓN
# --------------------------------------------------

def main():

    cargar_env()

    # Utilizamos la API y el filtro definidos arriba.
    base = API_URL
    filtro = API_FILTRO

    token = os.environ.get("SOCRATA_APP_TOKEN", "").strip()

    tam = int(os.environ.get("TAM_PAGINA", "1000") or 1000)

    max_filas = int(
        os.environ.get("MAX_FILAS", "100000") or 100000
    )

    simular = os.environ.get(
        "SIMULAR_FALLA", ""
    ).strip().lower()

    conjunto = base.rstrip("/").split("/")[-1].replace(".json", "")

    filtros = urllib.parse.parse_qsl(
        filtro,
        keep_blank_values=True
    )

    ahora = datetime.now(COLOMBIA)

    fecha = ahora.strftime("%Y-%m-%d %H:%M")

    revisar_gitignore()

    print("=" * 60)
    print("EXTRACCIÓN DE CARTERA VENCIDA")
    print("=" * 60)

    print(f"Fuente: {conjunto}")
    print("Filtro: registros con valores mayores que cero")
    print(f"Tamaño de página: {tam}")

    if simular:
        print(f"SIMULACRO: falla «{simular}» activada")

    def cerrar(
        esperadas,
        traidas,
        unicos,
        paginas,
        estado,
        archivo,
        detalle
    ):

        registrar([
            fecha,
            conjunto,
            filtro,
            esperadas,
            traidas,
            unicos,
            paginas,
            estado,
            archivo,
            detalle
        ])

        print(f"Registro agregado a conteos.csv ({estado}).")

        sys.exit(0 if estado == "completa" else 1)

    # --------------------------------------------------
    # 7. PRIMERA CONSULTA: CONTAR LOS REGISTROS
    # --------------------------------------------------

    try:

        resp = pedir(
            base,
            filtros + [("$select", "count(*)")],
            token
        )

        esperadas = int(list(resp[0].values())[0])

    except (FallaAPI, IndexError, ValueError) as e:

        print(f"ALTO: no pude pedir el conteo: {e}")

        cerrar("", 0, 0, 0, "error", "", f"conteo: {e}")

    print(f"Esperadas según la API: {miles(esperadas)}")

    if esperadas == 0:

        print("ALTO: la API dice que hay 0 filas. Revisa el filtro.")

        cerrar(0, 0, 0, 0, "vacia", "", "0 filas con ese filtro")

    if esperadas > max_filas:

        print(
            f"ALTO: {miles(esperadas)} filas superan "
            f"el límite de {miles(max_filas)}."
        )

        cerrar(
            esperadas,
            0,
            0,
            0,
            "detenida",
            "",
            f"más de {max_filas} filas"
        )

    # --------------------------------------------------
    # 8. EXTRAER LOS REGISTROS POR PÁGINAS
    # --------------------------------------------------

    filas = []
    pagina = 0
    offset = 0

    while True:

        pagina += 1

        if simular == "pagina" and pagina == 2:

            print(f"Página {pagina}: SIMULACRO, me la salto.")

            offset += tam

            continue

        params = filtros + [
            ("$select", ":*,*"),
            ("$order", ":id"),
            ("$limit", str(tam)),
            ("$offset", str(offset))
        ]

        try:

            lote = pedir(
                base,
                params,
                token,
                simular_error=(
                    simular == "error" and pagina == 2
                )
            )

        except FallaAPI as e:

            print(f"ALTO: la página {pagina} falló: {e}")

            print(
                "No guardo nada: una extracción incompleta "
                "no representa el total de registros."
            )

            cerrar(
                esperadas,
                len(filas),
                len({r.get(":id") for r in filas}),
                pagina,
                "incompleta",
                "",
                f"página {pagina}: {e}"
            )

        filas.extend(lote)

        print(
            f"Página {pagina}: {miles(len(lote))} filas "
            f"(llevo {miles(len(filas))})"
        )

        if len(lote) < tam or len(filas) > esperadas + tam:
            break

        offset += tam

    # --------------------------------------------------
    # 9. COMPROBAR QUE NO FALTEN REGISTROS
    # --------------------------------------------------

    unicos = len({r.get(":id") for r in filas})

    print("-" * 60)

    print(f"Registros traídos: {miles(len(filas))}")
    print(f"Identificadores únicos: {miles(unicos)}")
    print(f"Registros esperados: {miles(esperadas)}")

    if len(filas) != esperadas or unicos != len(filas):

        print(
            "ALTO: los conteos no coinciden. "
            "No guardo el archivo bruto."
        )

        cerrar(
            esperadas,
            len(filas),
            unicos,
            pagina,
            "incompleta",
            "",
            (
                "traídas distintas de esperadas"
                if len(filas) != esperadas
                else "filas repetidas"
            )
        )

    # --------------------------------------------------
    # 10. GUARDAR LA EXTRACCIÓN COMPLETA
    # --------------------------------------------------

    os.makedirs(
        os.path.join("data", "raw"),
        exist_ok=True
    )

    archivo = os.path.join(
        "data",
        "raw",
        f"{conjunto}_{ahora.strftime('%Y-%m-%d_%H%M%S')}.json"
    )

    with open(archivo, "w", encoding="utf-8") as f:

        json.dump(
            filas,
            f,
            ensure_ascii=False
        )

    print("=" * 60)
    print("EXTRACCIÓN COMPLETA")
    print(f"Archivo guardado: {archivo}")
    print("=" * 60)

    cerrar(
        esperadas,
        len(filas),
        unicos,
        pagina,
        "completa",
        archivo,
        ""
    )


# --------------------------------------------------
# 11. EJECUTAR EL PROGRAMA
# --------------------------------------------------

if __name__ == "__main__":
    main()

