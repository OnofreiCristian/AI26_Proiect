import os
import sys
from pathlib import Path

# Ensure project root is in sys.path and is the current working directory
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import customtkinter as ctk
import numpy as np
import re
from PIL import Image, ImageTk
import queue
import threading
import time

from Automata.Sandpile import SandpileAutomata
from Automata.PredatorPrey import PredatorPreyAutomata

AUTOMATA_REGISTRY = {
    "Sandpile Model": SandpileAutomata,
    "Predator-Prey": PredatorPreyAutomata,
}

PREDATOR_PREY_PALETTE = np.array([
    [255, 255, 255],  # 0: Empty
    [46, 204, 113],   # 1: Rabbit
    [231, 76, 60],    # 2: Fox
], dtype=np.uint8)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CelLabGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. configuram titlul si dimensiunea ferestrei principale
        self.title("CelLab - Simulation GUI")
        self.geometry("900x600")

        # 2. configuram sistemul de grid al ferestrei
        # vrem ca coloana 1(cea cu canvasul) sa se extinda cand marim fereastra
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 3. cream un panou in stanga (sidebar-ul)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)

        # dam un titlu in sidebar
        self.lbl_title = ctk.CTkLabel(self.sidebar, text="Controls", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_title.pack(padx=10, pady=10)

        # selectie automat (Sandpile / Predator-Prey)
        self.automata_selector = ctk.CTkOptionMenu(
            self.sidebar,
            values=list(AUTOMATA_REGISTRY.keys()),
            command=self.change_automaton
        )
        self.automata_selector.pack(padx=10, pady=10)

        # adauga butoane ctk.CTkButton in sidebar start si pause
        self.btn_start = ctk.CTkButton(self.sidebar, text="Start", command=self.start_simulation)
        self.btn_start.pack(padx=10, pady=10) 
        
        self.btn_pause = ctk.CTkButton(self.sidebar, text="Pause", command=self.pause_simulation)
        self.btn_pause.pack(padx=10, pady=10)

        self.btn_dim = ctk.CTkButton(self.sidebar, text="Change dimensions", command=self.change_dimensions)
        self.btn_dim.pack(padx=10, pady=10)

        # 4. cream zona pentru canvas in dreapta
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # creeaza un obiect ctk.Canvas in interiorul self.canvas_frame
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # zona pentru text
        self.textbox = ctk.CTkEntry(self.canvas_frame, width=300, height=30)
        self.textbox.pack(padx=10, pady=10)

        # Desenat pe canvas folosind o matrice NumPy

        # Atribute pentru a retine referinta imaginii desenate pe canvas
        self.image_on_canvas = None
        self.tk_image = None
        self.automaton = None
        self.current_grid: np.ndarray | None = None

        # State variables si coada pentru cadre
        self.is_running = False
        self.world_size = (100, 100)  # Dimensiunea lumii de simulare
        self.frame_queue = queue.Queue(maxsize=5)  # Coada pentru a stoca cadrele de simulare

        # Initializare automat celular
        self.init_automaton()

        # Actualizam geometria ferestrei pentru a calcula dimensiunile reale ale canvasului
        self.update_idletasks()

        # randeaza matricea pe canvas folosind metoda update_canvas
        self.update_canvas(self.automaton.get_grid())

        # Redimensionam automat matricea pe canvas cand se modifica dimensiunea ferestrei
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Pornim verificarea periodica a cozii la initializarea GUI-ului
        self.poll_queue()

    def init_automaton(self, model_name=None):
        # Initializeaza modelul de automat celular selectat.
        if model_name is None:
            model_name = self.automata_selector.get()
        automata_cls = AUTOMATA_REGISTRY.get(model_name, SandpileAutomata)
        self.automaton = automata_cls(rows=self.world_size[0], cols=self.world_size[1])
        self.automaton.reset()
        self.current_grid = self.automaton.get_grid()

    def clear_queue(self):
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

    def change_automaton(self, choice: str):
        # schimba modelul cand se alege din dropdown
        self.pause_simulation()
        self.clear_queue()
        self.init_automaton(choice)
        self.update_canvas(self.automaton.get_grid())

    def on_canvas_resize(self, event=None):
        # Redeseneaza matricea la noile dimensiuni ale canvasului cand se redimensioneaza fereastra
        grid = self.current_grid
        if grid is None and self.automaton is not None:
            grid = self.automaton.get_grid()
        if isinstance(grid, np.ndarray):
            self.update_canvas(grid)

    def update_canvas(self, grid_matrix: np.ndarray):
        self.current_grid = grid_matrix

        if isinstance(self.automaton, SandpileAutomata):
            img = Image.fromarray((grid_matrix * 50).astype(np.uint8))
        else:
            safe_grid = np.clip(grid_matrix, 0, len(PREDATOR_PREY_PALETTE) - 1)
            img = Image.fromarray(PREDATOR_PREY_PALETTE[safe_grid], mode="RGB")

        # preluam dimensiunile curente ale canvasului
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 500
            canvas_height = 500

        # Redimensioneaza imaginea la canvas_width si canvas_height folosind Image.Resampling.NEAREST
        img = img.resize((canvas_width, canvas_height), Image.Resampling.NEAREST)

        # convertesc img intr un obiect ImageTk.PhotoImage si salveazal intr un atribut al clasei pentru a preveni garbage collection
        self.tk_image = ImageTk.PhotoImage(img)

        # afisam si actualizam imaginea pe canvas
        if self.image_on_canvas is None:
            self.image_on_canvas = self.canvas.create_image(
                0, 0, image=self.tk_image, anchor="nw")
        else:
            self.canvas.itemconfig(self.image_on_canvas, image=self.tk_image)

    # thread simulare
    def sim_worker(self):
        # Ruleaza in fundal un loop care apeleaza pasul de logica al simulatiei si pune cadrele in coada
        while self.is_running:
            self.automaton.step()
            next_grid = self.automaton.get_grid().copy()
            stable = getattr(self.automaton, "stable", False)

            # punem cadrul in coada doar daca nu este plina (pentru a evita acumularea de cadre vechi)
            if not self.frame_queue.full():
                self.frame_queue.put(next_grid)

            # Daca simularea a devenit stabila (in cazul Sandpile), oprim simularea
            if stable:
                self.is_running = False
                break

            time.sleep(0.05)  # Simuleaza timpul de procesare al simulatiei, aici 20 FPS

    def start_simulation(self):
        # Porneste thread-ul de simulare si seteaza is_running la True
        if not self.is_running:
            # Daca modelul este deja stabil, il resetam inainte de pornire
            if getattr(self.automaton, "stable", False):
                self.automaton.reset()
                self.update_canvas(self.automaton.get_grid())

            self.is_running = True
            # cream un thread daemon ca sa se inchida automat cand inchidem GUI-ul
            threading.Thread(target=self.sim_worker, daemon=True).start()

    def pause_simulation(self):
        # Opreste thread-ul de simulare si seteaza is_running la False
        self.is_running = False

    def change_dimensions(self):
        self.pause_simulation()
        self.clear_queue()
        input_text = self.textbox.get()
        dimensions = re.findall(r'\d+', input_text)
        if len(dimensions) == 2:
            self.world_size = (int(dimensions[0]), int(dimensions[1]))
        if len(dimensions) == 1:
            self.world_size = (int(dimensions[0]), int(dimensions[0]))
        self.init_automaton()
        self.update_canvas(self.automaton.get_grid())

    def poll_queue(self):
        # Rulata pe thread-ul principal al GUI-ului, verifica coada pentru cadre noi si actualizeaza canvasul daca exista
        try:
            while not self.frame_queue.empty():
                grid = self.frame_queue.get_nowait()
                self.current_grid = grid
                self.update_canvas(grid)
        except queue.Empty:
            pass

        # re-programam functia sa ruleze din nou dupa 20ms
        self.after(20, self.poll_queue)


if __name__ == "__main__":
    app = CelLabGUI()
    app.mainloop()
