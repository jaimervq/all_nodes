// Author: Jaime Rivera <jaime.rvq@gmail.com>
// Copyright: Copyright 2022, Jaime Rivera
// License: "MIT License"

use euclid::default::Point2D;
use noise::{NoiseFn, Simplex};
use pyo3::prelude::*;
use rand::Rng;

fn fbm(
    noise: &impl NoiseFn<f64, 2>,
    x: f64,
    y: f64,
    octaves: usize,
    lacunarity: f64,
    gain: f64,
) -> f64 {
    let mut total = 0.0;
    let mut frequency = 1.0;
    let mut amplitude = 1.0;

    for _ in 0..octaves {
        total += noise.get([x * frequency, y * frequency]) * amplitude;
        frequency *= lacunarity;
        amplitude *= gain;
    }

    total
}

#[pyfunction]
fn colorful_fbm_noise(width: usize, height: usize, scale: f64, seed: u32) -> PyResult<Vec<u8>> {
    if width == 0 || height == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Width and height must be > 0",
        ));
    }

    let simplex_r = Simplex::new(seed);
    let simplex_g = Simplex::new(seed.wrapping_add(1));
    let simplex_b = Simplex::new(seed.wrapping_add(2));

    let octaves = 4;
    let lacunarity = 2.0;
    let gain = 0.5;

    let mut rgb_data = Vec::with_capacity(width * height * 3);

    for y in 0..height {
        for x in 0..width {
            let nx = x as f64 / scale;
            let ny = y as f64 / scale;

            let r = fbm(&simplex_r, nx, ny, octaves, lacunarity, gain);
            let g = fbm(&simplex_g, nx, ny, octaves, lacunarity, gain);
            let b = fbm(&simplex_b, nx, ny, octaves, lacunarity, gain);

            // Normalize from approximately [-1, 1] to [0, 255]
            let r_u8 = ((r + 1.0) * 0.5 * 255.0).clamp(0.0, 255.0) as u8;
            let g_u8 = ((g + 1.0) * 0.5 * 255.0).clamp(0.0, 255.0) as u8;
            let b_u8 = ((b + 1.0) * 0.5 * 255.0).clamp(0.0, 255.0) as u8;

            rgb_data.push(r_u8);
            rgb_data.push(g_u8);
            rgb_data.push(b_u8);
        }
    }

    Ok(rgb_data)
}

fn generate_seeds_with_colors(
    num_seeds: usize,
    width: usize,
    height: usize,
) -> (Vec<Point2D<f32>>, Vec<[u8; 3]>) {
    let mut rng = rand::rng();
    let seeds: Vec<Point2D<f32>> = (0..num_seeds)
        .map(|_| {
            Point2D::new(
                rng.random_range(0.0..width as f32),
                rng.random_range(0.0..height as f32),
            )
        })
        .collect();

    let colors: Vec<[u8; 3]> = (0..num_seeds)
        .map(|_| [rng.random(), rng.random(), rng.random()])
        .collect();

    (seeds, colors)
}

fn compute_voronoi_rgb(
    width: usize,
    height: usize,
    seeds: &[Point2D<f32>],
    colors: &[[u8; 3]],
) -> Vec<u8> {
    let mut result = Vec::with_capacity(width * height * 3);

    for y in 0..height {
        for x in 0..width {
            let point = Point2D::new(x as f32, y as f32);

            let mut min_dist = f32::MAX;
            let mut closest_idx = 0;

            for (i, &seed) in seeds.iter().enumerate() {
                let d = point.distance_to(seed);
                if d < min_dist {
                    min_dist = d;
                    closest_idx = i;
                }
            }

            result.extend_from_slice(&colors[closest_idx]);
        }
    }

    result
}

#[pyfunction]
fn simplex_noise_rgb(width: usize, height: usize, scale: f64, seed: u32) -> PyResult<Vec<u8>> {
    if width == 0 || height == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Width and height must be > 0",
        ));
    }

    let simplex = Simplex::new(seed);
    let mut rgb_data = Vec::with_capacity(width * height * 3);

    for y in 0..height {
        for x in 0..width {
            let nx = x as f64 / scale;
            let ny = y as f64 / scale;

            // Noise value approx in [-1, 1]
            let val = simplex.get([nx, ny]);

            // Normalize to [0, 255]
            let norm = ((val + 1.0) * 0.5 * 255.0).clamp(0.0, 255.0) as u8;

            // Push grayscale RGB
            rgb_data.push(norm);
            rgb_data.push(norm);
            rgb_data.push(norm);
        }
    }

    Ok(rgb_data)
}

#[pyfunction]
fn voronoi_rgb(width: usize, height: usize, num_seeds: usize) -> PyResult<Vec<u8>> {
    if width == 0 || height == 0 || num_seeds == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be > 0",
        ));
    }

    let (seeds, colors) = generate_seeds_with_colors(num_seeds, width, height);
    let rgb_data = compute_voronoi_rgb(width, height, &seeds, &colors);
    Ok(rgb_data)
}

#[pymodule]
fn rust_noise(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(voronoi_rgb, m)?)?;
    m.add_function(wrap_pyfunction!(simplex_noise_rgb, m)?)?;
    m.add_function(wrap_pyfunction!(colorful_fbm_noise, m)?)?;
    Ok(())
}
