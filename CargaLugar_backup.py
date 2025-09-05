"""
Sistema automatizado de reserva de lugares en hoteling.

Este sistema permite automatizar la reserva de lugares en un sistema web,
consultando reservaciones existentes en una base de datos SQLite para evitar
duplicados y optimizar el proceso de reserva.

Características:
- Configuración a través de variables de entorno (.env)
- Persistencia en base de datos SQLite
- Consulta de reservaciones existentes antes de reservar
- Validación de fechas y lugares
- Modo de solo consulta disponible
"""

import asyncio
import os
import sqlite3
from datetime import datetime, date, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv


# ====================================================================
# CONFIGURACIÓN Y CONSTANTES GLOBALES
# ====================================================================

# Cargar variables de entorno
load_dotenv()

# Mapeo de números a nombres de días para mostrar información
NOMBRES_DIAS = {
    0: "Lunes",
    1: "Martes", 
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

# Base de datos SQLite
DB_NAME = "reservaciones.db"


# ====================================================================
# FUNCIONES DE UTILIDAD Y VALIDACIÓN
# ====================================================================
def validar_lugares(lugares):
    """Valida que los lugares configurados tengan el formato correcto."""
    lugares_validos = []
    for lugar in lugares:
        # Validación básica del formato P##-####
        if lugar and len(lugar) >= 6 and "-" in lugar:
            lugares_validos.append(lugar)
        else:
            print(f"⚠️ Lugar ignorado por formato inválido: '{lugar}'")

    if not lugares_validos:
        print("❌ No hay lugares válidos configurados. Usando valores por defecto.")
        return ["P17-1001", "P17-1002", "P17-1003"]

    return lugares_validos


def validar_dias(dias):
    """Valida que los días configurados estén en el rango 0-6."""
    dias_validos = []
    for dia in dias:
        try:
            dia_int = int(dia.strip())
            if 0 <= dia_int <= 6:
                dias_validos.append(dia_int)
            else:
                print(f"⚠️ Día ignorado (debe estar entre 0-6): '{dia}'")
        except ValueError:
            print(f"⚠️ Día ignorado por formato inválido: '{dia}'")

    if not dias_validos:
        print("❌ No hay días válidos configurados. Usando valores por defecto (Miércoles y Jueves).")
        return [2, 3]  # Miércoles y Jueves por defecto

    return dias_validos


def configurar_variables_entorno():
    """Configura y valida las variables de entorno."""
    # Obtener lugares desde variable de entorno como lista
    lugares_env = os.getenv("LUGARES_RESERVA", "P17-1001,P17-1002,P17-1003")
    lugares_sin_validar = [
        lugar.strip() for lugar in lugares_env.split(",") if lugar.strip()
    ]
    lugares_disponibles = validar_lugares(lugares_sin_validar)

    # Obtener días desde variable de entorno como lista
    dias_env = os.getenv("DIAS_RESERVA", "2,3")
    dias_sin_validar = [dia.strip() for dia in dias_env.split(",") if dia.strip()]
    dias_reserva = validar_dias(dias_sin_validar)
    
    return lugares_disponibles, dias_reserva


def mostrar_configuracion(lugares_disponibles, dias_reserva):
    """Muestra la configuración actual del sistema."""
    print("🏢 Lugares configurados para reserva:")
    for i, lugar in enumerate(lugares_disponibles, 1):
        print(f"  {i}. {lugar}")
    print(f"📋 Total de opciones: {len(lugares_disponibles)}")

    print("\n📅 Días configurados para reserva:")
    for dia in dias_reserva:
        print(f"  • {NOMBRES_DIAS[dia]} ({dia})")
    print(f"📋 Total de días: {len(dias_reserva)}")

    print("\n🚀 PROCESO AUTOMÁTICO DE RESERVA INTELIGENTE")
    print("=" * 60)
    print("📋 El sistema ejecutará automáticamente:")
    print("  1️⃣ Consultar reservaciones existentes")
    print("  2️⃣ Determinar siguiente fecha disponible")
    print("  3️⃣ Reservar solo fechas posteriores a las existentes")
    print("  4️⃣ Actualizar base de datos con nuevas reservas")
    print("=" * 60)
    print("🔄 Iniciando proceso automatizado...\n")


# ====================================================================
# FUNCIONES DE BASE DE DATOS
# ====================================================================

def inicializar_base_datos():
    """Inicializa la base de datos SQLite para guardar las reservaciones."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Crear tabla de reservaciones si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_consulta TEXT NOT NULL,
            columna_1 TEXT,
            columna_2 TEXT,
            columna_3 TEXT,
            columna_4 TEXT,
            columna_5 TEXT,
            columna_6 TEXT,
            columna_7 TEXT,
            fecha_reserva TEXT,
            columna_9 TEXT,
            columna_10 TEXT,
            fila_completa TEXT,
            UNIQUE(fecha_reserva, columna_1, columna_2, columna_3)
        )
    """)

    conn.commit()
    conn.close()
    print("📊 Base de datos inicializada correctamente")


def guardar_reservacion(datos_fila, fecha_reserva):
    """Guarda una reservación en la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Dividir los datos de la fila en columnas
        columnas = datos_fila.split(" | ")

        # Asegurar que tenemos al menos 10 columnas, completar con cadena vacía si faltan
        while len(columnas) < 10:
            columnas.append("")

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT OR REPLACE INTO reservaciones 
            (fecha_consulta, columna_1, columna_2, columna_3, columna_4, columna_5, 
             columna_6, columna_7, fecha_reserva, columna_9, columna_10, fila_completa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                fecha_actual,
                columnas[0] if len(columnas) > 0 else "",
                columnas[1] if len(columnas) > 1 else "",
                columnas[2] if len(columnas) > 2 else "",
                columnas[3] if len(columnas) > 3 else "",
                columnas[4] if len(columnas) > 4 else "",
                columnas[5] if len(columnas) > 5 else "",
                columnas[6] if len(columnas) > 6 else "",
                fecha_reserva,
                columnas[8] if len(columnas) > 8 else "",
                columnas[9] if len(columnas) > 9 else "",
                datos_fila,
            ),
        )

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error al guardar reservación: {e}")
        return False
    finally:
        conn.close()


def mostrar_reservaciones_guardadas():
    """Muestra las reservaciones guardadas en la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT fecha_consulta, fecha_reserva, columna_1, columna_2, columna_3, fila_completa 
            FROM reservaciones 
            ORDER BY fecha_reserva DESC
        """)

        reservaciones = cursor.fetchall()

        if reservaciones:
            print(f"\n📋 Reservaciones guardadas en la base de datos ({len(reservaciones)}):")
            print("-" * 80)
            for reservacion in reservaciones:
                fecha_consulta, fecha_reserva, col1, col2, col3, fila_completa = reservacion
                print(f"📅 {fecha_reserva} | {col1} | {col2} | {col3}")
                print(f"   Consultado: {fecha_consulta}")
                print(f"   Datos completos: {fila_completa}")
                print("-" * 80)
        else:
            print("📋 No hay reservaciones guardadas en la base de datos")

    except sqlite3.Error as e:
        print(f"❌ Error al consultar la base de datos: {e}")
    finally:
        conn.close()


def obtener_ultima_fecha_reservada():
    """Obtiene la fecha más reciente con reservaciones existentes desde la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT MAX(fecha_reserva) 
            FROM reservaciones 
            WHERE fecha_reserva >= date('now')
        """)

        resultado = cursor.fetchone()

        if resultado and resultado[0]:
            try:
                # Convertir de DD/MM/YYYY a objeto date
                fecha_str = resultado[0]
                fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                print(f"📅 Última reservación encontrada: {fecha_str}")
                return fecha_obj
            except ValueError:
                print(f"⚠️ Formato de fecha inválido en DB: {resultado[0]}")
                return None
        else:
            print("📅 No se encontraron reservaciones existentes")
            return None

    except sqlite3.Error as e:
        print(f"❌ Error al consultar última fecha: {e}")
        return None
    finally:
        conn.close()


def obtener_siguiente_fecha_disponible():
    """Obtiene la siguiente fecha disponible para reservar (después de la última reservación)."""
    ultima_fecha = obtener_ultima_fecha_reservada()

    if ultima_fecha:
        # Agregar un día a la última fecha reservada
        siguiente_fecha = ultima_fecha + timedelta(days=1)
        print(f"🗓️ Siguiente fecha disponible para reservar: {siguiente_fecha.strftime('%d/%m/%Y')}")
        return siguiente_fecha
    else:
        # Si no hay reservaciones, usar la fecha de hoy
        hoy = date.today()
        print(f"🗓️ No hay reservaciones previas, iniciando desde hoy: {hoy.strftime('%d/%m/%Y')}")
        return hoy


# ====================================================================
# FUNCIONES DE CONSULTA WEB
# ====================================================================
async def consultar_reservaciones_actuales(page):
    """Consulta las reservaciones actuales desde el sitio web y las guarda en la base de datos."""
    print("🔍 Consultando reservaciones actuales...")

    try:
        # Navegar a la página de consulta de reservaciones
        await page.goto(
            "https://intranet.mx.deloitte.com/ReservacionesHoteling/ConsultarReservaciones",
            timeout=90000,
        )
        await page.wait_for_timeout(5000)

        # Esperar a que aparezca la tabla de reservaciones
        await page.wait_for_selector(
            "//div[@id='gridmisreservas']//table[1]/tbody/tr", timeout=30000
        )

        # Obtener todas las filas de la tabla
        filas = await page.locator("//div[@id='gridmisreservas']//table[1]/tbody/tr").all()

        fecha_hoy = date.today()
        reservaciones_guardadas = 0
        reservaciones_omitidas = 0

        print(f"📋 Encontradas {len(filas)} reservaciones para procesar")

        for i, fila in enumerate(filas):
            try:
                # Obtener todas las celdas de la fila
                celdas = await fila.locator("td").all()

                if len(celdas) >= 8:  # Asegurar que tenemos al menos 8 columnas
                    # Obtener el contenido de todas las celdas
                    datos_celdas = []
                    for celda in celdas:
                        texto = await celda.inner_text()
                        datos_celdas.append(texto.strip())

                    # La columna 8 (índice 7) contiene la fecha
                    if len(datos_celdas) > 7:
                        fecha_str = datos_celdas[7]  # Columna 8 (índice 7)

                        try:
                            # Parsear la fecha en formato DD/MM/YYYY
                            fecha_reserva = datetime.strptime(fecha_str, "%d/%m/%Y").date()

                            # Solo procesar si la fecha es hoy o futura
                            if fecha_reserva >= fecha_hoy:
                                datos_fila = " | ".join(datos_celdas)

                                if guardar_reservacion(datos_fila, fecha_str):
                                    reservaciones_guardadas += 1
                                    print(f"✅ Reservación guardada: {fecha_str} - {datos_celdas[0] if datos_celdas else 'N/A'}")
                                else:
                                    print(f"❌ Error al guardar reservación: {fecha_str}")
                            else:
                                reservaciones_omitidas += 1
                                print(f"⏭️ Reservación omitida (fecha pasada): {fecha_str}")

                        except ValueError:
                            print(f"⚠️ Fecha inválida en fila {i + 1}: '{fecha_str}'")
                    else:
                        print(f"⚠️ Fila {i + 1} no tiene suficientes columnas")
                else:
                    print(f"⚠️ Fila {i + 1} no tiene el número mínimo de celdas requeridas")

            except Exception as e:
                print(f"❌ Error procesando fila {i + 1}: {e}")

        print(f"\n📊 Resumen de consulta:")
        print(f"  ✅ Reservaciones guardadas: {reservaciones_guardadas}")
        print(f"  ⏭️ Reservaciones omitidas (fechas pasadas): {reservaciones_omitidas}")
        print(f"  📋 Total procesadas: {reservaciones_guardadas + reservaciones_omitidas}")

    except Exception as e:
        print(f"❌ Error durante la consulta de reservaciones: {e}")


# ====================================================================
# FUNCIONES DE RESERVA
# ====================================================================

async def intentar_reserva_lugar(page, lugar, fecha_minima, dias_reserva):
    """Intenta reservar un lugar específico y retorna True si tiene éxito, False si está ocupado."""
    print(f"🔄 Intentando reservar lugar: {lugar}")

    if fecha_minima:
        print(f"📅 Solo procesando fechas desde: {fecha_minima.strftime('%d/%m/%Y')}")

    # Hacer clic para abrir el dropdown
    await page.click(
        "xpath= /html/body/section/main/div[2]/div/div/div/div[1]/form/div[4]/div/div[1]/span/span[1]/span/span[1]"
    )

    # Esperar a que aparezca el dropdown y seleccionar el li que contiene el lugar específico
    await page.wait_for_selector("#select2-lugaresDisponibles-results")
    await page.click(f"#select2-lugaresDisponibles-results li:has-text('{lugar}')")

    print(f"✅ Lugar {lugar} seleccionado")

    # Obtener las filas de fechas disponibles
    filas = await page.locator(
        "xpath=/html/body/section/main/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/table/tbody/tr"
    ).all()

    reservas_exitosas = 0
    fechas_omitidas_por_existentes = 0

    for fila in filas:
        celdas = await fila.locator("xpath=td").all()
        datos_fila = " | ".join([await celda.inner_text() for celda in celdas])
        fecha_str = datos_fila.split(" | ")[0]

        try:
            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
            fecha_date = fecha_obj.date()
            dia_semana = fecha_obj.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday

            # Verificar si la fecha es posterior a la fecha mínima (si se especifica)
            if fecha_minima and fecha_date <= fecha_minima:
                fechas_omitidas_por_existentes += 1
                print(f"⏭️ Fecha omitida (ya tiene reservación): {fecha_str}")
                continue

            # Usar los días configurados desde .env en lugar de valores hardcodeados
            if dia_semana in dias_reserva:
                dia_nombre = NOMBRES_DIAS[dia_semana]
                print(f"📅 Procesando fecha: {datos_fila} ({dia_nombre})")
                checkbox = fila.locator("input[type='checkbox'][name='seleccionar']")
                await checkbox.click()

                try:
                    alerta_visible = await page.is_visible(
                        "div.alert.alert-warning.fade.show", timeout=3000
                    )
                    if alerta_visible:
                        alerta = page.locator(
                            "div.alert.alert-warning.fade.show",
                            has_text="No se puede reservar",
                        )
                        aux = await alerta.inner_text()
                        if aux:
                            await checkbox.click()
                            print(f"❌ Día ocupado para {lugar}: {aux}")
                            await page.wait_for_selector(
                                "div.alert.alert-warning.fade.show",
                                state="detached",
                                timeout=8000,
                            )
                            return False  # El lugar está ocupado, intentar con el siguiente
                    else:
                        print(f"✅ Día reservado exitosamente para {lugar} ({dia_nombre})")
                        reservas_exitosas += 1
                except TimeoutError:
                    print(f"⚠️ No se detectó alerta para {lugar}, asumiendo reserva exitosa ({dia_nombre})")
                    reservas_exitosas += 1

        except (ValueError, IndexError) as e:
            print(f"❌ Error procesando fecha: {e}")

    if fechas_omitidas_por_existentes > 0:
        print(f"📊 Fechas omitidas por reservaciones existentes: {fechas_omitidas_por_existentes}")

    return reservas_exitosas > 0


# ====================================================================
# FUNCIONES PRINCIPALES
# ====================================================================

def inicializar_base_datos():
    """Inicializa la base de datos SQLite para guardar las reservaciones."""
    conn = sqlite3.connect("reservaciones.db")
    cursor = conn.cursor()

    # Crear tabla de reservaciones si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_consulta TEXT NOT NULL,
            columna_1 TEXT,
            columna_2 TEXT,
            columna_3 TEXT,
            columna_4 TEXT,
            columna_5 TEXT,
            columna_6 TEXT,
            columna_7 TEXT,
            fecha_reserva TEXT,
            columna_9 TEXT,
            columna_10 TEXT,
            fila_completa TEXT,
            UNIQUE(fecha_reserva, columna_1, columna_2, columna_3)
        )
    """)

    conn.commit()
    conn.close()
    print("📊 Base de datos inicializada correctamente")


def guardar_reservacion(datos_fila, fecha_reserva):
    """Guarda una reservación en la base de datos."""
    conn = sqlite3.connect("reservaciones.db")
    cursor = conn.cursor()

    try:
        # Dividir los datos de la fila en columnas
        columnas = datos_fila.split(" | ")

        # Asegurar que tenemos al menos 10 columnas, completar con None si faltan
        while len(columnas) < 10:
            columnas.append("")

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT OR REPLACE INTO reservaciones 
            (fecha_consulta, columna_1, columna_2, columna_3, columna_4, columna_5, 
             columna_6, columna_7, fecha_reserva, columna_9, columna_10, fila_completa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                fecha_actual,
                columnas[0] if len(columnas) > 0 else "",
                columnas[1] if len(columnas) > 1 else "",
                columnas[2] if len(columnas) > 2 else "",
                columnas[3] if len(columnas) > 3 else "",
                columnas[4] if len(columnas) > 4 else "",
                columnas[5] if len(columnas) > 5 else "",
                columnas[6] if len(columnas) > 6 else "",
                fecha_reserva,
                columnas[8] if len(columnas) > 8 else "",
                columnas[9] if len(columnas) > 9 else "",
                datos_fila,
            ),
        )

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error al guardar reservación: {e}")
        return False
    finally:
        conn.close()


async def run(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()

    try:
        print("🌐 Navegando al sitio de reservas...")
        await page.goto(
            "https://intranet.mx.deloitte.com/ReservacionesHoteling/", timeout=90000
        )
        await page.wait_for_selector(
            "xpath=//h5[contains(text(),'Solicitar reservación')]",
            timeout=90000,
        )

        # PASO 1: Consultar reservaciones existentes primero
        print("🔍 PASO 1: Consultando reservaciones existentes...")
        await consultar_reservaciones_actuales(page)

        # PASO 2: Determinar fecha mínima para nuevas reservas
        fecha_minima = obtener_siguiente_fecha_disponible()

        # PASO 3: Proceder con las reservas normales
        print(
            f"\n🚀 PASO 2: Iniciando proceso de reserva desde {fecha_minima.strftime('%d/%m/%Y')}"
        )

        await page.click("xpath=//h5[contains(text(),'Solicitar reservación')]")
        await page.wait_for_timeout(10000)

        print("👤 Seleccionando tipo de usuario Staff...")

        # Cerrar el modal predictivo si está presente
        try:
            await page.wait_for_selector("#btnCerrarPredictivo", timeout=5000)
            await page.click("#btnCerrarPredictivo", timeout=3000)
            print("🔒 Modal predictivo cerrado.")
        except Exception:
            pass  # Si no está presente, continuar normalmente

        # Esperar a que aparezca el dropdown y seleccionar el li que contiene "Staff"
        await page.wait_for_selector("#select2-tipoLugar-container")
        await page.click("#select2-tipoLugar-container")
        await page.click("#select2-tipoLugar-results li:has-text('Staff')")

        print("✅ Tipo de usuario Staff seleccionado")

        # Intentar reservar con cada lugar disponible hasta que uno funcione
        reserva_exitosa = False
        total_lugares = len(lugares_disponibles)

        for i, lugar in enumerate(lugares_disponibles):
            print(f"\n🎯 Intento {i + 1}/{total_lugares} con lugar: {lugar}")

            if await intentar_reserva_lugar(page, lugar, fecha_minima):
                print(f"✅ Reserva exitosa con el lugar: {lugar}")
                reserva_exitosa = True
                break
            else:
                print(f"❌ No se pudo reservar el lugar: {lugar}")
                if i < len(lugares_disponibles) - 1:
                    print("🔄 Intentando con el siguiente lugar...")
                    await page.wait_for_timeout(
                        2000
                    )  # Pequeña pausa antes del siguiente intento

        if not reserva_exitosa:
            print("❌ No se pudo reservar ninguno de los lugares configurados")
            print("💡 Considera cambiar los lugares en el archivo .env")
        else:
            print("🎉 Proceso de reserva completado exitosamente")

        # PASO 3: Actualizar la base de datos con las nuevas reservas
        print("\n🔄 PASO 3: Actualizando base de datos con nuevas reservas...")
        await consultar_reservaciones_actuales(page)

    except Exception as e:
        print(f"❌ Error durante el proceso de reserva: {e}")
    finally:
        try:
            print("💾 Finalizando reserva...")
            await page.click(
                "xpath=/html/body/section/main/div[2]/div/div/div/div[1]/div[1]/div[2]/div[3]/div/div/button"
            )
            print("✅ Clic en el botón 'Reservar' realizado.")
            await page.wait_for_timeout(25000)
        except Exception as e:
            print(f"⚠️ Error al finalizar: {e}")
        finally:
            await browser.close()
            print("🔒 Navegador cerrado")


async def consultar_reservaciones_main():
    """Función principal para consultar reservaciones solamente."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            print("🌐 Navegando al sitio de reservas para consulta...")
            await page.goto(
                "https://intranet.mx.deloitte.com/ReservacionesHoteling/", timeout=90000
            )
            await page.wait_for_selector(
                "xpath=//h5[contains(text(),'Solicitar reservación')]",
                timeout=90000,
            )

            # Ir directamente a consultar reservaciones
            await consultar_reservaciones_actuales(page)

            # Mostrar reservaciones guardadas
            mostrar_reservaciones_guardadas()

        except Exception as e:
            print(f"❌ Error durante la consulta de reservaciones: {e}")
        finally:
            await browser.close()
            print("🔒 Navegador cerrado")


# https://intranet.mx.deloitte.com/ReservacionesHoteling/ConsultarReservaciones
# //div[@id='gridmisreservas']//table[1]/tbody/tr


def inicializar_base_datos():
    """Inicializa la base de datos SQLite para guardar las reservaciones."""
    conn = sqlite3.connect("reservaciones.db")
    cursor = conn.cursor()

    # Crear tabla de reservaciones si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_consulta TEXT NOT NULL,
            columna_1 TEXT,
            columna_2 TEXT,
            columna_3 TEXT,
            columna_4 TEXT,
            columna_5 TEXT,
            columna_6 TEXT,
            columna_7 TEXT,
            fecha_reserva TEXT,
            columna_9 TEXT,
            columna_10 TEXT,
            fila_completa TEXT,
            UNIQUE(fecha_reserva, columna_1, columna_2, columna_3)
        )
    """)

    conn.commit()
    conn.close()
    print("📊 Base de datos inicializada correctamente")


def guardar_reservacion(datos_fila, fecha_reserva):
    """Guarda una reservación en la base de datos."""
    conn = sqlite3.connect("reservaciones.db")
    cursor = conn.cursor()

    try:
        # Dividir los datos de la fila en columnas
        columnas = datos_fila.split(" | ")

        # Asegurar que tenemos al menos 10 columnas, completar con None si faltan
        while len(columnas) < 10:
            columnas.append("")

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT OR REPLACE INTO reservaciones 
            (fecha_consulta, columna_1, columna_2, columna_3, columna_4, columna_5, 
             columna_6, columna_7, fecha_reserva, columna_9, columna_10, fila_completa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                fecha_actual,
                columnas[0] if len(columnas) > 0 else "",
                columnas[1] if len(columnas) > 1 else "",
                columnas[2] if len(columnas) > 2 else "",
                columnas[3] if len(columnas) > 3 else "",
                columnas[4] if len(columnas) > 4 else "",
                columnas[5] if len(columnas) > 5 else "",
                columnas[6] if len(columnas) > 6 else "",
                fecha_reserva,
                columnas[8] if len(columnas) > 8 else "",
                columnas[9] if len(columnas) > 9 else "",
                datos_fila,
            ),
        )

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error al guardar reservación: {e}")
        return False
    finally:
        conn.close()


async def consultar_reservaciones_actuales(page):
    """Consulta las reservaciones actuales desde el sitio web y las guarda en la base de datos."""
    print("🔍 Consultando reservaciones actuales...")

    try:
        # Navegar a la página de consulta de reservaciones
        await page.goto(
            "https://intranet.mx.deloitte.com/ReservacionesHoteling/ConsultarReservaciones",
            timeout=90000,
        )
        await page.wait_for_timeout(5000)

        # Esperar a que aparezca la tabla de reservaciones
        await page.wait_for_selector(
            "//div[@id='gridmisreservas']//table[1]/tbody/tr", timeout=30000
        )

        # Obtener todas las filas de la tabla
        filas = await page.locator("//div[@id='gridmisreservas']//table[1]/tbody/tr").all()

        fecha_hoy = date.today()
        reservaciones_guardadas = 0
        reservaciones_omitidas = 0

        print(f"📋 Encontradas {len(filas)} reservaciones para procesar")

        for i, fila in enumerate(filas):
            try:
                # Obtener todas las celdas de la fila
                celdas = await fila.locator("td").all()

                if len(celdas) >= 8:  # Asegurar que tenemos al menos 8 columnas
                    # Obtener el contenido de todas las celdas
                    datos_celdas = []
                    for celda in celdas:
                        texto = await celda.inner_text()
                        datos_celdas.append(texto.strip())

                    # La columna 8 (índice 7) contiene la fecha
                    if len(datos_celdas) > 7:
                        fecha_str = datos_celdas[7]  # Columna 8 (índice 7)

                        try:
                            # Parsear la fecha en formato DD/MM/YYYY
                            fecha_reserva = datetime.strptime(fecha_str, "%d/%m/%Y").date()

                            # Solo procesar si la fecha es hoy o futura
                            if fecha_reserva >= fecha_hoy:
                                datos_fila = " | ".join(datos_celdas)

                                if guardar_reservacion(datos_fila, fecha_str):
                                    reservaciones_guardadas += 1
                                    print(f"✅ Reservación guardada: {fecha_str} - {datos_celdas[0] if datos_celdas else 'N/A'}")
                                else:
                                    print(f"❌ Error al guardar reservación: {fecha_str}")
                            else:
                                reservaciones_omitidas += 1
                                print(f"⏭️ Reservación omitida (fecha pasada): {fecha_str}")

                        except ValueError:
                            print(f"⚠️ Fecha inválida en fila {i + 1}: '{fecha_str}'")
                    else:
                        print(f"⚠️ Fila {i + 1} no tiene suficientes columnas")
                else:
                    print(f"⚠️ Fila {i + 1} no tiene el número mínimo de celdas requeridas")

            except Exception as e:
                print(f"❌ Error procesando fila {i + 1}: {e}")

        print(f"\n📊 Resumen de consulta:")
        print(f"  ✅ Reservaciones guardadas: {reservaciones_guardadas}")
        print(f"  ⏭️ Reservaciones omitidas (fechas pasadas): {reservaciones_omitidas}")
        print(f"  📋 Total procesadas: {reservaciones_guardadas + reservaciones_omitidas}")

    except Exception as e:
        print(f"❌ Error durante la consulta de reservaciones: {e}")


# ====================================================================
# FUNCIONES DE RESERVA
# ====================================================================

async def intentar_reserva_lugar(page, lugar, fecha_minima, dias_reserva):
    """Intenta reservar un lugar específico y retorna True si tiene éxito, False si está ocupado."""
    print(f"🔄 Intentando reservar lugar: {lugar}")

    if fecha_minima:
        print(f"📅 Solo procesando fechas desde: {fecha_minima.strftime('%d/%m/%Y')}")

    # Hacer clic para abrir el dropdown
    await page.click(
        "xpath= /html/body/section/main/div[2]/div/div/div/div[1]/form/div[4]/div/div[1]/span/span[1]/span/span[1]"
    )

    # Esperar a que aparezca el dropdown y seleccionar el li que contiene el lugar específico
    await page.wait_for_selector("#select2-lugaresDisponibles-results")
    await page.click(f"#select2-lugaresDisponibles-results li:has-text('{lugar}')")

    print(f"✅ Lugar {lugar} seleccionado")

    # Obtener las filas de fechas disponibles
    filas = await page.locator(
        "xpath=/html/body/section/main/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/table/tbody/tr"
    ).all()

    reservas_exitosas = 0
    fechas_omitidas_por_existentes = 0

    for fila in filas:
        celdas = await fila.locator("xpath=td").all()
        datos_fila = " | ".join([await celda.inner_text() for celda in celdas])
        fecha_str = datos_fila.split(" | ")[0]

        try:
            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
            fecha_date = fecha_obj.date()
            dia_semana = fecha_obj.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday

            # Verificar si la fecha es posterior a la fecha mínima (si se especifica)
            if fecha_minima and fecha_date <= fecha_minima:
                fechas_omitidas_por_existentes += 1
                print(f"⏭️ Fecha omitida (ya tiene reservación): {fecha_str}")
                continue

            # Usar los días configurados desde .env en lugar de valores hardcodeados
            if dia_semana in dias_reserva:
                dia_nombre = NOMBRES_DIAS[dia_semana]
                print(f"📅 Procesando fecha: {datos_fila} ({dia_nombre})")
                checkbox = fila.locator("input[type='checkbox'][name='seleccionar']")
                await checkbox.click()

                try:
                    alerta_visible = await page.is_visible(
                        "div.alert.alert-warning.fade.show", timeout=3000
                    )
                    if alerta_visible:
                        alerta = page.locator(
                            "div.alert.alert-warning.fade.show",
                            has_text="No se puede reservar",
                        )
                        aux = await alerta.inner_text()
                        if aux:
                            await checkbox.click()
                            print(f"❌ Día ocupado para {lugar}: {aux}")
                            await page.wait_for_selector(
                                "div.alert.alert-warning.fade.show",
                                state="detached",
                                timeout=8000,
                            )
                            return False  # El lugar está ocupado, intentar con el siguiente
                    else:
                        print(f"✅ Día reservado exitosamente para {lugar} ({dia_nombre})")
                        reservas_exitosas += 1
                except TimeoutError:
                    print(f"⚠️ No se detectó alerta para {lugar}, asumiendo reserva exitosa ({dia_nombre})")
                    reservas_exitosas += 1

        except (ValueError, IndexError) as e:
            print(f"❌ Error procesando fecha: {e}")

    if fechas_omitidas_por_existentes > 0:
        print(f"📊 Fechas omitidas por reservaciones existentes: {fechas_omitidas_por_existentes}")

    return reservas_exitosas > 0


# ====================================================================
# FUNCIONES PRINCIPALES
# ====================================================================

# Cargar variables de entorno
load_dotenv()

# Inicializar base de datos
inicializar_base_datos()

async def main():
    """Función principal que ejecuta el proceso completo de reserva."""
    async with async_playwright() as playwright:
        await run(playwright)

# Ejecutar el programa
if __name__ == "__main__":
    import sys

    # Verificar si se solicita consultar reservaciones
    if len(sys.argv) > 1 and sys.argv[1] == "--consultar":
        print("🔍 Modo consulta de reservaciones activado")
        asyncio.run(consultar_reservaciones_main())
    else:
        print("🚀 Modo reserva normal activado")
        print(
            "💡 Para consultar reservaciones existentes, usa: python CargaLugar.py --consultar"
        )
        asyncio.run(main())



