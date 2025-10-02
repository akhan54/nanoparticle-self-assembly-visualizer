import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QDoubleSpinBox, QSpinBox, 
    QHBoxLayout, QSlider, QFileDialog
)
from PyQt5.QtCore import QTimer, Qt
from simulation_engine import SimulationEngine
from particle_renderer import ParticleRenderer

# The default seed for reproducibility
DEFAULT_SEED = 42

class MainWindow(QMainWindow):
    def __init__(self, simulation_engine):
        super().__init__()
        self.setWindowTitle("Nanoparticle Self-Assembly Visualizer")
        self.simulation_engine = simulation_engine
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        
        self.particle_renderer = ParticleRenderer(self.simulation_engine)
        main_layout.addWidget(self.particle_renderer)
        
        # --- Control Panel Layout ---
        control_layout = QHBoxLayout()
        
        # Temperature Control
        temp_layout = QVBoxLayout()
        temp_label = QLabel("Temp (reduced units):")
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(1, 100)
        self.temp_slider.setValue(int(self.simulation_engine.temperature * 10))
        self.temp_slider.valueChanged.connect(self.update_temperature)
        self.temp_value_label = QLabel(f"{self.simulation_engine.temperature:.1f}")
        temp_sub_layout = QHBoxLayout()
        temp_sub_layout.addWidget(temp_label)
        temp_sub_layout.addWidget(self.temp_value_label)
        temp_layout.addLayout(temp_sub_layout)
        temp_layout.addWidget(self.temp_slider)

        # Num Particles Control
        num_layout = QVBoxLayout()
        num_label = QLabel("Num Particles:")
        self.num_spinbox = QSpinBox() # Changed to QSpinBox for particle count
        self.num_spinbox.setRange(50, 2000)
        self.num_spinbox.setSingleStep(50)
        self.num_spinbox.setValue(self.simulation_engine.num_particles)
        self.num_spinbox.valueChanged.connect(self.update_num_particles)
        num_layout.addWidget(num_label)
        num_layout.addWidget(self.num_spinbox)

        # Epsilon (Interaction Strength) Control
        epsilon_layout = QVBoxLayout()
        epsilon_label = QLabel("Epsilon:")
        self.epsilon_spinbox = QDoubleSpinBox()
        self.epsilon_spinbox.setRange(0.1, 5.0)
        self.epsilon_spinbox.setSingleStep(0.1)
        self.epsilon_spinbox.setValue(self.simulation_engine.epsilon)
        epsilon_layout.addWidget(epsilon_label)
        epsilon_layout.addWidget(self.epsilon_spinbox)
        self.epsilon_spinbox.valueChanged.connect(self.update_epsilon)
        
        # Seed Control
        seed_layout = QVBoxLayout()
        seed_label = QLabel("Seed:")
        self.seed_spinbox = QSpinBox()
        self.seed_spinbox.setRange(0, 10000)
        self.seed_spinbox.setValue(DEFAULT_SEED)
        self.seed_spinbox.valueChanged.connect(self.update_seed)
        seed_layout.addWidget(seed_label)
        seed_layout.addWidget(self.seed_spinbox)
        
        # Reduced Temperature Display (T* = T / epsilon)
        self.t_star_label = QLabel(f"T*: {self.simulation_engine.temperature / self.simulation_engine.epsilon:.2f}")

        # Pause/Resume Button
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_simulation)
        
        # Reset Button (initializes with current settings, including seed)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_simulation)
        
        # New: Save Button
        save_button = QPushButton("Save RDF / Snapshot")
        save_button.clicked.connect(self.save_data_dialog)
        
        # Assemble control layout
        control_layout.addLayout(temp_layout)
        control_layout.addLayout(num_layout)
        control_layout.addLayout(epsilon_layout)
        control_layout.addLayout(seed_layout) # Add seed control
        control_layout.addWidget(self.t_star_label)
        control_layout.addWidget(self.pause_resume_button)
        control_layout.addWidget(reset_button)
        control_layout.addWidget(save_button) # Add save button
        
        main_layout.addLayout(control_layout)
        
        # Start the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_and_update)
        self.timer.start(16)
        
    def update_t_star_display(self):
        t_star = self.simulation_engine.temperature / self.simulation_engine.epsilon
        self.t_star_label.setText(f"T*: {t_star:.2f}")

    def update_temperature(self, value):
        temp_value = value / 10.0
        self.simulation_engine.temperature = temp_value
        self.temp_value_label.setText(f"{temp_value:.1f}")
        self.update_t_star_display()
        
    def update_num_particles(self, value):
        self.simulation_engine.num_particles = int(value)
        self.reset_simulation()

    def update_epsilon(self, value):
        self.simulation_engine.epsilon = value
        self.update_t_star_display()
        
    def update_seed(self, value):
        # We only apply the new seed on reset/re-initialization
        pass
    
    def reset_simulation(self):
        current_seed = self.seed_spinbox.value()
        self.simulation_engine.re_initialize_system(
            self.simulation_engine.num_particles, 
            self.simulation_engine.box_size,
            self.simulation_engine.temperature,
            seed=current_seed # Pass the seed to re_initialize
        )
        
    def toggle_simulation(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_resume_button.setText("Resume")
        else:
            self.timer.start()
            self.pause_resume_button.setText("Pause")

    # New method to handle the save dialog and data export
    def save_data_dialog(self):
        # Use QFileDialog to get a file name from the user
        filename, _ = QFileDialog.getSaveFileName(self, 
                                                  "Save RDF Data", 
                                                  "rdf_export.csv", 
                                                  "CSV Files (*.csv);;All Files (*)")
        
        if filename:
            self.particle_renderer.export_rdf_to_csv(filename)
        
    def run_and_update(self):
        self.simulation_engine.run_step()
        self.particle_renderer.update_plots()
        
if __name__ == '__main__':
    # Initial setup for the simulation engine, using the default seed
    initial_particles = 250
    initial_box = 25.0
    initial_temp = 2.0
    
    engine = SimulationEngine(initial_particles, initial_box, initial_temp, seed=DEFAULT_SEED)
    
    app = QApplication(sys.argv)
    window = MainWindow(engine)
    window.show()
    sys.exit(app.exec_())