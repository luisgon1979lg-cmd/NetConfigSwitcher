# NetConfigSwitcher (NetConfigUtility v1.0) 🌐⚡

Aplicación moderna para Windows desarrollada en **Python** con **CustomTkinter** que automatiza la configuración de direcciones IP estáticas, máscaras de subred y puertas de enlace (Gateway) en adaptadores de red mediante comandos nativos `netsh`.

![Interfaz](Gemini_Generated_Image_5toqri5toqri5toq.jfif)

---

## ✨ Características Principales

- **Doble Modo (IP Estática y DHCP Automático)**:
  - **APPLY SETTINGS (ESTÁTICA)**: Configura la IP estática personalizada con máscara y gateway.
  - **⚡ OBTENER IP AUTOMÁTICA (DHCP)**: Restablece el adaptador para obtener IP y servidores DNS de forma automática mediante DHCP con un solo clic.
- **Detección del Modo Actual**: Muestra en tiempo real si el adaptador seleccionado se encuentra en modo DHCP o con IP Estática, junto con su dirección IP activa.
- **Elevación Automática de Privilegios (UAC)**: Detecta al inicio si se cuenta con permisos de administrador. Si no, solicita elevación automáticamente en Windows.
- **Selector de Adaptador**: Menú desplegable para elegir de forma estricta entre adaptadores como `WiFi 2` y `Ethernet 5`, con detección dinámica del nombre real del sistema.
- **Entrada Visual de Octetos**: 4 bloques estilizados con borde violeta (`#70569f`):
  - `192` y `168` fijos.
  - 3.er y 4.º octetos editables con control numérico (0–255) y auto-avance.
- **Historial FIFO (Hasta 10 IPs)**: Almacena las últimas 10 IPs aplicadas con éxito. Al seleccionar cualquiera de ellas, se cargan de inmediato los datos en pantalla.
- **Botón Clear IP**: Píldora en cyan neón (`✕ Clear IP`) para restablecer los campos con un solo clic.
- **Máscara de Subred Protegida por Clave**:
  - Por defecto fijada en `255.255.255.0` y bloqueada contra escritura.
  - Al pulsar el candado 🔒 se solicita contraseña (`6363`) en una ventana modal oscura; si es correcta, el campo se desbloquea 🔓.
- **Puerta de Enlace (Gateway .200 Automática)**:
  - Se recalcula en tiempo real al editar el 3.er octeto (`192.168.X.200`).
  - Distintivo visual `.200` en cyan idéntico al diseño de interfaz.
- **Aplicación Segura y Notificaciones**:
  - Aplica la configuración mediante:
    ```cmd
    netsh interface ipv4 set address name="{adaptador}" static {ip} {mascara} {gateway}
    ```
  - Mensajes de confirmación y advertencias de error detalladas.

---

## 🛠️ Requisitos e Instalación

- **Sistema Operativo**: Windows 10 o Windows 11
- **Python**: 3.8 o superior

### 1. Clonar el repositorio
```bash
git clone https://github.com/luisgon1979lg-cmd/NetConfigSwitcher.git
cd NetConfigSwitcher
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 🚀 Uso

### Opción A (Ejecutable Portable .EXE - Sin necesidad de Python)
Simplemente haz doble clic sobre:
```
NetConfigUtility.exe
```
> **Nota de Portabilidad**: Este archivo `.exe` es completamente autónomo (incluye Python y librerías). Puedes copiar únicamente el archivo `NetConfigUtility.exe` a un pendrive USB o a cualquier otro ordenador con Windows 10/11 y funcionará directamente sin instalar nada.

### Opción B: Doble clic con script Batch
Ejecuta el archivo:
```
Iniciar_NetConfigUtility.bat
```

### Opción C: Desde la línea de comandos de Python
```bash
python NetConfigSwitcher.py
```

---

## 📦 Compilación del Ejecutable (.EXE)
Si realizas modificaciones en el código y deseas regenerar el ejecutable standalone:
```bash
python -m PyInstaller --noconsole --onefile --name "NetConfigUtility" --icon "icon.ico" --add-data "icon.ico;." --collect-all customtkinter --uac-admin NetConfigSwitcher.py
```

---

## 🔐 Seguridad
- **Contraseña para desbloquear la máscara de subred**: `6363`
- La aplicación no almacena credenciales de red sensibles y solo modifica configuraciones locales de interfaz a petición expresa del usuario.

