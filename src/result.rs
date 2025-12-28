use std::collections::HashMap;

use pyo3::{
    Bound,
    prelude::*,
    types::{PyDict, PyFunction, PyTuple, PyType},
    exceptions::{PyBaseException, PyTypeError, PyValueError},
};

use crate::frozen::NONE_REPR;


#[pyclass(module = "py_wraps")]
#[derive(Debug)]
pub struct Result {
    _ok: Option<Py<PyAny>>,
    _err: Option<Py<PyBaseException>>,
    _err_handlers: HashMap<Py<PyBaseException>, Py<PyFunction>>
}

// Функции недоступные из Python
impl Result {
    fn ok_string(&self) -> String {
        match &self.ok() {
            Some(ok) => ok.to_string(),
            None => NONE_REPR.to_string(),
        }
    }

    fn err_string(&self) -> String {
        match &self.err() {
            Some(err) => err.to_string(),
            None => NONE_REPR.to_string(),
        }
    }

    fn err_from_exc(&self, py: Python<'_>, err: &Py<PyBaseException>) -> PyErr {
        PyErr::from_value(err.bind(py).as_any().to_owned())
    }
}


// Реализация доступная из Python по FFI
#[pymethods]
impl Result {
    #[new]
    #[pyo3(signature=(ok=None, err=None))]
    fn new(ok: Option<Py<PyAny>>, err: Option<Py<PyBaseException>>) -> PyResult<Self> {
        match (&ok, &err) {
            (Some(_), Some(_)) => {
                Err(PyTypeError::new_err(
                    "`Result` cannot have both `ok` and `err` values",
                ))
            }
            _ => PyResult::Ok(Self{_ok: ok, _err: err, _err_handlers: HashMap::new()}),
        }
    }

    #[classmethod]
    #[pyo3(signature=(func, *, args=None, kwargs=None))]
    fn wrap(_cls: Py<PyType>, func: Py<PyFunction>, args: Option<Py<PyTuple>>, kwargs: Option<Bound<'_, PyDict>>) -> PyResult<Self> {
        Python::attach(|py| {
            let _args = args.unwrap_or_else(|| PyTuple::empty(py).unbind());
            let _kwargs = kwargs.unwrap_or_else(|| PyDict::new(py));
            let res = match func.call(py, _args, Some(&_kwargs)) {
                Ok(ok) => Result::new(Some(ok), None)?,
                Err(err) => {
                    Result::new(None, Some(err.into_value(py)))?
                },
            };
            Ok(res)
        })
    }

    fn is_ok(&self) -> bool {
        !self._err.is_some()
    }

    fn is_err(&self) -> bool {
        self._err.is_some()
    }

    fn ok(&self) -> Option<Py<PyAny>> {
        Python::attach(|py| {
            self._ok.as_ref().map(|ok| ok.clone_ref(py))
        })
    }

    fn err(&self) -> Option<Py<PyBaseException>> {
        Python::attach(|py| {
            self._err.as_ref().map(|err| err.clone_ref(py))
        })
    }

    #[pyo3(signature=())]
    fn unwrap(&self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        match (&self._ok, &self._err) {
            (Some(_), Some(_)) => {
                Err(PyTypeError::new_err(
                    "`Result` cannot have both `ok` and `err` values",
                ))
            },
            (Some(ok), None) => Ok(Some(ok.clone_ref(py))),
            (None, Some(err)) => {
                Err(self.err_from_exc(py, err))
            },
            (None, None) => Ok(None),
        }
    }

    fn unwrap_or(&self, default: Py<PyAny>) -> Option<Py<PyAny>> {
        Python::attach(|py| {
            self.unwrap(py).unwrap_or(Some(default))
        })
    }

    #[pyo3(signature=(func))]
    fn unwrap_or_else(&self, py: Python<'_>, func: Py<PyFunction>) -> PyResult<Option<Py<PyAny>>> {
        match self.unwrap(py) {
            Ok(ok) => Ok(ok),
            Err(_) => {
                let default = func.call0(py)?;
                Ok(Some(default))
            },
        }
    }

    #[pyo3(signature=())]
    fn unwrap_err(&self, py: Python<'_>) -> PyResult<Py<PyBaseException>>{
        match &self._err {
            Some(err) => Ok(err.clone_ref(py)),
            None => {
                let msg = format!("result in status success with value {}", self.ok_string());
                Err(PyValueError::new_err(msg))
            },
        }
    }

    fn __repr__(&self) -> String {
        format!("Result(ok={}, err={})", self.ok_string(), self.err_string())
    }
}
