# CargaLugar - Sistema de Reserva de Lugares

Sistema automatizado para la reserva de lugares de oficina utilizando una interfaz gráfica intuitiva y automatización web.

## Descripción

CargaLugar es una aplicación de Python que automatiza el proceso de reserva de lugares en un sistema de hoteling corporativo. La aplicación presenta una interfaz gráfica que permite seleccionar el lugar deseado y luego automatiza el proceso de reserva en el sitio web correspondiente.

## Características

- **Interfaz gráfica amigable**: Utiliza Tkinter para una selección fácil del lugar deseado
- **Automatización web**: Emplea Playwright para automatizar la navegación y reserva
- **Reserva inteligente**: Automáticamente reserva los días miércoles y jueves
- **Detección de conflictos**: Identifica cuando un lugar ya está ocupado
- **Amplia selección**: Incluye más de 60 opciones de lugares disponibles

## Requisitos del Sistema

- Python 3.7 o superior
- Windows (recomendado)
- Conexión a internet
- Acceso al sistema de reservas corporativo

## Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias requeridas:
   ```bash
   pip install -r requirements.txt
   ```
3. Instala los navegadores de Playwright:
   ```bash
   playwright install
   ```

## Uso

1. Ejecuta la aplicación:
   ```bash
   python CargaLugar.py
   ```

2. Selecciona el lugar deseado de la lista desplegable

3. Haz clic en "Aceptar"

4. La aplicación abrirá automáticamente el navegador y realizará la reserva

## Estructura del Proyecto

```
CargaLugar/
├── CargaLugar.py       # Archivo principal de la aplicación
├── requirements.txt    # Dependencias del proyecto
└── README.md          # Este archivo
```

## Funcionalidades Técnicas

- **Selección de lugar**: Lista desplegable con todas las opciones de lugares disponibles
- **Automatización de formularios**: Completa automáticamente los campos del sitio web
- **Manejo de errores**: Detecta y maneja alertas de lugares ocupados
- **Reserva específica**: Enfocado en días miércoles y jueves
- **Interfaz centrada**: Ventana posicionada automáticamente en el centro de la pantalla

## Lugares Disponibles

El sistema incluye lugares en el edificio P17, distribuidos en múltiples pisos:
- Pisos 1, 2, 3, 4, 5, 6, 7, 8, 9
- Pisos 10, 12, 13, 14, 15, 16, 18, 19, 21, 22, 23, 24
- Lugar especial P16-1904

## Dependencias

- **playwright**: Automatización del navegador web
- **asyncio**: Programación asíncrona
- **tkinter**: Interfaz gráfica de usuario
- **datetime**: Manejo de fechas y horarios

## Notas Importantes

- La aplicación está configurada para funcionar con un sistema de reservas específico
- Se requiere autenticación en el sistema corporativo
- Los tiempos de espera están optimizados para conexiones estables

## Contribución

Si deseas contribuir a este proyecto, por favor:
1. Haz un fork del repositorio
2. Crea una rama para tu característica
3. Realiza tus cambios
4. Envía un pull request

## Licencia

Este proyecto es para uso interno y educativo.

---

*Desarrollado para automatizar el proceso de reserva de lugares de oficina*
