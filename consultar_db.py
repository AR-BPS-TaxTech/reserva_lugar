# Archivo de ejemplo para consultar la base de datos de reservaciones
import sqlite3
from datetime import datetime, date, timedelta


def consultar_reservaciones_por_fecha(fecha_inicio=None, fecha_fin=None):
    """Consulta reservaciones en un rango de fechas específico."""
    conn = sqlite3.connect("reservaciones.db")
    cursor = conn.cursor()

    try:
        if fecha_inicio and fecha_fin:
            cursor.execute(
                """
                SELECT * FROM reservaciones 
                WHERE fecha_reserva BETWEEN ? AND ?
                ORDER BY fecha_reserva ASC
            """,
                (fecha_inicio, fecha_fin),
            )
        else:
            cursor.execute("""
                SELECT * FROM reservaciones 
                ORDER BY fecha_reserva ASC
            """)

        reservaciones = cursor.fetchall()

        print(f"📋 Reservaciones encontradas: {len(reservaciones)}")

        for reservacion in reservaciones:
            print(f"ID: {reservacion[0]}")
            print(f"Fecha consulta: {reservacion[1]}")
            print(f"Fecha reserva: {reservacion[8]}")
            print(f"Datos: {reservacion[12]}")
            print("-" * 50)

    except sqlite3.Error as e:
        print(f"❌ Error al consultar: {e}")
    finally:
        conn.close()


def reservaciones_proximas(dias=7):
    """Muestra reservaciones en los próximos N días."""
    fecha_hoy = date.today().strftime("%d/%m/%Y")
    fecha_limite = (date.today() + timedelta(days=dias)).strftime("%d/%m/%Y")

    print(f"🔍 Buscando reservaciones entre {fecha_hoy} y {fecha_limite}")
    consultar_reservaciones_por_fecha(fecha_hoy, fecha_limite)


if __name__ == "__main__":
    print("📊 Consultando base de datos de reservaciones")

    # Mostrar todas las reservaciones
    consultar_reservaciones_por_fecha()

    # Mostrar solo próximas reservaciones
    # reservaciones_proximas(14)  # Próximos 14 días
