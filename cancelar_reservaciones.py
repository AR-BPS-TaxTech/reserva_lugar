"""Script para cancelar reservaciones desde la intranet usando Playwright.

Este script navega a la página de consulta de reservaciones y hace click
en cada botón que representa una "Cancelación". Después de cada click
espera la confirmación mediante cualquiera de los siguientes eventos (en
orden):

- aparición de un diálogo (confirm), que será aceptado automáticamente
- aparición de una alerta/notification en la página (p.ej. div.alert)
- que el propio botón deje de estar visible o se deshabilite

Uso:
  python cancelar_reservaciones.py [--headless]

Opciones:
  --headless   Ejecuta Playwright en modo headless si se especifica

Notas:
 - La página puede requerir autenticación previa en la intranet; este
   script no realiza login automático. Ejecutar desde una sesión donde
   la intranet ya esté accesible o agregar pasos de autenticación según
   necesidad.
"""

import asyncio
import os
import re
import sys
from typing import Optional
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Page,
    Locator,
)
from dotenv import load_dotenv


# Cargar .env si existe
load_dotenv()

TARGET_URL = os.getenv(
    "URL_CANCELAR",
    "https://intranet.mx.deloitte.com/ReservacionesHoteling/ConsultarReservaciones",
)


async def aceptar_dialogo_si_existe(page: Page, timeout: int = 3000) -> bool:
    """Intenta aceptar un diálogo de confirmación.

    Se manejan en prioridad:
    1) Diálogos nativos (window.confirm/alert) capturados por el evento "dialog".
    2) Modales/in-page dialogs comunes (busca contenedores .modal, .swal2-container, etc.)
       y hace click en botones con texto 'Si' / 'Sí' (variantes de mayúsculas).
    3) Botones globales con texto 'Si' como último recurso.

    Retorna True si se detectó y aceptó alguna confirmación, False en caso contrario.
    """
    # 1) Diálogo nativo del navegador
    try:
        dialog = await page.wait_for_event("dialog", timeout=timeout)
        print("💬 Diálogo nativo detectado: aceptando...")
        await dialog.accept()
        return True
    except PlaywrightTimeoutError:
        pass

    # 2) Buscar modales / contenedores de confirmación comunes y pulsar 'Si'/'Sí'
    modal_selectors = [
        "div.modal.fade.show",
        ".swal2-container",
        ".sweet-alert",
        "div[role='dialog']",
        "div.ui-dialog",
        # Kendo UI confirm dialog (ejemplo provisto)
        ".k-widget.k-window.k-dialog.k-confirm",
        "div.k-dialog-buttongroup",
    ]

    for sel in modal_selectors:
        try:
            # obtener todos los elementos que coinciden y seleccionar el primero visible
            elems = await page.locator(sel).all()
            visible_elem = None
            for el in elems:
                try:
                    if await el.is_visible():
                        visible_elem = el
                        break
                except Exception:
                    continue

            if not visible_elem:
                continue

            # dentro del modal visible buscar botones de confirmación en español
            btn = visible_elem.locator(
                "button.k-button.k-primary:has-text('si'), button:has-text('Si'), button:has-text('SI'), button:has-text('si'), button:has-text('Sí'), button:has-text('SÍ')"
            )
            if await btn.count() > 0:
                print(f"💬 Modal detectado ({sel}), pulsando botón de confirmación")
                await btn.first.click()
                # esperar que el modal se cierre o desaparezca
                try:
                    # esperar hasta que el elemento deje de ser visible o se desconecte
                    await visible_elem.wait_for(state="detached", timeout=3000)
                except PlaywrightTimeoutError:
                    await page.wait_for_timeout(500)
                return True
        except Exception:
            # cualquier excepción aquí la ignoramos y probamos el siguiente selector
            continue

    # 3) Intentar localizar botones por rol/texto (p.ej. get_by_role('button', name='si'))
    try:
        # usar regex para cubrir 'si' y 'sí' (mayúsculas/minúsculas)
        btn_role = page.get_by_role(
            "button", name=re.compile(r"^s[ií]$", re.IGNORECASE)
        )
        if await btn_role.count() > 0:
            print("💬 Botón por rol/texto detectado; haciendo click")
            await btn_role.first.click()
            await page.wait_for_timeout(400)
            return True
    except Exception:
        pass

    # 4) Último recurso: buscar botones globales "Si" en la página por selector genérico
    try:
        global_btn = page.locator(
            "button:has-text('Si'), button:has-text('SI'), button:has-text('si'), button:has-text('Sí')"
        )
        if await global_btn.count() > 0:
            print("💬 Botón global 'Si' detectado; haciendo click")
            await global_btn.first.click()
            await page.wait_for_timeout(400)
            return True
    except Exception:
        pass

    # nada detectado
    return False


async def esperar_confirmacion(
    page: Page, previous_button: Optional[Locator] = None, timeout: int = 10000
) -> None:
    """Espera una confirmación tras la acción de cancelar.

    La confirmación se considera cumplida si ocurre cualquiera de:
    - aparece un elemento tipo alerta (div.alert)
    - el botón anterior desaparece o se deshabilita
    - se alcanza el timeout
    """
    try:
        # esperar por una alerta en la página
        await page.wait_for_selector("div.alert", timeout=timeout)
        print("🔔 Alerta de confirmación detectada en la página")
        # dar tiempo breve para que la alerta se muestre completamente
        await page.wait_for_timeout(800)
        return
    except PlaywrightTimeoutError:
        # no apareció alerta; comprobar si el botón ya no existe o está deshabilitado
        if previous_button:
            try:
                # re-evaluar si el botón sigue en el DOM
                visible = await previous_button.is_visible()
                enabled = await previous_button.is_enabled()
                if not visible or not enabled:
                    print("ℹ️ El botón fue removido o deshabilitado tras la acción")
                    return
            except Exception:
                # el objeto anterior puede fallar si el elemento fue removido
                print("ℹ️ El botón anterior ya no existe (removido del DOM)")
                return

        # último recurso: esperar un pequeño tiempo y continuar
        print(
            "⏳ No se detectó confirmación explícita; continuando después de espera máxima"
        )
        await page.wait_for_timeout(500)


async def cancelar_todas(page: Page) -> int:
    """Busca y hace click en todos los botones de cancelación.

    Retorna el número de cancelaciones intentadas.
    """
    intentos = 0

    while True:
        # Localizar botones de cancelación (Locator). Trabajamos siempre con el
        # primer elemento porque el DOM suele cambiar tras cada cancelación.
        selector = "button[title='Cancelación'], button[id='cancelacion'], button.btn-icon[title='Cancelación']"
        locator = page.locator(selector)
        count = await locator.count()
        if count == 0:
            print("✅ No se encontraron más botones de cancelación.")
            break

        print(
            f"🔎 Encontrados {count} botones de cancelación (re-evaluando antes de click)"
        )

        # Trabajar con el primer botón actual (Locator.nth(0))
        boton: Locator = locator.nth(0)

        try:
            # Extraer algún identificador visible para logs (atributo data-cancelar o onclick)
            data_cancelar = await boton.get_attribute("data-cancelar")
            onclick = await boton.get_attribute("onclick")
            descripcion = (
                f"data-cancelar={data_cancelar}"
                if data_cancelar
                else (onclick or "sin-atributos")
            )
            print(f"🖱️ Haciendo click en botón de cancelación ({descripcion})")

            # Registrar un handler one-time para diálogos nativos justo antes del click
            page.once("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

            # Hacer click; el diálogo nativo (si existe) será aceptado por el handler
            await boton.click()

            # Intentar aceptar modales in-page / botones de confirmación
            accepted = await aceptar_dialogo_si_existe(page, timeout=12000)
            if accepted:
                print("✅ Confirmación en página aceptada")

            # esperar una confirmación en la página o la desaparición del botón
            await esperar_confirmacion(page, previous_button=boton, timeout=12000)

            intentos += 1
            # Pequeña pausa entre cancelaciones para no saturar el servidor
            await page.wait_for_timeout(800)

        except Exception as e:
            print(f"❌ Error al intentar cancelar (se omite): {e}")
            # si falla un botón, intentar con el siguiente después de una pausa
            await page.wait_for_timeout(1000)

    return intentos


async def main(headless: bool = False, url: Optional[str] = None) -> None:
    url = url or TARGET_URL

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            print(f"🌐 Navegando a: {url}")
            await page.goto(url, timeout=90000)

            # Esperar que la tabla/elementos carguen (selector genérico)
            try:
                await page.wait_for_selector(
                    "//div[@id='gridmisreservas']//table//tr", timeout=20000
                )
            except PlaywrightTimeoutError:
                # si no existe la tabla, seguir con búsqueda de botones
                print(
                    "⚠️ No se detectó la tabla de reservaciones; se buscarán botones igualmente"
                )

            # Ejecutar la cancelación iterativa
            total = await cancelar_todas(page)
            print(f"🎯 Intentos de cancelación realizados: {total}")

        except Exception as e:
            print(f"❌ Error general en el proceso: {e}")
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    # headless_flag = "--headless" in sys.argv
    asyncio.run(main(headless=False))
