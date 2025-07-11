// Author: Jaime Rivera <jaime.rvq@gmail.com>
// Copyright: Copyright 2022, Jaime Rivera
// License: "MIT License"

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use rayon::prelude::*;
use regex::Regex;
use std::fs;

#[pyfunction]
fn find_word_matches_parallel(path: &str, word: &str) -> PyResult<usize> {
    let content =
        fs::read_to_string(path).or_else(|_| Err(PyRuntimeError::new_err("Could not open file!")));

    let pattern = format!(r"\b{}\b", regex::escape(word));
    let re = Regex::new(&pattern).unwrap();

    let count: usize = content?
        .par_lines()
        .map(|line| re.find_iter(line).count())
        .sum();

    Ok(count)
}

#[pymodule]
fn rust_regex(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_word_matches_parallel, m)?)?;
    Ok(())
}
