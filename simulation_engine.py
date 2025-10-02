import numpy as np

class SimulationEngine:
    # 1. Add 'seed' to __init__
    def __init__(self, num_particles, box_size, temperature, epsilon=1.0, seed=None):
        self.num_particles = num_particles
        self.box_size = box_size
        self.temperature = temperature
        self.epsilon = epsilon
        
        # 2. Use the Seeded RNG object
        self.rng = np.random.default_rng(seed)
        
        self.positions = self.rng.random((num_particles, 2)) * box_size
        self.velocities = (self.rng.random((num_particles, 2)) - 0.5) * np.sqrt(temperature)
        
        self.time_step = 0.005
        self.forces = np.zeros((num_particles, 2))
        self.potential_energy = 0.0
        
        # Cell list parameters
        self.cutoff = 3.0
        self.cell_size = self.cutoff
        self.num_cells_x = int(self.box_size / self.cell_size)
        self.num_cells_y = int(self.box_size / self.cell_size)
        self.cell_list = [[] for _ in range(self.num_cells_x * self.num_cells_y)]

    # 1. Add 'seed' to re_initialize_system
    def re_initialize_system(self, num_particles, box_size, temperature, seed=None):
        self.num_particles = num_particles
        self.box_size = box_size
        self.temperature = temperature
        
        # 2. Re-initialize the RNG with the new seed
        self.rng = np.random.default_rng(seed)

        self.positions = self.rng.random((num_particles, 2)) * box_size
        self.velocities = (self.rng.random((num_particles, 2)) - 0.5) * np.sqrt(temperature)
        self.forces = np.zeros((num_particles, 2))
        self.potential_energy = 0.0
        
        # Recalculate cell list parameters
        self.num_cells_x = int(self.box_size / self.cell_size)
        self.num_cells_y = int(self.box_size / self.cell_size)
        self.cell_list = [[] for _ in range(self.num_cells_x * self.num_cells_y)]

    def build_cell_list(self):
        for cell in self.cell_list:
            cell.clear()
        
        for i in range(self.num_particles):
            ix = int(self.positions[i, 0] / self.cell_size) % self.num_cells_x
            iy = int(self.positions[i, 1] / self.cell_size) % self.num_cells_y
            cell_index = iy * self.num_cells_x + ix
            self.cell_list[cell_index].append(i)

    def calculate_forces(self):
        self.forces.fill(0.0)
        self.potential_energy = 0.0
        self.build_cell_list()
        
        sigma = 1.0
        epsilon = self.epsilon
        min_dist = 0.1 # A small distance to prevent division by zero
        
        for i in range(self.num_particles):
            ix = int(self.positions[i, 0] / self.cell_size) % self.num_cells_x
            iy = int(self.positions[i, 1] / self.cell_size) % self.num_cells_y
            cell_index = iy * self.num_cells_x + ix
            
            neighbor_cells = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx = (ix + dx + self.num_cells_x) % self.num_cells_x
                    ny = (iy + dy + self.num_cells_y) % self.num_cells_y
                    neighbor_cell_index = ny * self.num_cells_x + nx
                    neighbor_cells.append(neighbor_cell_index)

            for neighbor_cell_index in neighbor_cells:
                for j in self.cell_list[neighbor_cell_index]:
                    if i < j:
                        r_vec = self.positions[i] - self.positions[j]
                        r_vec -= self.box_size * np.rint(r_vec / self.box_size)
                        
                        r = np.linalg.norm(r_vec)

                        # Fix for the division by zero error
                        if r < min_dist:
                            r = min_dist

                        if r < self.cutoff:
                            r6 = (sigma / r)**6
                            r12 = r6**2
                            
                            u_ij = 4 * epsilon * (r12 - r6)
                            self.potential_energy += u_ij
                            
                            f_mag = 24 * epsilon * (2 * r12 - r6) / r**2
                            f_vec = f_mag * r_vec
                            
                            self.forces[i] += f_vec
                            self.forces[j] -= f_vec
    
    def run_step(self):
        # ... (Rest of the run_step method is the same)
        self.positions += self.velocities * self.time_step + 0.5 * self.forces * self.time_step**2
        old_forces = self.forces.copy()
        self.calculate_forces()
        self.velocities += 0.5 * (old_forces + self.forces) * self.time_step
        current_kinetic_energy = 0.5 * np.sum(self.velocities**2)
        target_kinetic_energy = 0.5 * self.num_particles * self.temperature * 2
        if current_kinetic_energy > 0:
            scale_factor = np.sqrt(target_kinetic_energy / current_kinetic_energy)
            self.velocities *= scale_factor