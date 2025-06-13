import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import threading

# Lista de lugares
opciones = [
    "P16-1904", "P17-1001", "P17-1002", "P17-1003", "P17-1004",
    "P17-102", "P17-103", "P17-104", "P17-105", "P17-106",
    "P17-1201", "P17-1202", "P17-1203", "P17-1204",
    "P17-1301", "P17-1302", "P17-1303", "P17-1304",
    "P17-1401", "P17-1402", "P17-1403", "P17-1404",
    "P17-1501", "P17-1502", "P17-1503", "P17-1504",
    "P17-1601", "P17-1602", "P17-1603", "P17-1604",
    "P17-1801", "P17-1802", "P17-1803", "P17-1804",
    "P17-1901", "P17-1902", "P17-1903",
    "P17-201", "P17-202", "P17-203", "P17-204", "P17-205", "P17-206",
    "P17-2101", "P17-2102", "P17-2103", "P17-2104", "P17-2105", "P17-2106",
    "P17-2201", "P17-2202", "P17-2203", "P17-2204",
    "P17-2301", "P17-2302", "P17-2303", "P17-2304",
    "P17-2401", "P17-2402", "P17-2403", "P17-2404",
    "P17-301", "P17-302", "P17-303", "P17-304",
    "P17-401", "P17-402", "P17-403", "P17-404",
    "P17-501", "P17-502", "P17-503", "P17-504",
    "P17-601", "P17-602", "P17-603", "P17-604",
    "P17-701", "P17-702", "P17-703", "P17-704",
    "P17-801", "P17-802", "P17-803", "P17-804",
    "P17-901", "P17-902", "P17-903", "P17-904"
]
seleccion = None

def aceptar():
    global seleccion
    seleccion = variable.get()
    print(f"Opción seleccionada: {seleccion}")
    ventana.destroy()
    #Play
    threading.Thread(target=asyncio.run, args=(main(),)).start()
    
# Crear la ventana
ventana = tk.Tk()
ventana.title("Reserva de Lugar")
# Tamaño
ancho_ventana = 400
alto_ventana = 200
# Posición
ancho_pantalla = ventana.winfo_screenwidth()
alto_pantalla = ventana.winfo_screenheight()
pos_x = (ancho_pantalla - ancho_ventana) // 2
pos_y = (alto_pantalla - alto_ventana) // 2
ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")
# Mensaje
mensaje = tk.Label(ventana, text="Seleccione el lugar que desea reservar:", font=("Arial", 12))
mensaje.pack(pady=10)
# Almacenar
variable = tk.StringVar(value="Seleccionar:")
# Desplegable
desplegable = ttk.Combobox(ventana, textvariable=variable, values=opciones, state="readonly", font=("Arial", 10))
desplegable.pack(pady=10)
# Botón de aceptar
boton_aceptar = tk.Button(ventana, text="Aceptar", command=aceptar, font=("Arial", 10))
boton_aceptar.pack(pady=10)
# Iniciar
ventana.mainloop()


async def run(playwright):
    global seleccion
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()
    #playwright codegen --browser=chromium https://intranet.mx.deloitte.com/ReservacionesHoteling/
    

    try:
        await page.goto("https://intranet.mx.deloitte.com/ReservacionesHoteling/", timeout=90000)
        await page.wait_for_selector("xpath=/html/body/section/div[2]/div/div/div[1]/div/div/a/div/div[1]/div/i", timeout=90000)
        await page.click("xpath=/html/body/section/div[2]/div/div/div[1]/div/div/a/div/div[1]/div/i")
        await page.wait_for_timeout(10000)
        
        while True:
            await page.click("xpath= /html/body/section/main/div[2]/div/div/div/div[1]/form/div[1]/div/div[1]/span/span[1]/span/span[1]")
            element = page.locator("xpath=/html/body/section/main/div[2]/div/div/div/div[1]/form/div[1]/div/div[1]/span/span[1]/span/span[1]")
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            title_value = await element.get_attribute("title")
            if  title_value == "Staff": break
        
        while True:
            await page.click("xpath= /html/body/section/main/div[2]/div/div/div/div[1]/form/div[4]/div/div[1]/span/span[1]/span/span[1]")
            element = page.locator("xpath=/html/body/section/main/div[2]/div/div/div/div[1]/form/div[4]/div/div[1]/span/span[1]/span/span[1]")
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            title_value = await element.get_attribute("title")
            if  title_value == seleccion: break
        
        filas = await page.locator("xpath=/html/body/section/main/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/table/tbody/tr").all()


        for fila in filas:
            celdas = await fila.locator("xpath=td").all()
            # Extraer el texto de cada celda y unirlo con " | "
            datos_fila = " | ".join([await celda.inner_text() for celda in celdas])

            fecha_str = datos_fila.split(" | ")[0]

            try:
                fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                dia_semana = fecha_obj.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday

                if (dia_semana == 2 or dia_semana == 3) :
                    print(datos_fila)
                    checkbox = fila.locator("input[type='checkbox'][name='seleccionar']")
                    await checkbox.click()
                    aux=""
                    try:
                        alerta_visible = await page.is_visible("div.alert.alert-warning.fade.show", timeout=3000)
                        if alerta_visible:
                            alerta = page.locator("div.alert.alert-warning.fade.show", has_text="No se puede reservar")
                            aux = await alerta.inner_text()
                            if aux:
                                await checkbox.click()
                                print("❌ Día ocupado:", aux)
                                await page.wait_for_selector("div.alert.alert-warning.fade.show", state='detached', timeout=8000)#Si no funciona poner el timeout en 10000
                        else:
                            print("✅ Día reservado")
                    except TimeoutError:
                        print("❌ No se detectó ninguna alerta")
                #else:
                    #print("No es día de oficina.")
            except (ValueError, IndexError) as e:
                print(f"El texto no es una fecha válida o no está en el formato esperado. Error: {e}")
                
    except Exception as e:
        print(f"No se pudo hacer clic en el elemento. Error: {e}")
    finally:
        await page.click("xpath=/html/body/section/main/div[2]/div/div/div/div[1]/div[1]/div[2]/div[3]/div/div/button")
        print("Clic en el botón 'Reservar' realizado.") 
        await page.wait_for_timeout(25000) 
        await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
