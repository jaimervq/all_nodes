// Author: Jaime Rivera <jaime.rvq@gmail.com>
// Copyright: Copyright 2022, Jaime Rivera
// License: "MIT License"

use chrono::Local;
use percent_encoding::percent_decode_str;
use pyo3::prelude::*;
use rayon::prelude::*;
use reqwest::blocking::Client;
use std::{
    fs::File,
    io::Write,
    path::{Path, PathBuf},
    sync::Mutex,
};
use url::Url;

fn guess_extension_from_content_type(content_type: Option<&str>) -> String {
    match content_type {
        Some("image/png") => ".png".to_string(),
        Some("image/jpeg") => ".jpg".to_string(),
        Some("image/gif") => ".gif".to_string(),
        Some("image/webp") => ".webp".to_string(),
        _ => ".bin".to_string(),
    }
}

#[pyfunction]
fn download_images(urls: Vec<String>, target_dir: &str) -> PyResult<Vec<PathBuf>> {
    let client = Client::builder()
        .user_agent("rayon_image_downloader/0.1")
        .build()
        .unwrap();

    let dir = Path::new(target_dir);
    std::fs::create_dir_all(dir).unwrap();

    let written = Mutex::new(vec![]);

    urls.par_iter().enumerate().for_each(|(i, url)| {
        let resp = client.get(url).send();
        if let Ok(res) = resp {
            if res.status().is_success() {
                let guessed_extension = guess_extension_from_content_type(
                    res.headers()
                        .get(reqwest::header::CONTENT_TYPE)
                        .and_then(|v| v.to_str().ok()),
                );

                let extension = Url::parse(url)
                    .ok()
                    .and_then(|parsed_url| {
                        parsed_url
                            .path_segments()
                            .and_then(|segments| segments.last())
                            .map(|filename| filename.to_string())
                    })
                    .and_then(|filename| {
                        filename
                            .split('.')
                            .last()
                            .filter(|ext| !ext.is_empty())
                            .map(|ext| format!(".{}", ext))
                    })
                    .unwrap_or_else(|| guessed_extension.to_string());

                let generic_filename = format!("file_{}{}", i, extension).to_owned();
                let mut filename = url
                    .split('/')
                    .last()
                    .unwrap_or(&generic_filename)
                    .to_string();
                filename = percent_decode_str(&filename)
                    .decode_utf8_lossy()
                    .into_owned();
                let path = dir.join(&filename);

                if let Ok(mut file) = File::create(&path) {
                    if let Ok(bytes) = res.bytes() {
                        if file.write_all(&bytes).is_ok() {
                            written.lock().unwrap().push(path);
                        }
                    }
                }
            }
        }
    });

    let mut result = written.lock().unwrap().clone();
    result.sort();
    println!(
        "{}  🦀 INFO- Downloaded {} images",
        Local::now().format("%Y%m%d %H:%M:%S%.3f"),
        result.len()
    );
    Ok(result)
}

#[pymodule]
fn rust_requests(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(download_images, m)?)?;
    Ok(())
}
