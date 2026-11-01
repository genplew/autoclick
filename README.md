# Funciona - Grabador y Reproductor de Movimientos de Ratón

# Creador - Codder- Developer - Tester
Genplew

## Descripción

**Funciona** es una herramienta para grabar y reproducir movimientos, clicks y scroll del ratón. Permite automatizar acciones repetitivas guardando una secuencia de eventos del ratón en formato JSON y reproduciéndolos posteriormente con control de velocidad, parada de emergencia y modo bucle.

## Características

- **Grabación precisa**: Captura movimientos, clics (izquierdo/derecho/medio) y desplazamiento de scroll con marcas temporales
- **Reproducción sincronizada**: Reproduce los eventos respetando los tiempos originales con factor de velocidad configurable
- **Interfaz gráfica**: Aplicación con Tkinter con botones visuales, configuración de tecla de parada y modo bucle
- **Parada de emergencia**: Se puede detener en cualquier momento con una tecla configurable (por defecto `Scroll Lock`)
- **Modo arrastre inteligente**: Soporta arrastre con predicción para movimientos más suaves
- **Guardado automático**: Las grabaciones se guardan en `mouse_track.json`
- **Recuerdos de posición**: Guarda la posición de la ventana en `window_pos.json`

## Requerimientos

### Dependencias Python

El programa requiere las siguientes librerías:

```txt
pyautogui
keyboard
pynput
numpy
```

### Instalación

```bash
pip install pyautogui keyboard pynput numpy
```

### Requisitos del sistema

- Python 3.x
- Windows (probado en entorno Windows)
- Permisos para controlar el ratón y teclado (puede requerir ejecución como administrador en algunos casos)
- Resolución de pantalla (configurado para 3840x2160 por defecto)

## Archivos del Programa

| Archivo | Descripción |
| --- | --- |
| `gui.py` | Interfaz gráfica principal (Tkinter). Permite grabar, reproducir, parar con hotkey y modo bucle |
| `recorder.py` | Grabador por línea de comandos. También envía datos UDP a `localhost:12345` |
| `player.py` | Reproductor por línea de comandos con parada de emergencia |
| `protocol.py` | Define estructura de datos para envío UDP (`MouseData`) |
| `receive_udp.py` | Recibe datos UDP (complementario al recorder) |
| `mouse_track.json` | Archivo de grabación (se genera al grabar) |
| `window_pos.json` | Guarda posición de la ventana GUI |
| `*.png` | Iconos de la interfaz (record, play, stop) |

## Uso

### Interfaz gráfica (Recomendado)

```bash
python gui.py
```

La interfaz muestra:
- **Botón Record (grabar)**: Inicia cuenta regresiva de 3 segundos y empieza a grabar. Al pulsar la tecla de parada se guarda en `mouse_track.json`
- **Botón Play (reproducir)**: Reproduce la última grabación con cuenta regresiva de 3 segundos
- **Botón Stop (detener)**: Detiene grabación o reproducción
- **Tecla de parada**: Configurable (por defecto `\`` o `scroll lock` según versión)
- **Loop**: Si está marcado, reproduce en bucle hasta detenerlo

### Línea de comandos

**Grabar:**
```bash
python recorder.py
```
- Espera 3 segundos
- Graba hasta pulsar `Scroll Lock` o `Ctrl+C`
- Guarda en `mouse_track.json`

**Reproducir:**
```bash
python player.py
```
- Espera 3 segundos
- Reproduce eventos
- Se puede detener con `Scroll Lock` o `Ctrl+C`

## Configuración

### En `gui.py`
- `WIDTH, HEIGHT`: Resolución de pantalla (3840, 2160)
- `MIN_MOVE_INTERVAL`: Intervalo mínimo entre eventos de movimiento (0.01s)
- `RECORDING_DELAY`: Retraso antes de grabar/reproducir (3s)
- `SPEED_FACTOR`: Factor de velocidad (1.0 = velocidad normal)
- `STOP_KEY`: Tecla de parada por defecto
- `DRAG_PREDICTION`: Predicción de arrastre para suavizar

### En `recorder.py`
- `ADDRESS`: Dirección UDP (`('localhost', 12345)`)
- `STOP_HOTKEY`: Tecla para detener grabación
- `MIN_MOVE_INTERVAL`: Filtrado de movimientos

### En `player.py`
- `SPEED_FACTOR`: Velocidad de reproducción
- `DRAG_PREDICTION`: Suavizado de arrastre
- `STOP_KEY`: Tecla de emergencia

## Notas Importantes

- **Seguridad**: El programa controla completamente el ratón y teclado. Úsalo con precaución.
- **Coordenadas absolutas**: Graba posiciones absolutas de pantalla. Funciona mejor en la misma resolución.
- **Durante reproducción**: Mueve el ratón manualmente puede interferir con la reproducción.
- **UDP**: `recorder.py` envía coordenadas por UDP mientras arrastra/cli quea - usado para integración con otros componentes.
- **Arrastre**: El sistema detecta `pressed` para aplicar `dragTo` en lugar de `moveTo`.
- **Filtrado**: Se filtran movimientos muy rápidos durante arrastre para reducir tamaño del archivo.

## Solución de Problemas

- **No se detecta tecla de parada**: Verifica que `keyboard` tenga permisos. En Windows puede requerir ejecutar como administrador.
- **La reproducción es errática**: Ajusta `SPEED_FACTOR` o desactiva `DRAG_PREDICTION`.
- **No funciona después de cambio de resolución**: Las coordenadas absolutas no coincidirán con otra resolución.
- **Falta `keyboard`/permisos**: Algunas teclas requieren permisos elevados en Windows.
