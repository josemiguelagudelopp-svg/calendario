from datetime import datetime
import re
import customtkinter as ctk
from supabase import Client, create_client

# Tus credenciales configuradas
SUPABASE_URL = "https://obcwirxjvypxdpxudyqu.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_nFUde6igy8iYfKScAMFhKQ_K1e7ot-d"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


class InventarioApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("Control de Inventario y Salidas - Laboratorio")
    self.geometry("980x650")

    self.datos_actuales = []  # Guardará todos los datos de la BD

    # Layout Principal
    self.grid_rowconfigure(3, weight=1)
    self.grid_columnconfigure(0, weight=1)

    # 1. Título y Estado
    self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
    self.header_frame.grid(
        row=0, column=0, padx=20, pady=(20, 5), sticky="ew"
    )

    self.titulo_label = ctk.CTkLabel(
        self.header_frame,
        text="Inventario y Salidas del Laboratorio",
        font=ctk.CTkFont(size=22, weight="bold"),
    )
    self.titulo_label.pack(side="left")

    self.estado_label = ctk.CTkLabel(
        self.header_frame,
        text="● Sincronizado",
        text_color="#10b981",
        font=ctk.CTkFont(size=12),
    )
    self.estado_label.pack(side="right", padx=10)

    # 2. Barra de Herramientas (Botones principales)
    self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
    self.toolbar_frame.grid(row=1, column=0, padx=20, pady=(5, 10), sticky="ew")

    self.btn_nuevo = ctk.CTkButton(
        self.toolbar_frame,
        text="+ Agregar Elemento",
        fg_color="#059669",
        hover_color="#047857",
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.abrir_modal_crear,
    )
    self.btn_nuevo.pack(side="left")

    self.btn_movimientos = ctk.CTkButton(
        self.toolbar_frame,
        text="🔍 Búsqueda y Movimientos",
        fg_color="#0284c7",
        hover_color="#0369a1",
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.abrir_modal_busqueda_movimientos,
    )
    self.btn_movimientos.pack(side="left", padx=12)

    # Botones para Salidas de Campo MVZ
    self.btn_salida = ctk.CTkButton(
        self.toolbar_frame,
        text="+ Registrar Salida MVZ",
        fg_color="#d97706",
        hover_color="#b45309",
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.abrir_modal_salida_campo,
    )
    self.btn_salida.pack(side="left")

    self.btn_admin_salidas = ctk.CTkButton(
        self.toolbar_frame,
        text="🚌 Administrar Salidas",
        fg_color="#78350f",
        hover_color="#92400e",
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.abrir_modal_admin_salidas,
    )
    self.btn_admin_salidas.pack(side="left", padx=12)

    # 3. BARRA DE BÚSQUEDA EN LA INTERFAZ PRINCIPAL
    self.search_main_var = ctk.StringVar()
    self.search_main_var.trace_add("write", self.filtrar_pantalla_principal)

    self.entry_busqueda_principal = ctk.CTkEntry(
        self,
        placeholder_text=(
            "🔍 Buscar en la lista principal (ej: guantes, alcohol...)"
        ),
        textvariable=self.search_main_var,
        height=38,
        font=ctk.CTkFont(size=13),
    )
    self.entry_busqueda_principal.grid(
        row=2, column=0, padx=20, pady=(0, 10), sticky="ew"
    )

    # 4. Contenedor de la lista con Scroll
    self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
    self.scroll_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
    self.scroll_frame.grid_columnconfigure(0, weight=1)

    # Cargar datos iniciales e iniciar la sincronización automática
    self.cargar_datos()
    self.auto_refrescar()

  def cargar_datos(self):
    try:
      response = supabase.table("inventario").select("*").execute()
      self.datos_actuales = response.data
      self.filtrar_pantalla_principal()
    except Exception as e:
      print(f"Error al cargar datos: {e}")

  def auto_refrescar(self):
    try:
      response = supabase.table("inventario").select("*").execute()
      nuevos_datos = response.data

      if nuevos_datos != self.datos_actuales:
        self.datos_actuales = nuevos_datos
        self.filtrar_pantalla_principal()
    except Exception:
      pass

    self.after(3000, self.auto_refrescar)

  def filtrar_pantalla_principal(self, *args):
    texto = self.search_main_var.get().lower().strip()
    if not texto:
      filtrados = self.datos_actuales
    else:
      filtrados = [
          item
          for item in self.datos_actuales
          if texto in item["nombre"].lower()
      ]
    self.actualizar_interfaz(filtrados)

  def actualizar_interfaz(self, items):
    for widget in self.scroll_frame.winfo_children():
      widget.destroy()

    if not items:
      vacio = ctk.CTkLabel(
          self.scroll_frame,
          text="No se encontraron elementos.",
          text_color="gray",
      )
      vacio.pack(pady=30)
      return

    items_ordenados = sorted(
        items,
        key=lambda x: (
            0 if x["cantidad"] <= x["stock_minimo"] else 1,
            x["nombre"].lower(),
        ),
    )

    for item in items_ordenados:
      es_critico = item["cantidad"] <= item["stock_minimo"]

      bg_color = "#450a0a" if es_critico else "#1e293b"
      borde_color = "#ef4444" if es_critico else "#334155"

      row_frame = ctk.CTkFrame(
          self.scroll_frame,
          fg_color=bg_color,
          border_color=borde_color,
          border_width=1,
          corner_radius=8,
      )
      row_frame.pack(fill="x", padx=5, pady=6)
      row_frame.grid_columnconfigure(0, weight=1)

      advertencia = " ⚠ [CRÍTICO]" if es_critico else ""
      texto_info = (
          f"{item['nombre']}  |  Cantidad: {item['cantidad']}"
          f" {item.get('unidad', '')}  |  Mínimo:"
          f" {item['stock_minimo']}{advertencia}"
      )

      color_texto = "#fca5a5" if es_critico else "#f1f5f9"
      lbl = ctk.CTkLabel(
          row_frame,
          text=texto_info,
          text_color=color_texto,
          font=ctk.CTkFont(
              size=13, weight="bold" if es_critico else "normal"
          ),
      )
      lbl.pack(side="left", padx=15, pady=12)

      btn_eliminar = ctk.CTkButton(
          row_frame,
          text="🗑️",
          width=40,
          fg_color="#dc2626",
          hover_color="#b91c1c",
          command=lambda i=item: self.eliminar_elemento(i["id"]),
      )
      btn_eliminar.pack(side="right", padx=5, pady=10)

      btn_editar = ctk.CTkButton(
          row_frame,
          text="✏ Editar",
          width=70,
          fg_color="#334155",
          hover_color="#475569",
          command=lambda i=item: self.abrir_modal_editar(i),
      )
      btn_editar.pack(side="right", padx=5, pady=10)

      btn_mas = ctk.CTkButton(
          row_frame,
          text="+",
          width=35,
          fg_color="#059669",
          hover_color="#047857",
          command=lambda i=item: self.cambiar_stock(i, 1),
      )
      btn_mas.pack(side="right", padx=2, pady=10)

      btn_menos = ctk.CTkButton(
          row_frame,
          text="-",
          width=35,
          fg_color="#dc2626",
          hover_color="#b91c1c",
          command=lambda i=item: self.cambiar_stock(i, -1),
      )
      btn_menos.pack(side="right", padx=5, pady=10)

  def cambiar_stock(self, item, cambio):
    nueva_cantidad = max(0, item["cantidad"] + cambio)
    try:
      supabase.table("inventario").update({"cantidad": nueva_cantidad}).eq(
          "id", item["id"]
      ).execute()
      self.cargar_datos()
    except Exception as e:
      print(f"Error actualizando stock: {e}")

  def eliminar_elemento(self, id_item):
    try:
      supabase.table("inventario").delete().eq("id", id_item).execute()
      self.cargar_datos()
    except Exception as e:
      print(f"Error al eliminar elemento: {e}")

  def abrir_modal_crear(self):
    ModalElemento(self, "Agregar Nuevo Elemento", self.guardar_nuevo_elemento)

  def abrir_modal_editar(self, item):
    ModalElemento(
        self,
        "Editar Elemento",
        lambda datos: self.actualizar_elemento(item["id"], datos),
        item_inicial=item,
    )

  def abrir_modal_busqueda_movimientos(self):
    ModalBusquedaMovimientos(
        self, self.datos_actuales, self.ejecutar_movimiento_masivo
    )

  def abrir_modal_salida_campo(self):
    ModalSalidaCampo(self)

  def abrir_modal_admin_salidas(self):
    ModalAdminSalidas(self)

  def guardar_nuevo_elemento(self, datos):
    try:
      supabase.table("inventario").insert(datos).execute()
      self.cargar_datos()
    except Exception as e:
      print(f"Error al crear elemento: {e}")

  def actualizar_elemento(self, id_item, datos):
    try:
      supabase.table("inventario").update(datos).eq("id", id_item).execute()
      self.cargar_datos()
    except Exception as e:
      print(f"Error al actualizar elemento: {e}")

  def ejecutar_movimiento_masivo(self, id_item, nueva_cantidad):
    try:
      supabase.table("inventario").update({"cantidad": nueva_cantidad}).eq(
          "id", id_item
      ).execute()
      self.cargar_datos()
    except Exception as e:
      print(f"Error en movimiento masivo: {e}")


class ModalElemento(ctk.CTkToplevel):

  def __init__(self, parent, titulo, callback_guardar, item_inicial=None):
    super().__init__(parent)
    self.titulo = titulo
    self.callback_guardar = callback_guardar
    self.item_inicial = item_inicial

    self.title(titulo)
    self.geometry("380x420")
    self.resizable(False, False)
    self.grab_set()

    ctk.CTkLabel(
        self, text=titulo, font=ctk.CTkFont(size=18, weight="bold")
    ).pack(pady=(20, 15))

    ctk.CTkLabel(self, text="Nombre del elemento:", anchor="w").pack(
        fill="x", padx=30
    )
    self.entry_nombre = ctk.CTkEntry(
        self, width=320, placeholder_text="Ej: Guantes de látex"
    )
    self.entry_nombre.pack(pady=(0, 10))

    ctk.CTkLabel(self, text="Cantidad actual:", anchor="w").pack(
        fill="x", padx=30
    )
    self.entry_cantidad = ctk.CTkEntry(
        self, width=320, placeholder_text="Ej: 25"
    )
    self.entry_cantidad.pack(pady=(0, 10))

    ctk.CTkLabel(self, text="Stock Mínimo (Alerta de escasez):", anchor="w").pack(
        fill="x", padx=30
    )
    self.entry_minimo = ctk.CTkEntry(
        self, width=320, placeholder_text="Ej: 5"
    )
    self.entry_minimo.pack(pady=(0, 10))

    ctk.CTkLabel(self, text="Unidad de medida (opcional):", anchor="w").pack(
        fill="x", padx=30
    )
    self.entry_unidad = ctk.CTkEntry(
        self, width=320, placeholder_text="Ej: unidades, ml, gramos"
    )
    self.entry_unidad.pack(pady=(0, 20))

    if self.item_inicial:
      self.entry_nombre.insert(0, str(self.item_inicial.get("nombre", "")))
      self.entry_cantidad.insert(0, str(self.item_inicial.get("cantidad", "")))
      self.entry_minimo.insert(0, str(self.item_inicial.get("stock_minimo", "")))
      self.entry_unidad.insert(0, str(self.item_inicial.get("unidad", "")))

    btn_guardar = ctk.CTkButton(
        self,
        text="Guardar",
        fg_color="#059669",
        hover_color="#047857",
        command=self.procesar_guardado,
    )
    btn_guardar.pack(pady=10)

  def procesar_guardado(self):
    nombre = self.entry_nombre.get().strip()
    cantidad_str = self.entry_cantidad.get().strip()
    minimo_str = self.entry_minimo.get().strip()
    unidad = self.entry_unidad.get().strip()

    if not nombre or not cantidad_str or not minimo_str:
      print("Error: Rellena los campos obligatorios.")
      return

    try:
      datos = {
          "nombre": nombre,
          "cantidad": int(cantidad_str),
          "stock_minimo": int(minimo_str),
          "unidad": unidad if unidad else None,
      }
      self.callback_guardar(datos)
      self.destroy()
    except ValueError:
      print("Error: Cantidad y Stock Mínimo deben ser números enteros.")


class PopUpCalendario(ctk.CTkToplevel):
  """Ventana emergente tipo calendario para seleccionar la fecha con un clic"""

  def __init__(self, parent, entry_destino):
    super().__init__(parent)
    self.entry_destino = entry_destino
    self.title("Seleccionar Fecha")
    self.geometry("280x320")
    self.resizable(False, False)
    self.grab_set()

    self.fecha_actual = datetime.now()
    self.anio = self.fecha_actual.year
    self.mes = self.fecha_actual.month

    self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
    self.header_frame.pack(fill="x", padx=10, pady=10)

    self.btn_anterior = ctk.CTkButton(
        self.header_frame, text="◀", width=30, command=self.mes_anterior
    )
    self.btn_anterior.pack(side="left")

    self.lbl_mes_anio = ctk.CTkLabel(
        self.header_frame, text="", font=ctk.CTkFont(weight="bold")
    )
    self.lbl_mes_anio.pack(side="left", expand=True)

    self.btn_siguiente = ctk.CTkButton(
        self.header_frame, text="▶", width=30, command=self.mes_siguiente
    )
    self.btn_siguiente.pack(side="right")

    self.calendar_frame = ctk.CTkFrame(self)
    self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    self.actualizar_calendario()

  def actualizar_calendario(self):
    for widget in self.calendar_frame.winfo_children():
      widget.destroy()

    import calendar

    nombres_meses = [
        "",
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    self.lbl_mes_anio.configure(text=f"{nombres_meses[self.mes]} {self.anio}")

    dias_semana = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]
    for i, d in enumerate(dias_semana):
      lbl = ctk.CTkLabel(
          self.calendar_frame,
          text=d,
          font=ctk.CTkFont(size=11, weight="bold"),
      )
      lbl.grid(row=0, column=i, padx=2, pady=2)

    cal = calendar.monthcalendar(self.anio, self.mes)
    for fila_idx, semana in enumerate(cal):
      for col_idx, dia in enumerate(semana):
        if dia != 0:
          btn = ctk.CTkButton(
              self.calendar_frame,
              text=str(dia),
              width=32,
              height=32,
              fg_color="#334155",
              hover_color="#475569",
              command=lambda d=dia: self.seleccionar_dia(d),
          )
          btn.grid(row=fila_idx + 1, column=col_idx, padx=2, pady=2)

  def mes_anterior(self):
    self.mes -= 1
    if self.mes < 1:
      self.mes = 12
      self.anio -= 1
    self.actualizar_calendario()

  def mes_siguiente(self):
    self.mes += 1
    if self.mes > 12:
      self.mes = 1
      self.anio += 1
    self.actualizar_calendario()

  def seleccionar_dia(self, dia):
    fecha_str = f"{self.anio}-{self.mes:02d}-{dia:02d}"
    self.entry_destino.delete(0, "end")
    self.entry_destino.insert(0, fecha_str)
    self.destroy()


class PopUpSelectorRuedaHora(ctk.CTkToplevel):
  """Selector de hora estilo rueda deslizante (inspirado en iOS)"""

  def __init__(self, parent, entry_destino):
    super().__init__(parent)
    self.entry_destino = entry_destino
    self.title("Seleccionar Hora")
    self.geometry("320x340")
    self.resizable(False, False)
    self.grab_set()

    # Listas de valores para la rueda
    self.horas = [str(i) for i in range(1, 13)]  # 1 a 12
    self.minutos = [
        "00",
        "05",
        "10",
        "15",
        "20",
        "25",
        "30",
        "35",
        "40",
        "45",
        "50",
        "55",
    ]
    self.ampm_list = ["AM", "PM"]

    self.idx_h = 10
    self.idx_m = 0
    self.idx_ap = 0

    ctk.CTkLabel(
        self,
        text="Selecciona la Hora",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(pady=(15, 10))

    rueda_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=10)
    rueda_frame.pack(pady=5, padx=20, fill="x")

    # Columna Horas
    col_h = ctk.CTkFrame(rueda_frame, fg_color="transparent")
    col_h.pack(side="left", expand=True, padx=5, pady=10)
    ctk.CTkButton(
        col_h,
        text="▲",
        width=40,
        height=24,
        fg_color="#334155",
        command=lambda: self.cambiar_valor("h", -1),
    ).pack(pady=2)
    self.lbl_h = ctk.CTkLabel(
        col_h,
        text=self.horas[self.idx_h],
        font=ctk.CTkFont(size=26, weight="bold"),
        width=60,
    )
    self.lbl_h.pack(pady=5)
    ctk.CTkButton(
        col_h,
        text="▼",
        width=40,
        height=24,
        fg_color="#334155",
        command=lambda: self.cambiar_valor("h", 1),
    ).pack(pady=2)

    ctk.CTkLabel(
        rueda_frame, text=":", font=ctk.CTkFont(size=26, weight="bold")
    ).pack(side="left", padx=2)

    # Columna Minutos
    col_m = ctk.CTkFrame(rueda_frame, fg_color="transparent")
    col_m.pack(side="left", expand=True, padx=5, pady=10)
    ctk.CTkButton(
        col_m,
        text="▲",
        width=40,
        height=24,
        fg_color="#334155",
        command=lambda: self.cambiar_valor("m", -1),
    ).pack(pady=2)
    self.lbl_m = ctk.CTkLabel(
        col_m,
        text=self.minutos[self.idx_m],
        font=ctk.CTkFont(size=26, weight="bold"),
        width=60,
    )
    self.lbl_m.pack(pady=5)
    ctk.CTkButton(
        col_m,
        text="▼",
        width=40,
        height=24,
        fg_color="#334155",
        command=lambda: self.cambiar_valor("m", 1),
    ).pack(pady=2)

    # Columna AM/PM
    col_ap = ctk.CTkFrame(rueda_frame, fg_color="transparent")
    col_ap.pack(side="left", expand=True, padx=5, pady=10)
    ctk.CTkButton(
        col_ap,
        text="▲",
        width=40,
        height=24,
        fg_color="#334155",
        command=lambda: self.cambiar_valor("ap", -1),
    ).pack(pady=2)
    self.lbl_ap = ctk.CTkLabel(
        col_ap,
        text=self.ampm_list[self.idx_ap],
        font=ctk.CTkFont(size=22, weight="bold"),
        width=60,
    )
    self.lbl_ap.pack(pady=8)
    ctk.CTkButton(
        col_ap,
        text="▼",
        width=40,
        height=24,
        fg_color="#334155",
        command=lambda: self.cambiar_valor("ap", 1),
    ).pack(pady=2)

    btn_listo = ctk.CTkButton(
        self,
        text="Listo",
        fg_color="#059669",
        hover_color="#047857",
        font=ctk.CTkFont(size=14, weight="bold"),
        command=self.confirmar_hora,
    )
    btn_listo.pack(pady=20, fill="x", padx=40)

  def cambiar_valor(self, campo, direccion):
    if campo == "h":
      self.idx_h = (self.idx_h + direccion) % len(self.horas)
      self.lbl_h.configure(text=self.horas[self.idx_h])
    elif campo == "m":
      self.idx_m = (self.idx_m + direccion) % len(self.minutos)
      self.lbl_m.configure(text=self.minutos[self.idx_m])
    elif campo == "ap":
      self.idx_ap = (self.idx_ap + direccion) % len(self.ampm_list)
      self.lbl_ap.configure(text=self.ampm_list[self.idx_ap])

  def confirmar_hora(self):
    h = int(self.horas[self.idx_h])
    m = self.minutos[self.idx_m]
    ap = self.ampm_list[self.idx_ap]

    if ap == "PM" and h < 12:
      h += 12
    elif ap == "AM" and h == 12:
      h = 0

    hora_24h = f"{h:02d}:{m}"

    self.entry_destino.delete(0, "end")
    self.entry_destino.insert(0, hora_24h)
    self.destroy()


class ModalSalidaCampo(ctk.CTkToplevel):

  def __init__(self, parent):
    super().__init__(parent)
    self.title("Registrar Salida de Campo - MVZ")
    self.geometry("420x460")
    self.resizable(False, False)
    self.grab_set()

    ctk.CTkLabel(
        self,
        text="Nueva Salida Práctica",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(pady=(15, 10))

    ctk.CTkLabel(self, text="Materia / Asignatura:", anchor="w").pack(
        fill="x", padx=30
    )
    self.entry_materia = ctk.CTkEntry(
        self, width=360, placeholder_text="Ej: Cirugía de Grandes Animales"
    )
    self.entry_materia.pack(pady=(0, 8))

    ctk.CTkLabel(
        self, text="Fecha (Haz clic para abrir el calendario):", anchor="w"
    ).pack(fill="x", padx=30)
    self.entry_fecha = ctk.CTkEntry(
        self, width=360, placeholder_text="YYYY-MM-DD"
    )
    self.entry_fecha.pack(pady=(0, 8))
    self.entry_fecha.bind(
        "<Button-1>", lambda e: PopUpCalendario(self, self.entry_fecha)
    )

    ctk.CTkLabel(
        self, text="Hora (Haz clic para abrir el selector de rueda):", anchor="w"
    ).pack(fill="x", padx=30)
    self.entry_hora = ctk.CTkEntry(self, width=360, placeholder_text="HH:MM")
    self.entry_hora.pack(pady=(0, 8))
    self.entry_hora.bind(
        "<Button-1>", lambda e: PopUpSelectorRuedaHora(self, self.entry_hora)
    )

    ctk.CTkLabel(self, text="Lugar:", anchor="w").pack(fill="x", padx=30)
    self.entry_lugar = ctk.CTkEntry(
        self, width=360, placeholder_text="Ej: Finca Experimental La Rivera"
    )
    self.entry_lugar.pack(pady=(0, 8))

    ctk.CTkLabel(self, text="¿Qué hay que llevar?:", anchor="w").pack(
        fill="x", padx=30
    )
    self.text_requerimientos = ctk.CTkTextbox(self, width=360, height=50)
    self.text_requerimientos.pack(pady=(0, 15))

    btn_guardar = ctk.CTkButton(
        self,
        text="Guardar y Sincronizar en Web",
        fg_color="#d97706",
        hover_color="#b45309",
        command=self.guardar_salida_db,
    )
    btn_guardar.pack(pady=5)

  def guardar_salida_db(self):
    materia = self.entry_materia.get().strip()
    fecha_texto = self.entry_fecha.get().strip()
    hora = self.entry_hora.get().strip()
    lugar = self.entry_lugar.get().strip()
    requerimientos = self.text_requerimientos.get("1.0", "end-1c").strip()

    if not materia or not fecha_texto or not hora:
      print("Error: Materia, Fecha y Hora son obligatorias.")
      return

    try:
      fecha_formateada = datetime.strptime(
          fecha_texto, "%Y-%m-%d"
      ).strftime("%Y-%m-%d")
    except Exception:
      print("Error: Formato de fecha inválido. Usa el calendario.")
      return

    try:
      data = {
          "materia": materia,
          "fecha": fecha_formateada,
          "hora": hora,
          "lugar": lugar,
          "requerimientos": requerimientos,
      }
      supabase.table("salidas_campo").insert(data).execute()
      print("¡Salida registrada con éxito!")
      self.destroy()
    except Exception as e:
      print(f"Error al guardar salida de campo: {e}")


class ModalAdminSalidas(ctk.CTkToplevel):

  def __init__(self, parent):
    super().__init__(parent)
    self.title("Administrar Salidas de Campo - MVZ")
    self.geometry("700x550")
    self.minsize(600, 450)
    self.resizable(True, True)  # VENTANA AJUSTABLE HABILITADA
    self.grab_set()

    self.todas_las_salidas = []

    # Configuración del grid principal de la ventana para expandirse
    self.grid_rowconfigure(2, weight=1)
    self.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        self,
        text="Listado de Salidas Programadas",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).grid(row=0, column=0, pady=(15, 8), padx=20, sticky="w")

    self.search_salidas_var = ctk.StringVar()
    self.search_salidas_var.trace_add("write", self.filtrar_salidas_en_vivo)

    self.entry_busqueda_salidas = ctk.CTkEntry(
        self,
        placeholder_text=(
            "🔍 Buscar salida por materia, lugar o fecha (ej: cirugia...)"
        ),
        textvariable=self.search_salidas_var,
        height=35,
        font=ctk.CTkFont(size=12),
    )
    self.entry_busqueda_salidas.grid(
        row=1, column=0, padx=20, pady=(0, 10), sticky="ew"
    )

    self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
    self.scroll_frame.grid(
        row=2, column=0, padx=20, pady=(0, 15), sticky="nsew"
    )
    self.scroll_frame.grid_columnconfigure(0, weight=1)

    self.cargar_salidas()

  def cargar_salidas(self):
    try:
      response = (
          supabase.table("salidas_campo").select("*").order("fecha").execute()
      )
      self.todas_las_salidas = response.data
      self.filtrar_salidas_en_vivo()
    except Exception as e:
      print(f"Error cargando salidas para administrar: {e}")

  def filtrar_salidas_en_vivo(self, *args):
    texto = self.search_salidas_var.get().lower().strip()

    if not texto:
      salidas_filtradas = self.todas_las_salidas
    else:
      salidas_filtradas = [
          s
          for s in self.todas_las_salidas
          if texto in s.get("materia", "").lower()
          or texto in s.get("lugar", "").lower()
          or texto in str(s.get("fecha", ""))
      ]

    self.actualizar_lista_visual_salidas(salidas_filtradas)

  def actualizar_lista_visual_salidas(self, salidas):
    for widget in self.scroll_frame.winfo_children():
      widget.destroy()

    if not salidas:
      ctk.CTkLabel(
          self.scroll_frame,
          text="No se encontraron salidas compatibles.",
          text_color="gray",
      ).pack(pady=30)
      return

    for salida in salidas:
      card = ctk.CTkFrame(
          self.scroll_frame, fg_color="#1e293b", corner_radius=6
      )
      card.pack(fill="x", padx=5, pady=6)
      
      # Distribución en Grid para asegurar que los botones sean fijos a la derecha
      card.grid_columnconfigure(0, weight=1)
      card.grid_columnconfigure(1, weight=0)

      info_txt = f"📅 {salida['fecha']} | ⏰ {salida['hora']} - {salida['materia']} ({salida.get('lugar', 'Sin lugar')})"
      
      lbl = ctk.CTkLabel(
          card,
          text=info_txt,
          font=ctk.CTkFont(size=12, weight="bold"),
          text_color="#f1f5f9",
          anchor="w",
          justify="left",
          wraplength=450,  # Salto de línea automático para textos muy largos
      )
      lbl.grid(row=0, column=0, sticky="ew", padx=12, pady=12)

      # Contenedor para mantener los botones fijos y ordenados a la derecha
      btn_frame = ctk.CTkFrame(card, fg_color="transparent")
      btn_frame.grid(row=0, column=1, padx=10, pady=8, sticky="e")

      btn_editar = ctk.CTkButton(
          btn_frame,
          text="✏️ Editar",
          width=70,
          height=30,
          fg_color="#334155",
          hover_color="#475569",
          command=lambda s=salida: self.abrir_modal_editar_salida(s),
      )
      btn_editar.pack(side="left", padx=2)

      btn_eliminar = ctk.CTkButton(
          btn_frame,
          text="🗑️",
          width=36,
          height=30,
          fg_color="#dc2626",
          hover_color="#b91c1c",
          command=lambda s=salida: self.eliminar_salida(s["id"]),
      )
      btn_eliminar.pack(side="left", padx=2)

  def eliminar_salida(self, id_salida):
    try:
      supabase.table("salidas_campo").delete().eq("id", id_salida).execute()
      self.cargar_salidas()
    except Exception as e:
      print(f"Error al eliminar salida: {e}")

  def abrir_modal_editar_salida(self, salida):
    ModalEditarSalidaIndividual(self, salida, self.cargar_salidas)


class ModalEditarSalidaIndividual(ctk.CTkToplevel):

  def __init__(self, parent, salida, callback_actualizado):
    super().__init__(parent)
    self.salida = salida
    self.callback_actualizado = callback_actualizado

    self.title(f"Editar: {salida['materia']}")
    self.geometry("420x460")
    self.resizable(False, False)
    self.grab_set()

    ctk.CTkLabel(
        self,
        text="Modificar Salida Práctica",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(pady=(15, 10))

    ctk.CTkLabel(self, text="Materia / Asignatura:", anchor="w").pack(
        fill="x", padx=30
    )
    self.entry_materia = ctk.CTkEntry(self, width=360)
    self.entry_materia.pack(pady=(0, 8))
    self.entry_materia.insert(0, salida.get("materia", ""))

    ctk.CTkLabel(self, text="Fecha:", anchor="w").pack(fill="x", padx=30)
    self.entry_fecha = ctk.CTkEntry(self, width=360)
    self.entry_fecha.pack(pady=(0, 8))
    self.entry_fecha.insert(0, str(salida.get("fecha", "")))
    self.entry_fecha.bind(
        "<Button-1>", lambda e: PopUpCalendario(self, self.entry_fecha)
    )

    ctk.CTkLabel(self, text="Hora:", anchor="w").pack(fill="x", padx=30)
    self.entry_hora = ctk.CTkEntry(self, width=360)
    self.entry_hora.pack(pady=(0, 8))
    self.entry_hora.insert(0, str(salida.get("hora", "")))
    self.entry_hora.bind(
        "<Button-1>", lambda e: PopUpSelectorRuedaHora(self, self.entry_hora)
    )

    ctk.CTkLabel(self, text="Lugar:", anchor="w").pack(fill="x", padx=30)
    self.entry_lugar = ctk.CTkEntry(self, width=360)
    self.entry_lugar.pack(pady=(0, 8))
    self.entry_lugar.insert(0, str(salida.get("lugar", "") or ""))

    ctk.CTkLabel(self, text="¿Qué hay que llevar?:", anchor="w").pack(
        fill="x", padx=30
    )
    self.text_requerimientos = ctk.CTkTextbox(self, width=360, height=50)
    self.text_requerimientos.pack(pady=(0, 15))
    self.text_requerimientos.insert(
        "1.0", str(salida.get("requerimientos", "") or "")
    )

    btn_guardar = ctk.CTkButton(
        self,
        text="Actualizar Cambios",
        fg_color="#059669",
        hover_color="#047857",
        command=self.guardar_cambios_db,
    )
    btn_guardar.pack(pady=5)

  def guardar_cambios_db(self):
    materia = self.entry_materia.get().strip()
    fecha_texto = self.entry_fecha.get().strip()
    hora = self.entry_hora.get().strip()
    lugar = self.entry_lugar.get().strip()
    requerimientos = self.text_requerimientos.get("1.0", "end-1c").strip()

    if not materia or not fecha_texto or not hora:
      print("Error: Materia, Fecha y Hora son obligatorias.")
      return

    try:
      fecha_formateada = datetime.strptime(
          fecha_texto, "%Y-%m-%d"
      ).strftime("%Y-%m-%d")
    except Exception:
      print("Error: Formato de fecha no válido.")
      return

    try:
      data = {
          "materia": materia,
          "fecha": fecha_formateada,
          "hora": hora,
          "lugar": lugar,
          "requerimientos": requerimientos,
      }
      supabase.table("salidas_campo").update(data).eq(
          "id", self.salida["id"]
      ).execute()
      print("¡Salida actualizada con éxito!")
      self.callback_actualizado()
      self.destroy()
    except Exception as e:
      print(f"Error al actualizar salida de campo: {e}")


class ModalBusquedaMovimientos(ctk.CTkToplevel):

  def __init__(self, parent, lista_items, callback_movimiento):
    super().__init__(parent)
    self.lista_items = lista_items
    self.callback_movimiento = callback_movimiento

    self.title("Búsqueda y Movimientos Rápidos")
    self.geometry("600x500")
    self.resizable(False, False)
    self.grab_set()

    ctk.CTkLabel(
        self,
        text="Gestión Rápida de Stock por Búsqueda",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(pady=(15, 10))

    self.search_var = ctk.StringVar()
    self.search_var.trace_add("write", self.filtrar_resultados)

    self.entry_buscar = ctk.CTkEntry(
        self,
        placeholder_text=(
            "🔍 Escribe para buscar un elemento (ej: jeringa, alcohol...)"
        ),
        textvariable=self.search_var,
        width=540,
        height=38,
        font=ctk.CTkFont(size=13),
    )
    self.entry_buscar.pack(pady=(0, 10))

    self.scroll_resultados = ctk.CTkScrollableFrame(
        self, width=540, height=340, corner_radius=8
    )
    self.scroll_resultados.pack(pady=(0, 15), padx=20)
    self.scroll_resultados.grid_columnconfigure(0, weight=1)

    self.actualizar_lista_resultados(self.lista_items)

  def filtrar_resultados(self, *args):
    texto = self.search_var.get().lower().strip()
    if not texto:
      filtrados = self.lista_items
    else:
      filtrados = [
          item
          for item in self.lista_items
          if texto in item["nombre"].lower()
      ]
    self.actualizar_lista_resultados(filtrados)

  def actualizar_lista_resultados(self, items):
    for widget in self.scroll_resultados.winfo_children():
      widget.destroy()

    if not items:
      ctk.CTkLabel(
          self.scroll_resultados,
          text="No se encontraron coincidencias",
          text_color="gray",
      ).pack(pady=20)
      return

    for item in items:
      card = ctk.CTkFrame(
          self.scroll_resultados, fg_color="#1e293b", corner_radius=6
      )
      card.pack(fill="x", padx=5, pady=4)
      card.grid_columnconfigure(0, weight=1)

      info_txt = (
          f"{item['nombre']}  (Stock actual: {item['cantidad']}"
          f" {item.get('unidad', '')})"
      )
      ctk.CTkLabel(
          card,
          text=info_txt,
          font=ctk.CTkFont(size=12, weight="bold"),
          text_color="#f1f5f9",
      ).pack(side="left", padx=12, pady=10)

      btn_ajustar = ctk.CTkButton(
          card,
          text="Ajustar Cantidad ➕➖",
          width=130,
          height=30,
          fg_color="#0284c7",
          hover_color="#0369a1",
          command=lambda i=item: self.pedir_cantidad_movimiento(i),
      )
      btn_ajustar.pack(side="right", padx=10, pady=6)

  def pedir_cantidad_movimiento(self, item):
    dialogo = ctk.CTkToplevel(self)
    dialogo.title(f"Ajustar: {item['nombre']}")
    dialogo.geometry("320x240")
    dialogo.resizable(False, False)
    dialogo.grab_set()

    ctk.CTkLabel(
        dialogo, text=item["nombre"], font=ctk.CTkFont(size=14, weight="bold")
    ).pack(pady=(15, 5))
    ctk.CTkLabel(
        dialogo,
        text=f"Actual: {item['cantidad']} {item.get('unidad', '')}",
        text_color="#94a3b8",
    ).pack(pady=(0, 10))

    ctk.CTkLabel(
        dialogo,
        text="Cantidad a sumar (+) o restar (-):",
        font=ctk.CTkFont(size=11),
    ).pack()
    entry_cant = ctk.CTkEntry(dialogo, width=200, placeholder_text="Ej: 50 o -15")
    entry_cant.pack(pady=8)
    entry_cant.focus()

    def confirmar_cambio():
      try:
        valor = int(entry_cant.get().strip())
        nueva_cantidad = max(0, item["cantidad"] + valor)

        self.callback_movimiento(item["id"], nueva_cantidad)
        item["cantidad"] = nueva_cantidad
        self.filtrar_resultados()

        dialogo.destroy()
      except ValueError:
        print("Error: Ingresa un número entero válido.")

    btn_ok = ctk.CTkButton(
        dialogo,
        text="Aplicar Movimiento",
        fg_color="#059669",
        hover_color="#047857",
        command=confirmar_cambio,
    )
    btn_ok.pack(pady=10)


if __name__ == "__main__":
  app = InventarioApp()
  app.mainloop()