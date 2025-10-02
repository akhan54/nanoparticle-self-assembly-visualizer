import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import numpy as np

class ParticleRenderer(QWidget):
    def __init__(self, simulation_engine):
        super().__init__()
        self.engine = simulation_engine
        
        layout = QVBoxLayout(self)
        
        # Create a figure with two subplots: one for the simulation, one for the RDF
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        # --- Ax1: Particle Plot Setup ---
        self.ax1.set_xlim(0, self.engine.box_size)
        self.ax1.set_ylim(0, self.engine.box_size)
        self.ax1.set_aspect('equal')
        self.ax1.set_title("Nanoparticle Self-Assembly")
        self.ax1.tick_params(left=False, right=False, labelleft=False,
                            labelbottom=False, bottom=False)
        self.particles_plot = self.ax1.scatter(self.engine.positions[:, 0], self.engine.positions[:, 1], s=50, c='blue')
        
        # --- Ax2: Radial Distribution Function (RDF) Plot Setup ---
        self.ax2.set_xlim(0, self.engine.box_size / 2)
        self.ax2.set_ylim(0, 4)
        self.ax2.set_title("Radial Distribution Function (g(r))")
        self.ax2.set_xlabel("Distance (r)")
        self.ax2.set_ylabel("g(r)")
        
        self.rdf_line, = self.ax2.plot([], [], 'r-')
        self.num_bins = 50
        
        # B) Exponential Moving Average (EMA) for RDF smoothing
        self.rdf_ema = None         # EMA buffer
        self.rdf_alpha = 0.2        # Smoothing factor (0-1, lower is smoother)
        
    
    def calculate_rdf(self):
        distances = []
        for i in range(self.engine.num_particles):
            for j in range(i + 1, self.engine.num_particles):
                r_vec = self.engine.positions[i] - self.engine.positions[j]
                r_vec -= self.engine.box_size * np.rint(r_vec / self.engine.box_size)
                r = np.linalg.norm(r_vec)
                distances.append(r)
        
        hist, bin_edges = np.histogram(distances, bins=self.num_bins, range=(0, self.engine.box_size / 2))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        dr = bin_edges[1] - bin_edges[0]
        rho = self.engine.num_particles / self.engine.box_size**2
        
        dr = bin_edges[1] - bin_edges[0]
        rho = self.engine.num_particles / self.engine.box_size**2
        
        # Calculate normalization factor for unique pairs (i<j) in 2D: N * rho * (pi * r * dr).
        # This is half the normalization for all N*N pairs, correcting for the i<j loop (A: Fix RDF normalization).
        norm = np.pi * bin_centers * dr * self.engine.num_particles * rho
        
        # Avoid division by zero
        norm[norm == 0] = 1.0 # Use 1.0 for robustness
        
        gr = hist / norm
        return bin_centers, gr
    
    # This function handles exporting the current RDF data to a CSV file

    def export_rdf_to_csv(self, filename="rdf_export.csv"):
        """Exports the current smoothed RDF data to a CSV file."""
        if self.rdf_ema is None:
            print("Cannot export: RDF data has not been calculated yet.")
            return

        r, _ = self.calculate_rdf() # Get the r values (bin centers)

        # The data to save: r (bin centers) and the smoothed g(r) (rdf_ema)
        data = np.column_stack((r, self.rdf_ema))

        # Header for the CSV file
        header = "r_distance,g_r_smoothed"

        try:
            np.savetxt(filename, data, delimiter=",", header=header, comments="# ")
            print(f"Successfully exported RDF data to {filename}")
        except Exception as e:
            print(f"Error saving RDF data: {e}")
        
    def update_plots(self):
        # Update particle plot
        positions = self.engine.positions
        self.particles_plot.set_offsets(positions)
        
        # Update RDF plot
        r, gr = self.calculate_rdf()
        
        # B) Apply Exponential Moving Average (EMA) for smoothing
        if self.rdf_ema is None:
            self.rdf_ema = gr
        else:
            self.rdf_ema = (1 - self.rdf_alpha) * self.rdf_ema + self.rdf_alpha * gr
            
        self.rdf_line.set_data(r, self.rdf_ema)
        
        self.canvas.draw()