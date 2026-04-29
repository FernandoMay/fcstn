"""
Fractal Generation Engine
Implementation of Mandelbrot set computation with GPU acceleration
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
import logging

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logging.warning("CuPy not available. Falling back to CPU computation.")

@dataclass
class FractalParameters:
    """Parameters for fractal generation"""
    center: Tuple[float, float] = (-0.5, 0.0)
    zoom: float = 1.0
    max_iterations: int = 256
    escape_radius: float = 2.0
    resolution: Tuple[int, int] = (1920, 1080)


class MandelbrotGenerator:
    """
    Real-time Mandelbrot set generator with GPU acceleration.
    
    Implements the iterative formula: z_{n+1} = z_n^2 + c
    where z and c are complex numbers.
    """
    
    def __init__(self, params: Optional[FractalParameters] = None, use_gpu: bool = True):
        """
        Initialize the Mandelbrot generator.
        
        Args:
            params: Fractal generation parameters
            use_gpu: Whether to use GPU acceleration if available
        """
        self.params = params or FractalParameters()
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.xp = cp if self.use_gpu else np
        
        logging.info(f"Mandelbrot Generator initialized (GPU: {self.use_gpu})")
    
    def generate(self) -> np.ndarray:
        """
        Generate the Mandelbrot set fractal field.
        
        Returns:
            2D array of iteration counts for each pixel
        """
        width, height = self.params.resolution
        cx, cy = self.params.center
        
        # Create complex plane grid
        x = self.xp.linspace(
            cx - 2.0/self.params.zoom,
            cx + 2.0/self.params.zoom,
            width
        )
        y = self.xp.linspace(
            cy - 1.5/self.params.zoom,
            cy + 1.5/self.params.zoom,
            height
        )
        
        X, Y = self.xp.meshgrid(x, y)
        C = X + 1j * Y
        
        # Initialize arrays
        Z = self.xp.zeros_like(C)
        M = self.xp.zeros(C.shape, dtype=self.xp.int32)
        
        # Mandelbrot iteration
        for i in range(self.params.max_iterations):
            # Check which points have not escaped
            mask = self.xp.abs(Z) <= self.params.escape_radius
            
            # Update Z for non-escaped points
            Z[mask] = Z[mask]**2 + C[mask]
            
            # Increment iteration count
            M[mask] = i
        
        # Convert back to numpy if using GPU
        if self.use_gpu:
            M = cp.asnumpy(M)
        
        return M.T
    
    def generate_smooth(self) -> np.ndarray:
        """
        Generate smooth-colored Mandelbrot set using continuous iteration count.
        
        Returns:
            2D array of smooth iteration values
        """
        width, height = self.params.resolution
        cx, cy = self.params.center
        
        # Create complex plane grid
        x = self.xp.linspace(
            cx - 2.0/self.params.zoom,
            cx + 2.0/self.params.zoom,
            width
        )
        y = self.xp.linspace(
            cy - 1.5/self.params.zoom,
            cy + 1.5/self.params.zoom,
            height
        )
        
        X, Y = self.xp.meshgrid(x, y)
        C = X + 1j * Y
        
        # Initialize arrays
        Z = self.xp.zeros_like(C)
        M = self.xp.zeros(C.shape, dtype=self.xp.float32)
        
        # Mandelbrot iteration
        for i in range(self.params.max_iterations):
            mask = self.xp.abs(Z) <= self.params.escape_radius
            Z[mask] = Z[mask]**2 + C[mask]
            M[mask] = i
        
        # Smooth coloring
        final_mask = self.xp.abs(Z) > self.params.escape_radius
        M[final_mask] = M[final_mask] + 1 - self.xp.log(self.xp.log(self.xp.abs(Z[final_mask])))/self.xp.log(2)
        
        if self.use_gpu:
            M = cp.asnumpy(M)
        
        return M.T
    
    def generate_multiscale(self, num_scales: int = 5) -> dict:
        """
        Generate multi-scale fractal representations.
        
        Args:
            num_scales: Number of zoom levels to generate
            
        Returns:
            Dictionary mapping scale to fractal field
        """
        original_zoom = self.params.zoom
        scales = {}
        
        for i in range(num_scales):
            zoom_level = original_zoom * (2 ** i)
            self.params.zoom = zoom_level
            scales[zoom_level] = self.generate()
        
        self.params.zoom = original_zoom
        return scales
    
    def compute_density_field(self) -> np.ndarray:
        """
        Compute spatial density field from fractal iterations.
        
        Returns:
            Normalized density field (0-1)
        """
        fractal_field = self.generate()
        density = fractal_field / self.params.max_iterations
        return density
    
    def find_interesting_regions(self, threshold: float = 0.5) -> list:
        """
        Identify regions with high fractal complexity.
        
        Args:
            threshold: Complexity threshold (0-1)
            
        Returns:
            List of (x, y, complexity) tuples for interesting regions
        """
        fractal_field = self.generate_smooth()
        
        # Compute local complexity via gradient magnitude
        if self.use_gpu:
            gradient = cp.gradient(self.xp.array(fractal_field))
            complexity = cp.sqrt(gradient[0]**2 + gradient[1]**2)
            complexity = cp.asnumpy(complexity)
        else:
            gradient = np.gradient(fractal_field)
            complexity = np.sqrt(gradient[0]**2 + gradient[1]**2)
        
        # Normalize
        complexity = complexity / complexity.max()
        
        # Find regions above threshold
        interesting = []
        y_coords, x_coords = np.where(complexity > threshold)
        
        for y, x in zip(y_coords, x_coords):
            interesting.append((x, y, complexity[y, x]))
        
        return interesting


class JuliaSetGenerator:
    """
    Julia set generator for creating variant fractal patterns.
    
    Implements: z_{n+1} = z_n^2 + c with fixed c
    """
    
    def __init__(self, c: complex, params: Optional[FractalParameters] = None, use_gpu: bool = True):
        """
        Initialize Julia set generator.
        
        Args:
            c: Complex constant for Julia set
            params: Fractal generation parameters
            use_gpu: Whether to use GPU acceleration
        """
        self.c = c
        self.params = params or FractalParameters()
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.xp = cp if self.use_gpu else np
    
    def generate(self) -> np.ndarray:
        """Generate Julia set"""
        width, height = self.params.resolution
        cx, cy = self.params.center
        
        # Create complex plane grid
        x = self.xp.linspace(cx - 2.0/self.params.zoom, cx + 2.0/self.params.zoom, width)
        y = self.xp.linspace(cy - 1.5/self.params.zoom, cy + 1.5/self.params.zoom, height)
        
        X, Y = self.xp.meshgrid(x, y)
        Z = X + 1j * Y
        
        M = self.xp.zeros(Z.shape, dtype=self.xp.int32)
        
        for i in range(self.params.max_iterations):
            mask = self.xp.abs(Z) <= self.params.escape_radius
            Z[mask] = Z[mask]**2 + self.c
            M[mask] = i
        
        if self.use_gpu:
            M = cp.asnumpy(M)
        
        return M.T


def create_color_mapping(fractal_field: np.ndarray, colormap: str = 'twilight') -> np.ndarray:
    """
    Create RGB color mapping from fractal iteration counts.
    
    Args:
        fractal_field: 2D array of iteration counts
        colormap: Matplotlib colormap name
        
    Returns:
        RGB image array
    """
    import matplotlib.cm as cm
    
    # Normalize to 0-1
    normalized = fractal_field / fractal_field.max()
    
    # Apply colormap
    cmap = cm.get_cmap(colormap)
    colored = cmap(normalized)
    
    # Convert to 8-bit RGB
    rgb = (colored[:, :, :3] * 255).astype(np.uint8)
    
    return rgb


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    params = FractalParameters(
        center=(-0.5, 0.0),
        zoom=1.0,
        max_iterations=256,
        resolution=(1920, 1080)
    )
    
    generator = MandelbrotGenerator(params)
    fractal = generator.generate_smooth()
    
    print(f"Generated fractal field: {fractal.shape}")
    print(f"Value range: [{fractal.min():.2f}, {fractal.max():.2f}]")
    
    # Find interesting regions
    regions = generator.find_interesting_regions(threshold=0.7)
    print(f"Found {len(regions)} interesting regions")
