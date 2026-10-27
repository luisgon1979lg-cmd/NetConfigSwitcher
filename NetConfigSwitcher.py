"""
NetConfigUtility v1.1 - NetConfigSwitcher
Automatización de direcciones IP (Estáticas y Automáticas por DHCP) con CustomTkinter y permisos de Administrador en Windows.
"""

import os
import sys
import json
import re
import subprocess
import ctypes
from typing import List, Tuple, Optional, Dict
import customtkinter as ctk
from tkinter import messagebox

# ==========================================
# CONSTANTES DE DISEÑO Y COLOR (Mockup UI)
# ==========================================
BG_DARK = "#1f222e"           # Fondo principal de la ventana
PANEL_BG = "#262939"          # Fondo de campos y contenedores
BORDER_PURPLE = "#70569f"     # Borde morado característico del diseño
BORDER_SUBTLE = "#3b3e52"     # Borde sutil para subred y gateway
ACCENT_CYAN = "#43eeff"       # Cyan brillante / Neón
ACCENT_CYAN_HOVER = "#06b6d4" # Hover para botones cyan
TEXT_DARK = "#0b1329"         # Texto oscuro sobre fondo cyan
TEXT_MUTED = "#94a3b8"        # Color gris claro para etiquetas
TEXT_LIGHT = "#f8fafc"        # Blanco / texto destacado
FONT_FAMILY = "Segoe UI"

PASSWORD_SUBNET = "6363"

# Directorio base para persistencia de datos (compatible con PyInstaller frozen)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

HISTORY_FILE = os.path.join(BASE_DIR, "ip_history.json")


# ==========================================
# GESTIÓN DEL HISTORIAL (FIFO - Máx 10 IPs)
# ==========================================
class HistoryManager:
    def __init__(self, filepath: str = HISTORY_FILE, max_items: int = 10):
        self.filepath = filepath
        self.max_items = max_items
        self.history = self.load()

    def load(self) -> List[str]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return [str(ip) for ip in data[:self.max_items]]
            except Exception:
                pass
        return []

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def add(self, ip: str):
        if ip in self.history:
            self.history.remove(ip)
        self.history.insert(0, ip)
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
        self.save()


# ==========================================
# DIÁLOGO MODAL PARA CONTRASEÑA
# ==========================================
class PasswordModal(ctk.CTkToplevel):
    def __init__(self, parent, title="Seguridad", prompt="Introduce la contraseña para desbloquear:"):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x210")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.transient(parent)
        self.grab_set()
        
        self.password: Optional[str] = None
        
        # Centrar sobre la ventana padre
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 190
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 105
        self.geometry(f"+{px}+{py}")

        lbl = ctk.CTkLabel(
            self, text=prompt,
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_LIGHT,
            wraplength=340
        )
        lbl.pack(pady=(25, 12), padx=20)

        self.entry_pass = ctk.CTkEntry(
            self, show="•", width=240, height=36,
            fg_color=PANEL_BG, border_color=BORDER_PURPLE,
            border_width=2, text_color=TEXT_LIGHT,
            font=(FONT_FAMILY, 14), justify="center"
        )
        self.entry_pass.pack(pady=5)
        self.entry_pass.focus()

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(pady=(18, 15))

        btn_ok = ctk.CTkButton(
            frame_btns, text="Desbloquear", width=115, height=32,
            fg_color=ACCENT_CYAN, hover_color=ACCENT_CYAN_HOVER,
            text_color=TEXT_DARK, font=(FONT_FAMILY, 11, "bold"),
            corner_radius=16, command=self._on_confirm
        )
        btn_ok.pack(side="left", padx=6)

        btn_cancel = ctk.CTkButton(
            frame_btns, text="Cancelar", width=95, height=32,
            fg_color="#334155", hover_color="#475569",
            text_color=TEXT_LIGHT, font=(FONT_FAMILY, 11),
            corner_radius=16, command=self._on_cancel
        )
        btn_cancel.pack(side="left", padx=6)

        self.bind("<Return>", lambda e: self._on_confirm())
        self.bind("<Escape>", lambda e: self._on_cancel())

        self.wait_window(self)

    def _on_confirm(self):
        self.password = self.entry_pass.get()
        self.destroy()

    def _on_cancel(self):
        self.password = None
        self.destroy()


# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
class NetConfigSwitcher(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración básica de ventana
        self.title("NetConfigUtility v1.1")
        self.geometry("490x650")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        
        # Centrar ventana en pantalla
        self.center_window(490, 650)

        # Aplicar icono si existe
        icon_path = os.path.join(BUNDLE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Estado interno
        self.subnet_locked = True
        self.history_mgr = HistoryManager()
        self.system_adapters = self.detect_system_adapters()

        self.build_ui()
        self.load_initial_values()

    def center_window(self, width: int, height: int):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, int((screen_w - width) / 2))
        y = max(0, int((screen_h - height) / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def detect_system_adapters(self) -> List[str]:
        """Detecta las interfaces de red dedicadas disponibles en Windows."""
        adapters = []
        try:
            res = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, errors="replace"
            )
            for line in res.stdout.splitlines():
                m = re.search(r'(Dedicado|Dedicated)\s+(.+)$', line)
                if m:
                    adapters.append(m.group(2).strip())
        except Exception:
            pass
        return adapters

    def resolve_adapter_name(self, selected_name: str) -> str:
        """Mapea el nombre seleccionado (ej. 'WiFi 2') al nombre real de la interfaz (ej. 'Wi-Fi 2')."""
        if selected_name in self.system_adapters:
            return selected_name
        
        norm_selected = selected_name.replace(" ", "").replace("-", "").lower()
        for adapter in self.system_adapters:
            if adapter.replace(" ", "").replace("-", "").lower() == norm_selected:
                return adapter
        return selected_name

    def get_adapter_info(self, adapter_name: str) -> Dict:
        """Consulta el estado actual de IP y DHCP de una interfaz."""
        info = {"dhcp": True, "ip": None, "gateway": None}
        try:
            res = subprocess.run(
                ["netsh", "interface", "ipv4", "show", "addresses", adapter_name],
                capture_output=True, text=True, errors="replace"
            )
            for line in res.stdout.splitlines():
                line_clean = line.strip()
                line_lower = line_clean.lower()
                if "dhcp habilitado" in line_lower or "dhcp enabled" in line_lower:
                    info["dhcp"] = "s" in line_lower or "yes" in line_lower
                elif "dirección ip" in line_lower or "ip address" in line_lower:
                    parts = line_clean.split(":")
                    if len(parts) > 1 and not info["ip"]:
                        info["ip"] = parts[1].strip()
                elif line_lower.startswith("puerta de enlace predeterminada") or line_lower.startswith("default gateway"):
                    parts = line_clean.split(":")
                    if len(parts) > 1:
                        gw = parts[1].strip()
                        if gw and gw != "None":
                            info["gateway"] = gw
        except Exception:
            pass
        return info

    def refresh_current_adapter_status(self):
        """Actualiza la etiqueta con el modo actual (DHCP o Estática) de la interfaz seleccionada."""
        selected = self.adapter_var.get()
        actual = self.resolve_adapter_name(selected)
        info = self.get_adapter_info(actual)

        if info.get("dhcp"):
            ip_str = f" ({info['ip']})" if info.get('ip') else ""
            self.lbl_adapter_mode.configure(
                text=f"● Modo actual: Automático / DHCP{ip_str}",
                text_color=ACCENT_CYAN
            )
        else:
            ip_str = f" ({info['ip']})" if info.get('ip') else ""
            self.lbl_adapter_mode.configure(
                text=f"● Modo actual: IP Estática{ip_str}",
                text_color="#f59e0b"
            )

    def _on_adapter_changed(self, new_val):
        self.refresh_current_adapter_status()

    def build_ui(self):
        # 0. Título superior elegante
        title_label = ctk.CTkLabel(
            self, text="NetConfigUtility v1.1",
            font=(FONT_FAMILY, 15, "bold"),
            text_color=TEXT_LIGHT
        )
        title_label.pack(pady=(18, 12))

        # 1. Selector de Adaptador
        adapter_options = ["WiFi 2", "Ethernet 5"]
        self.adapter_var = ctk.StringVar(value=adapter_options[0])

        self.combo_adapter = ctk.CTkOptionMenu(
            self,
            values=adapter_options,
            variable=self.adapter_var,
            command=self._on_adapter_changed,
            width=360,
            height=38,
            corner_radius=10,
            fg_color=PANEL_BG,
            button_color="#33374c",
            button_hover_color="#434963",
            dropdown_fg_color=PANEL_BG,
            dropdown_hover_color="#343950",
            dropdown_text_color=TEXT_LIGHT,
            text_color=TEXT_LIGHT,
            font=(FONT_FAMILY, 13, "bold"),
            dropdown_font=(FONT_FAMILY, 12)
        )
        self.combo_adapter.configure(dynamic_resizing=False)
        self.combo_adapter.pack(pady=(0, 6))

        # Indicador de Modo Actual de la Red (DHCP vs Estática)
        frame_mode_status = ctk.CTkFrame(self, fg_color="transparent")
        frame_mode_status.pack(pady=(0, 14))

        self.lbl_adapter_mode = ctk.CTkLabel(
            frame_mode_status,
            text="● Modo actual: Consultando...",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=ACCENT_CYAN
        )
        self.lbl_adapter_mode.pack(side="left", padx=(0, 6))

        btn_refresh_status = ctk.CTkButton(
            frame_mode_status,
            text="🔄",
            width=24,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#33374c",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 11),
            command=self.refresh_current_adapter_status
        )
        btn_refresh_status.pack(side="left")

        # 2. SECCIÓN: IP Address
        lbl_ip = ctk.CTkLabel(
            self, text="IP Address",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        lbl_ip.pack(pady=(0, 5))

        # 4 Cajas de Octetos idénticas al diseño
        frame_octets = ctk.CTkFrame(self, fg_color="transparent")
        frame_octets.pack(pady=(0, 10))

        # Octeto 1 (Fijo: 192)
        self.entry_oct1 = self._create_octet_box(frame_octets, "192", readonly=True)
        self.entry_oct1.pack(side="left", padx=4)

        # Octeto 2 (Fijo: 168)
        self.entry_oct2 = self._create_octet_box(frame_octets, "168", readonly=True)
        self.entry_oct2.pack(side="left", padx=4)

        # Octeto 3 (Editable: default 1)
        self.entry_oct3 = self._create_octet_box(frame_octets, "1", readonly=False)
        self.entry_oct3.pack(side="left", padx=4)
        self.entry_oct3.bind("<KeyRelease>", self._on_oct3_change)
        self.entry_oct3.bind("<Key>", self._filter_octet_keys)

        # Octeto 4 (Editable: default 100)
        self.entry_oct4 = self._create_octet_box(frame_octets, "100", readonly=False)
        self.entry_oct4.pack(side="left", padx=4)
        self.entry_oct4.bind("<Key>", self._filter_octet_keys)

        # Fila de Acciones: Botón Clear IP + Selector de Historial FIFO
        frame_ip_actions = ctk.CTkFrame(self, fg_color="transparent")
        frame_ip_actions.pack(pady=(0, 16))

        # Botón Clear IP (píldora cyan)
        self.btn_clear = ctk.CTkButton(
            frame_ip_actions,
            text="✕ Clear IP",
            width=115,
            height=30,
            corner_radius=15,
            fg_color=ACCENT_CYAN,
            hover_color=ACCENT_CYAN_HOVER,
            text_color=TEXT_DARK,
            font=(FONT_FAMILY, 11, "bold"),
            command=self.clear_ip_fields
        )
        self.btn_clear.pack(side="left", padx=(0, 10))

        # Menú desplegable para el Historial FIFO (máximo 10)
        self.history_var = ctk.StringVar(value="📜 Historial (0)")
        self.opt_history = ctk.CTkOptionMenu(
            frame_ip_actions,
            values=["(Sin historial)"],
            variable=self.history_var,
            command=self._on_history_selected,
            width=175,
            height=30,
            corner_radius=15,
            fg_color=PANEL_BG,
            button_color="#33374c",
            button_hover_color="#434963",
            text_color=TEXT_LIGHT,
            dropdown_fg_color=PANEL_BG,
            dropdown_hover_color="#343950",
            font=(FONT_FAMILY, 11)
        )
        self.opt_history.pack(side="left")

        # 3. SECCIÓN: Subnet Mask (Locked)
        self.lbl_sub = ctk.CTkLabel(
            self, text="Subnet Mask (Locked)",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.lbl_sub.pack(pady=(0, 5))

        frame_subnet_container = ctk.CTkFrame(
            self, width=360, height=40,
            fg_color=PANEL_BG,
            border_color=BORDER_SUBTLE,
            border_width=1.5,
            corner_radius=8
        )
        frame_subnet_container.pack(pady=(0, 16))
        frame_subnet_container.pack_propagate(False)

        # Candado / botón de desbloqueo
        self.btn_lock = ctk.CTkButton(
            frame_subnet_container,
            text="🔒",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#32374b",
            text_color=ACCENT_CYAN,
            font=(FONT_FAMILY, 15),
            command=self.toggle_subnet_lock
        )
        self.btn_lock.pack(side="left", padx=(6, 0))

        # Entrada de máscara de subred
        self.entry_subnet = ctk.CTkEntry(
            frame_subnet_container,
            width=300,
            height=34,
            fg_color="transparent",
            border_width=0,
            justify="center",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 13, "bold")
        )
        self.entry_subnet.insert(0, "255.255.255.0")
        self.entry_subnet.configure(state="disabled")
        self.entry_subnet.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 4. SECCIÓN: Gateway (.200 Fixed)
        lbl_gw = ctk.CTkLabel(
            self, text="Gateway (.200 Fixed)",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        lbl_gw.pack(pady=(0, 5))

        frame_gw_container = ctk.CTkFrame(
            self, width=360, height=40,
            fg_color=PANEL_BG,
            border_color=BORDER_SUBTLE,
            border_width=1.5,
            corner_radius=8
        )
        frame_gw_container.pack(pady=(0, 20))
        frame_gw_container.pack_propagate(False)

        self.lbl_gateway_val = ctk.CTkLabel(
            frame_gw_container,
            text="192.168.1.200",
            font=(FONT_FAMILY, 13, "bold"),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.lbl_gateway_val.pack(side="left", padx=(16, 0), fill="both", expand=True)

        # Badge lateral ".200" idéntico al mockup
        badge_frame = ctk.CTkFrame(
            frame_gw_container, width=54, height=26,
            fg_color="transparent",
            border_color=ACCENT_CYAN,
            border_width=1.5,
            corner_radius=6
        )
        badge_frame.pack(side="right", padx=(0, 8), pady=6)
        badge_frame.pack_propagate(False)

        lbl_badge_text = ctk.CTkLabel(
            badge_frame, text=".200",
            text_color=ACCENT_CYAN,
            font=(FONT_FAMILY, 11, "bold")
        )
        lbl_badge_text.pack(expand=True)

        # 5. BOTÓN 1: APPLY SETTINGS (ESTÁTICA)
        self.btn_apply = ctk.CTkButton(
            self,
            text="APPLY SETTINGS (ESTÁTICA)",
            width=280,
            height=42,
            corner_radius=21,
            fg_color=ACCENT_CYAN,
            hover_color=ACCENT_CYAN_HOVER,
            text_color=TEXT_DARK,
            font=(FONT_FAMILY, 12, "bold"),
            command=self.apply_network_config
        )
        self.btn_apply.pack(pady=(0, 10))

        # 6. BOTÓN 2: OBTENER IP AUTOMÁTICAMENTE (DHCP)
        self.btn_dhcp = ctk.CTkButton(
            self,
            text="⚡ OBTENER IP AUTOMÁTICA (DHCP)",
            width=280,
            height=40,
            corner_radius=20,
            fg_color=PANEL_BG,
            hover_color="#33384c",
            border_color=ACCENT_CYAN,
            border_width=1.5,
            text_color=ACCENT_CYAN,
            font=(FONT_FAMILY, 11, "bold"),
            command=self.apply_dhcp_config
        )
        self.btn_dhcp.pack(pady=(0, 14))

        # Status feedback sutil
        self.lbl_status = ctk.CTkLabel(
            self, text="Listo para aplicar configuración",
            font=(FONT_FAMILY, 10),
            text_color="#64748b"
        )
        self.lbl_status.pack()

    def _create_octet_box(self, parent, initial_val: str, readonly: bool = False) -> ctk.CTkEntry:
        """Crea una caja de octeto con borde púrpura idéntica al diseño."""
        entry = ctk.CTkEntry(
            parent,
            width=64,
            height=42,
            corner_radius=8,
            border_width=2,
            border_color=BORDER_PURPLE,
            fg_color=PANEL_BG,
            text_color=TEXT_LIGHT,
            font=(FONT_FAMILY, 14, "bold"),
            justify="center"
        )
        entry.insert(0, initial_val)
        if readonly:
            entry.bind("<Key>", lambda e: "break")
            entry.configure(cursor="arrow")
        return entry

    def _filter_octet_keys(self, event):
        """Permite únicamente números y teclas de control, con auto-avance."""
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return None
        
        # Auto-avance con punto o slash
        if event.char in (".", "/"):
            if event.widget == self.entry_oct3._entry:
                self.entry_oct4.focus()
            return "break"

        # Permitir solo dígitos
        if not event.char.isdigit():
            return "break"

        # Comprobar longitud máxima de 3 dígitos
        current_text = event.widget.get()
        if len(current_text) >= 3 and not event.widget.select_present():
            # Si se escribe un 4to dígito en octeto 3, saltar al 4
            if event.widget == self.entry_oct3._entry:
                self.entry_oct4.focus()
                self.entry_oct4.delete(0, "end")
                self.entry_oct4.insert(0, event.char)
            return "break"

        return None

    def _on_oct3_change(self, event=None):
        """Actualiza la puerta de enlace en tiempo real según el 3er octeto."""
        oct3 = self.entry_oct3.get().strip()
        if oct3.isdigit() and 0 <= int(oct3) <= 255:
            self.lbl_gateway_val.configure(text=f"192.168.{oct3}.200")
            if len(oct3) == 3 and event and event.widget == self.entry_oct3._entry:
                self.entry_oct4.focus()
        elif oct3 == "":
            self.lbl_gateway_val.configure(text="192.168. .200")
        else:
            self.lbl_gateway_val.configure(text=f"192.168.{oct3}.200")

    def load_initial_values(self):
        """Carga el historial y sincroniza valores iniciales."""
        self._refresh_history_dropdown()
        self._on_oct3_change()
        self.refresh_current_adapter_status()

    def _refresh_history_dropdown(self):
        """Actualiza el listado del desplegable de historial FIFO."""
        history = self.history_mgr.history
        if history:
            self.history_var.set(f"📜 Historial ({len(history)})")
            self.opt_history.configure(values=history)
        else:
            self.history_var.set("📜 Historial (0)")
            self.opt_history.configure(values=["(Sin historial)"])

    def _on_history_selected(self, selected_ip: str):
        """Carga la IP seleccionada del historial en los campos correspondientes."""
        if selected_ip == "(Sin historial)":
            return
        
        parts = selected_ip.split(".")
        if len(parts) == 4 and parts[0] == "192" and parts[1] == "168":
            self.entry_oct3.delete(0, "end")
            self.entry_oct3.insert(0, parts[2])
            
            self.entry_oct4.delete(0, "end")
            self.entry_oct4.insert(0, parts[3])
            
            self._on_oct3_change()
            self.lbl_status.configure(text=f"IP cargada desde historial: {selected_ip}")
            
        self.history_var.set(f"📜 Historial ({len(self.history_mgr.history)})")

    def clear_ip_fields(self):
        """Limpia los campos del 3er y 4to octeto."""
        self.entry_oct3.delete(0, "end")
        self.entry_oct3.insert(0, "1")
        self.entry_oct4.delete(0, "end")
        self.entry_oct4.focus()
        self._on_oct3_change()
        self.lbl_status.configure(text="Campos de IP restablecidos")

    def toggle_subnet_lock(self):
        """Gestiona el candado de la máscara de subred mediante clave 6363."""
        if self.subnet_locked:
            dialog = PasswordModal(
                self,
                title="Seguridad - Máscara de Subred",
                prompt="Introduce la contraseña para desbloquear la máscara:"
            )
            if dialog.password is not None:
                if dialog.password == PASSWORD_SUBNET:
                    self.subnet_locked = False
                    self.entry_subnet.configure(state="normal", text_color=TEXT_LIGHT)
                    self.btn_lock.configure(text="🔓")
                    self.lbl_sub.configure(text="Subnet Mask (Unlocked)", text_color=ACCENT_CYAN)
                    self.lbl_status.configure(text="Máscara de subred desbloqueada")
                else:
                    messagebox.showerror("Seguridad", "Contraseña incorrecta. Acceso denegado.")
        else:
            self.subnet_locked = True
            self.entry_subnet.configure(state="disabled", text_color=TEXT_MUTED)
            self.btn_lock.configure(text="🔒")
            self.lbl_sub.configure(text="Subnet Mask (Locked)", text_color=TEXT_MUTED)
            self.lbl_status.configure(text="Máscara de subred bloqueada")

    def validate_inputs(self) -> Tuple[bool, str, str, str, str]:
        """Valida que todos los octetos y la máscara sean correctos."""
        oct3 = self.entry_oct3.get().strip()
        oct4 = self.entry_oct4.get().strip()
        subnet = self.entry_subnet.get().strip()

        if not (oct3.isdigit() and 0 <= int(oct3) <= 255):
            return False, "El tercer octeto debe ser un número entero entre 0 y 255.", "", "", ""

        if not (oct4.isdigit() and 0 <= int(oct4) <= 255):
            return False, "El cuarto octeto debe ser un número entero entre 0 y 255.", "", "", ""

        sub_parts = subnet.split(".")
        if len(sub_parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in sub_parts):
            return False, "La máscara de subred debe tener el formato estándar (ej. 255.255.255.0).", "", "", ""

        ip = f"192.168.{oct3}.{oct4}"
        gateway = f"192.168.{oct3}.200"

        return True, "", ip, subnet, gateway

    def apply_network_config(self):
        """Ejecuta el comando netsh para aplicar la configuración estática."""
        ok, err_msg, ip, subnet, gateway = self.validate_inputs()
        if not ok:
            messagebox.showwarning("Dato Inválido", err_msg)
            return

        selected_adapter = self.adapter_var.get()
        actual_adapter = self.resolve_adapter_name(selected_adapter)

        cmd = f'netsh interface ipv4 set address name="{actual_adapter}" static {ip} {subnet} {gateway}'

        self.lbl_status.configure(text=f"Aplicando configuración a '{actual_adapter}'...")
        self.update_idletasks()

        try:
            resultado = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
                errors="replace"
            )

            if resultado.returncode == 0:
                self.history_mgr.add(ip)
                self._refresh_history_dropdown()
                self.refresh_current_adapter_status()

                self.lbl_status.configure(text=f"Configurado: {ip} en {actual_adapter}")
                messagebox.showinfo(
                    "Configuración Exitosa",
                    f"Adaptador '{actual_adapter}' configurado en IP Estática.\n\n"
                    f"• IP: {ip}\n"
                    f"• Máscara: {subnet}\n"
                    f"• Gateway: {gateway}"
                )
            else:
                err_text = resultado.stderr.strip() or resultado.stdout.strip()
                if "elevación" in err_text.lower() or "elevation" in err_text.lower():
                    err_text += "\n\nSe requieren privilegios de Administrador en Windows."

                self.lbl_status.configure(text="Error al aplicar configuración")
                messagebox.showerror(
                    "Error de Red",
                    f"No se pudo aplicar la configuración en '{actual_adapter}':\n\n{err_text}"
                )
        except Exception as ex:
            self.lbl_status.configure(text="Excepción en la ejecución")
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al ejecutar netsh:\n{str(ex)}")

    def apply_dhcp_config(self):
        """Configura el adaptador seleccionado para obtener IP y DNS automáticamente (DHCP)."""
        selected_adapter = self.adapter_var.get()
        actual_adapter = self.resolve_adapter_name(selected_adapter)

        self.lbl_status.configure(text=f"Obteniendo IP automáticamente en '{actual_adapter}'...")
        self.update_idletasks()

        try:
            # 1. Configurar IP para DHCP (Automático)
            cmd_ip = f'netsh interface ipv4 set address name="{actual_adapter}" source=dhcp'
            res_ip = subprocess.run(
                cmd_ip, capture_output=True, text=True, shell=True, errors="replace"
            )

            # 2. Configurar DNS para DHCP (Automático)
            cmd_dns = f'netsh interface ipv4 set dnsservers name="{actual_adapter}" source=dhcp'
            res_dns = subprocess.run(
                cmd_dns, capture_output=True, text=True, shell=True, errors="replace"
            )

            if res_ip.returncode == 0:
                self.lbl_status.configure(text=f"IP Automática (DHCP) asignada a '{actual_adapter}'")
                self.refresh_current_adapter_status()
                messagebox.showinfo(
                    "Configuración DHCP Exitosa",
                    f"El adaptador '{actual_adapter}' ahora está configurado para:\n\n"
                    f"✓ Obtener una dirección IP automáticamente (DHCP)\n"
                    f"✓ Obtener servidores DNS automáticamente"
                )
            else:
                err_text = res_ip.stderr.strip() or res_ip.stdout.strip()
                if "elevación" in err_text.lower() or "elevation" in err_text.lower():
                    err_text += "\n\nSe requieren privilegios de Administrador en Windows."

                self.lbl_status.configure(text="Error al activar DHCP")
                messagebox.showerror(
                    "Error de Red",
                    f"No se pudo configurar DHCP en '{actual_adapter}':\n\n{err_text}"
                )
        except Exception as ex:
            self.lbl_status.configure(text="Excepción en la ejecución")
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al configurar DHCP:\n{str(ex)}")


# ==========================================
# VERIFICACIÓN Y ELEVACIÓN DE UAC
# ==========================================
def verify_admin_elevation():
    """Verifica si la aplicación tiene privilegios de Administrador. Si no, solicita elevación."""
    if "--no-uac" in sys.argv:
        return True

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if not is_admin:
        if getattr(sys, "frozen", False):
            exe_path = sys.executable
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", exe_path, params, None, 1
            )
        else:
            script = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}'.strip(), None, 1
            )
        sys.exit(0)
    return True


if __name__ == "__main__":
    verify_admin_elevation()

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = NetConfigSwitcher()
    app.mainloop()
