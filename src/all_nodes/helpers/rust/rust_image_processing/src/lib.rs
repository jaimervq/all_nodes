use std::sync::Arc;

use exr::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3::Bound;

use rust_logging::*;

//
// =======================
// PURE RUST CORE (hidden)
// =======================
//
pub struct RustImageCore {
    width: usize,
    height: usize,
    pixels: Vec<f32>,
}

impl RustImageCore {
    fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            pixels: vec![0.0; width * height * 4],
        }
    }

    fn set_pixel_at(&mut self, x: usize, y: usize, rgba: (f32, f32, f32, f32)) {
        let idx = (y * self.width + x) * 4;
        let (r, g, b, a) = rgba;
        self.pixels[idx + 0] = r;
        self.pixels[idx + 1] = g;
        self.pixels[idx + 2] = b;
        self.pixels[idx + 3] = a;
    }
}

//
// =======================
// PYTHON WRAPPER
// =======================
//
#[pyclass]
pub struct RustImage {
    core: Arc<RustImageCore>,
}

#[pymethods]
impl RustImage {
    #[getter]
    fn width(&self) -> usize {
        self.core.width
    }

    #[getter]
    fn height(&self) -> usize {
        self.core.height
    }

    /// Return pixels as Vec<f32>
    fn get_pixels(&self) -> Vec<f32> {
        self.core.pixels.clone()
    }

    /// Zero-copy bytes
    fn pixels_as_bytes<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        let slice: &[u8] = bytemuck::cast_slice(&self.core.pixels);
        PyBytes::new(py, slice)
    }

    fn __str__(&self) -> String {
        format!("RustImage {}x{}", self.core.width, self.core.height)
    }

    fn __repr__(&self) -> String {
        format!(
            "RustImage(width={}, height={}, pixels={})",
            self.core.width,
            self.core.height,
            self.core.pixels.len()
        )
    }
}

//
// =======================
// EXR LOADER
// =======================
//
#[pyfunction]
fn load_exr(path: &str) -> PyResult<RustImage> {
    info!("Loading EXR: {}", path);

    let core = read_first_rgba_layer_from_file(
        path,
        // create image
        |resolution, _| RustImageCore::new(resolution.x(), resolution.y()),
        // write pixel
        |core, position, (r, g, b, a): (f32, f32, f32, f16)| {
            core.set_pixel_at(position.x(), position.y(), (r, g, b, a.into()));
        },
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
    .layer_data
    .channel_data
    .pixels;

    warning!("Loaded EXR successfully {}x{}", core.width, core.height);

    Ok(RustImage {
        core: Arc::new(core),
    })
}

//
// =======================
// MODULE
// =======================
//
#[pymodule]
fn rust_image_processing(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_class::<RustImage>()?;
    m.add_function(wrap_pyfunction!(load_exr, m)?)?;
    Ok(())
}
