import asyncio
import os
import re
from datetime import date, timedelta
from typing import List
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page

# Reusar la función de persistencia existente
try:
    from CargaLugar import guardar_reservacion
except Exception:

    def guardar_reservacion(datos_fila: str, fecha_reserva: str) -> bool:
        return False


load_dotenv()

# Configuración desde .env
LUGARES_RESERVA = [
    s.strip() for s in os.getenv("LUGARES_RESERVA", "").split(",") if s.strip()
]
DIAS_RESERVA = [
    int(s.strip()) for s in os.getenv("DIAS_RESERVA", "2,3").split(",") if s.strip()
]
BUSCAR_DIAS = int(os.getenv("BUSCAR_DIAS", "28"))


def generar_fechas_objetivo(dias_semana: List[int], dias_adelante: int) -> List[str]:
    hoy = date.today()
    fechas = []
    for d in range(dias_adelante + 1):
        f = hoy + timedelta(days=d)
        if f.weekday() in dias_semana:
            fechas.append(f.strftime("%d/%m/%Y"))
    return fechas


async def seleccionar_fecha_en_ui(page: Page, fecha_str: str) -> bool:
    try:
        await page.goto(
            "https://intranet.mx.deloitte.com/ReservacionesHoteling/Reservacion",
            timeout=90_000,
        )
        await page.wait_for_load_state("networkidle", timeout=30000)

        try:
            await page.click("li#tabstrip-tab-2[role='tab']")
        except Exception:
            pass

        # Intentar rellenar fecha directamente
        try:
            await page.locator("#fechaInicio").fill(fecha_str)
        except Exception:
            pass

        try:
            await page.locator("#fechaFinal").fill(fecha_str)
        except Exception:
            pass

        # Intentar elegir Staff si el selector está disponible
        try:
            await page.click("#select2-tipoLugarFecha-container")
            await page.click("#select2-tipoLugarFecha-results li:has-text('Staff')")
        except Exception:
            pass

        # Rellenar fechas en los campos (intentos con role-based API y fallbacks)
        try:
            # Fecha inicial: intentar primero por role (combobox) y si falla, por id
            try:
                await page.get_by_role(
                    "combobox", name=re.compile("Fecha inicial", re.I)
                ).click()
                await page.get_by_role(
                    "combobox", name=re.compile("Fecha inicial", re.I)
                ).fill(fecha_str)
                await page.get_by_role(
                    "combobox", name=re.compile("Fecha inicial", re.I)
                ).press("Tab")
            except Exception:
                try:
                    await page.locator("#fechaInicio").fill(fecha_str)
                    await page.locator("#fechaInicio").press("Tab")
                except Exception:
                    pass

            # Fecha final: role-based y fallback a id
            try:
                await page.get_by_role(
                    "combobox", name=re.compile("Fecha final", re.I)
                ).click()
                await page.get_by_role(
                    "combobox", name=re.compile("Fecha final", re.I)
                ).fill(fecha_str)
                await page.get_by_role(
                    "combobox", name=re.compile("Fecha final", re.I)
                ).press("Tab")
            except Exception:
                try:
                    await page.locator("#fechaFinal").fill(fecha_str)
                    await page.locator("#fechaFinal").press("Tab")
                except Exception:
                    pass

            # Intentar seleccionar horas (inicio 09:00, fin 16:00). No es obligatorio; usar fallbacks silenciosos.
            try:
                # Selector de hora de inicio (si existe)
                await page.locator("#seccionfechaHoraInicio b").click()
                await page.get_by_role("option", name=re.compile("09:00", re.I)).click()
            except Exception:
                pass

            try:
                # Selector de hora final (similar al de inicio)
                await page.locator("#seccionfechaHoraFin b").click()
                try:
                    await page.get_by_role(
                        "option", name=re.compile("16:00", re.I)
                    ).click()
                except Exception:
                    try:
                        await page.get_by_role(
                            "option", name=re.compile("16:30", re.I)
                        ).click()
                    except Exception:
                        pass
            except Exception:
                pass

            await page.wait_for_timeout(200)
        except Exception:
            pass

        # Click Buscar
        try:
            await page.get_by_role("button", name=re.compile("buscar", re.I)).click()
        except Exception:
            try:
                await page.click("button:has-text('Buscar')")
            except Exception:
                pass

        # esperar resultados
        try:
            await page.wait_for_selector(
                "#collapseLugares tbody tr:nth-child(1)", timeout=60000
            )
        except Exception:
            return False

        await page.wait_for_load_state("networkidle", timeout=30000)
        return True
    except Exception as e:
        print(f"⚠️ Error seleccionando fecha {fecha_str}: {e}")
        return False


async def intentar_reservar_para_fecha(
    page: Page, fecha_str: str, lugares_prioridad: List[str]
) -> bool:
    """Flujo robusto: re-query, find row by lugar+fecha, mark checkbox, confirm by reading td[7]."""
    try:
        # asegurar que hay resultados (esperar la segunda fila para evitar falsos positivos)
        try:
            await page.wait_for_selector("xpath=(//tbody/tr)[2]", timeout=90_000)
        except Exception:
            print(f"🔎 No hay lugares listados para la fecha {fecha_str}")
            return False

        for lugar in lugares_prioridad:
            # re-query filas
            try:
                filas = await page.locator("tbody tr").all()
            except Exception as e:
                print(f"⚠️ Error al obtener filas: {e}")
                filas = []

            matched_row = None
            for r in filas:
                try:
                    col_lugar = (await r.locator("td").nth(0).inner_text()).strip()
                    col_fecha = (await r.locator("td").nth(1).inner_text()).strip()
                    col_estado = (await r.locator("td").nth(2).inner_text()).strip()
                except Exception:
                    continue

                if col_lugar != lugar:
                    continue
                if fecha_str not in col_fecha:
                    continue
                if "disponible" not in col_estado.lower():
                    print(
                        f"⛔ Fila encontrada pero está ocupada: {col_lugar} | {col_fecha} | estado='{col_estado}'"
                    )
                    continue

                matched_row = r
                break

            if not matched_row:
                continue

            # marcar checkbox
            chk = None
            try:
                chk = matched_row.locator("input[type='checkbox']")
                await chk.wait_for(state="visible", timeout=90_000)
            except Exception:
                try:
                    chk = matched_row.locator("#Tr")
                    await chk.wait_for(state="visible", timeout=90_000)
                except Exception:
                    chk = None

            if chk is None:
                print(
                    f"⚠️ No se encontró checkbox seleccionable en la fila para {lugar} {fecha_str}"
                )
                continue

            try:
                await chk.check()
            except Exception:
                try:
                    await chk.click()
                except Exception as e:
                    print(f"⚠️ No se pudo marcar checkbox para {lugar} {fecha_str}: {e}")
                    continue

            # Click Reservar
            try:
                await page.get_by_role(
                    "button", name=re.compile("Reservar", re.I)
                ).click()
            except Exception:
                try:
                    await page.click("button:has-text('Reservar')")
                except Exception as e:
                    print(f"⚠️ Error al clicar 'Reservar': {e}")
                    continue

            # Click Generar reserva / confirmar
            try:
                await page.get_by_role(
                    "button", name=re.compile("Generar reserva|Generar", re.I)
                ).click()
            except Exception:
                try:
                    await page.click("button:has-text('Generar reserva')")
                except Exception as e:
                    print(f"⚠️ Error al clicar 'Generar reserva': {e}")
                    continue

            # esperar que la UI procese
            try:
                await page.wait_for_load_state("networkidle", timeout=60000)
            except Exception:
                pass

            # Re-query y confirmar por fila relativa
            confirmado = False

            # Intentar hasta 3 veces: esperar que se muestre el grid y la primera fila.
            # Si no aparece, recargar la página y reintentar (respetando timeouts).
            grid_available = False
            for attempt in range(3):
                try:
                    await page.wait_for_selector(
                        "#gridmisreservas", state="visible", timeout=90_000
                    )
                    await page.wait_for_selector(
                        "xpath=(//tbody/tr)[1]", state="visible", timeout=60000
                    )
                    grid_available = True
                    break
                except Exception as e:
                    print(f"⚠️ Intento {attempt + 1}/3: el grid no apareció: {e}")
                    try:
                        # Recargar la página antes de reintentar
                        await page.reload(timeout=90_000)
                        await page.wait_for_load_state("networkidle", timeout=30000)
                    except Exception as e2:
                        print(
                            f"⚠️ Error al recargar la página en intento {attempt + 1}: {e2}"
                        )
                    await asyncio.sleep(0.5)

            if not grid_available:
                print(
                    "⚠️ El grid de reservas no se mostró tras 3 reintentos; continúo con siguiente lugar"
                )
                continue

            for _ in range(3):
                await asyncio.sleep(0.4)
                try:
                    filas_post = await page.locator("tbody tr").all()
                except Exception as e:
                    print(f"⚠️ No se pudieron obtener filas tras generar reserva: {e}")
                    filas_post = []

                for rf in filas_post:
                    try:
                        rlugar = (await rf.locator("td").nth(6).inner_text()).strip()
                        rfecha = (await rf.locator("td").nth(7).inner_text()).strip()
                    except Exception:
                        continue

                    # Si la fila reportada tiene el mismo lugar y la fecha objetivo está
                    if lugar in rlugar and fecha_str in rfecha:
                        confirmado = True
                        break

                if confirmado:
                    break

            if not confirmado:
                print(
                    f"⚠️ No se confirmó la reserva para {lugar} {fecha_str} tras retries; continúo con siguiente lugar"
                )
                continue

            # Persistir
            try:
                hora_inicio = "09:00"
                hora_fin = "16:00"
                datos_fila = f"{lugar} | {fecha_str} | {hora_inicio}-{hora_fin}"
                ok_db = guardar_reservacion(datos_fila, fecha_str)
                if ok_db:
                    print(f"💾 Reservación guardada en DB: {lugar} | {fecha_str}")
                else:
                    print(
                        f"⚠️ No se pudo guardar reservación en DB para {lugar} {fecha_str}"
                    )
            except Exception as e:
                print(f"⚠️ Error guardando en DB: {e}")

            # Volver a la vista principal
            try:
                await page.goto(
                    "https://intranet.mx.deloitte.com/ReservacionesHoteling/Reservacion",
                    timeout=90_000,
                )
            except Exception:
                try:
                    await page.evaluate(
                        "window.location.href = 'https://intranet.mx.deloitte.com/ReservacionesHoteling/Reservacion'"
                    )
                except Exception:
                    pass

            await page.wait_for_timeout(800)
            return True

        # fin for lugares
        print(f"❌ No se encontró lugar disponible en prioridad para {fecha_str}")
        return False

    except Exception as e:
        print(f"⚠️ Error intentando reservar para {fecha_str}: {e}")
        return False


async def main() -> None:
    fechas = generar_fechas_objetivo(DIAS_RESERVA, BUSCAR_DIAS)
    if not fechas:
        print("❌ No hay fechas objetivo calculadas")
        return

    print(f"🔎 Fechas objetivo: {fechas}")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        for fecha in fechas:
            print(f"\n--- Procesando fecha {fecha} ---")
            ok = await seleccionar_fecha_en_ui(page, fecha)
            if not ok:
                print(f"⚠️ No se pudo preparar la búsqueda para {fecha}")
                continue

            reservado = await intentar_reservar_para_fecha(page, fecha, LUGARES_RESERVA)
            if reservado:
                await page.wait_for_timeout(1200)
            else:
                await page.wait_for_timeout(800)

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
