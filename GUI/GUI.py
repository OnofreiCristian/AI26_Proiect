import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk
import queue
import threading
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CelLabGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        #1. configuram titlul si dimensiunea ferestrei principale
        self.title("CelLab - Simulation GUI")
        self.geometry("900x600")

        #2. configuram sistemul de grid al ferestrei
        #vrem ca coloana 1(cea cu canvasul) sa se extinda cand marim fereastra
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)


        # 3. cream un panou in stanga (sidebar-ul)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)

        # dam un titlu in sidebar
        self.lbl_title = ctk.CTkLabel(self.sidebar, text="Controale", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_title.pack(padx=10, pady=10)


        #adauga doua butoane ctk.CTkButton in sidebard start si pause
        self.btn_start = ctk.CTkButton(self.sidebar, text="Start", command=self.start_simulation)
        self.btn_start.pack(padx=10, pady=10) 
        
        self.btn_pause = ctk.CTkButton(self.sidebar, text="Pause", command=self.pause_simulation)
        self.btn_pause.pack(padx=10, pady=10)

        #4. cream zona pentru canvas in dreapta
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        #creaaza un obiect ctk.Canvas in interiorul self.Canvas_frame
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)


        # Desenat pe canvas folosind o matrice NumPy

        #Atribut pentru a retine referinta imaginii desenate pe canvas
        self.image_on_canvas = None

        #Generam o matrice aleatoare de 100x100 cu valori 0 si 1, unde 0 reprezinta celule moarte si 1 celule vii 
        test_grid = np.random.choice([0,1], (100, 100), p=[0.8, 0.2])

        # randeaza matricea de test pe canvas folosind metoda update_canvas
        self.update_canvas(test_grid)


        # State variables si coada pentru cadre
        self.is_running = False
        self.world_size = (100, 100)  # Dimensiunea lumii de simulare
        self.frame_queue = queue.Queue(maxsize=5) # Coada pentru a stoca cadrele de simulare

        # Pornim verificarea periodica a cozii la initializarea GUI-ului
        self.poll_queue()

    def update_canvas(self, grid_matrix: np.ndarray):
        #1. transofmam matricile 0 si 1 in valori 0 si 255 (uint8 pentru pixelii imaginii)
        img_data = (grid_matrix * 255).astype(np.uint8)

        # cream o imagine PIL din matricea de pixeli
        img = Image.fromarray(img_data)

        #preluam dimensiunile curente ale canvasului
        canvas_width = max(self.canvas.winfo_width(), 500)
        canvas_height = max(self.canvas.winfo_height(), 500)

        # Redimensioneaza imaginea la canvas_width si canvas_height folosind Image.Resampling.NEAREST
        img = img.resize((canvas_width, canvas_height), Image.Resampling.NEAREST)

        #convertesc img intr un obiect ImageTk.PhotoImage si salveazal intr un atribut al clasei pentru a preveni garbage collection
        self.tk_image = ImageTk.PhotoImage(img)

        # afisam si actualizam imaginea pe canvas
        if self.image_on_canvas is None:
            self.image_on_canvas = self.canvas.create_image(
                0, 0, image=self.tk_image, anchor="nw")
        else:
            self.canvas.itemconfig(self.image_on_canvas, image=self.tk_image)

    #thread simulare
    def sim_worker(self):
        """Ruleaza in fundal un loop care genereaza cadre de simulare si le pune in coada pentru a fi procesate de GUI."""
        #starea initiala dummy (matrice aleatoare)
        current_grid = np.random.choice([0, 1], size=self.world_size, p=[0.8, 0.2])

        while self.is_running:
            #aici se va apela pasul de logica al simulatiei (de exemplu, Game of Life) pentru a genera urmatorul cadru
            # pentru demo, generam un nou cadru aleator
            current_grid = np.random.choice(
                [0, 1], size=self.world_size, p=[0.8, 0.2]
                )

            # punem cadrul in coada doar daca nu este plina (pentru a evita acumularea de cadre vechi)
            if not self.frame_queue.full():
                self.frame_queue.put(current_grid)

            time.sleep(0.05)  # Simuleaza timpul de procesare al simulatiei, aici 20 FPS

    def start_simulation(self):
        """Porneste thread-ul de simulare si seteaza is_running la True."""
        if not self.is_running:
            self.is_running = True
            #cream un thread daemon ca sa se inchida automat cand inchidem GUI-ul
            threading.Thread(target=self.sim_worker, daemon=True).start()

    def pause_simulation(self):
        """Opreste thread-ul de simulare si seteaza is_running la False."""
        self.is_running = False

    def poll_queue(self):
        """Rulata pe thread-ul principal al GUI-ului, verifica coada pentru cadre noi si actualizeaza canvasul daca exista."""
        try:
            while not self.frame_queue.empty():
                grid = self.frame_queue.get_nowait()
                self.current_grid = grid
                self.update_canvas(grid)
        except queue.Empty:
            pass

        #re-programam functia sa ruleze din nou dupa 20ms
        self.after(20, self.poll_queue)

if __name__ == "__main__":
    app = CelLabGUI()
    app.mainloop()