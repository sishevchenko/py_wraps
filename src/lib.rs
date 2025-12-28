use pyo3::prelude::*;

mod result;
use result::Result;
mod frozen;


#[pymodule]
fn py_wraps(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Result>()?;
    Ok(())
}
