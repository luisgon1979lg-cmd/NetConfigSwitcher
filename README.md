# NetConfigSwitcher (NetConfigUtility v1.2) 🌐⚡

Aplicación moderna para Windows desarrollada en **Python** con **CustomTkinter** que automatiza la configuración de direcciones IP estáticas y automáticas (DHCP), máscaras de subred y puertas de enlace (Gateway) en cualquier adaptador de red de cualquier ordenador mediante comandos nativos `netsh`.

![Interfaz](Gemini_Generated_Image_5toqri5toqri5toq.jfif)

---

## ✨ Características Principales

- **Detección Dinámica de Adaptadores (Multi-equipo)**: Escanea en tiempo real todas las interfaces de red físicas y dedicadas del ordenador (`Wi-Fi`, `Ethernet`, adaptadores USB, etc.), adaptándose automáticamente a cualquier equipo Windows sin nombres fijos predefinidos.
- **Acceso Rápido a Conexiones de Red**: Botón integrado **`🌐 Redes`** que abre directamente la ventana clásica de Conexiones de red de Windows (`ncpa.cpl`) y botón **`🔄`** para recargar adaptadores al conectar cables o adaptadores USB.
- **Doble Modo (IP Estática y DHCP Automático)**:
  - **APPLY SETTINGS (ESTÁTICA)**: Configura la IP estática personalizada con máscara y gateway.
  - **⚡ OBTENER IP AUTOMÁTICA (DHCP)**: Restablece el adaptador para obtener IP y servidores DNS de forma automática mediante DHCP con un solo clic.
- **Detección del Modo Actual**: Muestra en tiempo real si el adaptador seleccionado se encuentra en modo DHCP o con IP Estática, junto con su dirección IP activa.
- **Diseño Simétrico de Casillas IP y Gateway**:
  - **Casillas de IP**: 4 casillas individuales (`[192] [168] [X] [Y]`).
  - **Casillas de Gateway**: 4 casillas idénticas (`[192] [168] [X] [200]`). El 3.er octeto se sincroniza automáticamente al escribir la IP.
  - **Candado de Seguridad en Gateway**: El 4.º octeto (`.200`) está protegido por defecto. Al pulsar el candado 🔒 e introducir la clave **`6363`**, se desbloquea 🔓 para permitir personalizarlo (ej. `.1`, `.254`).
- **Máscara de Subred Protegida por Clave**:
  - Fijada en `255.255.255.0` y protegida por candado con la contraseña **`6363`**.
- **Historial FIFO (Hasta 10 IPs)**: Guarda las últimas 10 IPs aplicadas con persistencia local.
- **Botón Clear IP**: Píldora en cyan neón (`✕ Clear IP`) para restablecer los campos al instante.
- **Elevación Automática de Privilegios (UAC)**: Solicita permisos de Administrador de Windows automáticamente.
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

