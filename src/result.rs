use std::collections::HashMap;

use pyo3::{
    Bound, exceptions::{PyBaseException, PyTypeError, PyValueError}, prelude::*, types::{PyDict, PyFunction, PyTuple, PyType}
};

use crate::frozen::NONE_REPR;


type PyObjHash = isize;

#[pyclass(module = "py_wraps")]
#[derive(Debug)]
pub struct Result {
    _ok: Option<Py<PyAny>>,
    _err: Option<Py<PyBaseException>>,
    _err_handlers: HashMap<PyObjHash, (Py<PyType>, Py<PyFunction>)>
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

    fn get_py_hash(&self, py: Python<'_>, value: &Py<PyAny>) -> PyResult<PyObjHash> {
        Ok(value.bind(py).hash()?)
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

    #[pyo3(signature=(err, mapped_handlers))]
    fn get_err_handler(&self, py: Python<'_>, err: Py<PyBaseException>, mapped_handlers: Py<PyDict>) -> PyResult<Option<Py<PyFunction>>> {
        let hash = self.get_py_hash(py, err.as_any())?;
        match mapped_handlers.bind(py).get_item(hash)? {
            Some(handler) => {
                Ok(Some(handler.extract::<Py<PyFunction>>()?))
            },
            None => {
                for (exc, handler) in mapped_handlers.bind(py).iter() {
                    println!("exc={}, err={}", exc, err.as_any().bind(py).hash()?);
                    if err.as_any().bind(py).is_instance(exc.as_any())? {
                        return Ok(Some(handler.extract::<Py<PyFunction>>()?));
                    }
                    println!("after if");
                }
                Ok(None)
            },
        }
    }

    #[pyo3(signature=(mapped_handlers), name="match")]
    fn _match(&self, py: Python<'_>, mapped_handlers: Py<PyDict>) -> PyResult<Option<Py<PyAny>>> {
        match &self.err() {
            None => {
                Ok(self.ok())
            },
            Some(err) => {
                match self.get_err_handler(py, err.clone_ref(py), mapped_handlers)? {
                    Some(res) => Ok(Some(res.call0(py)?)),
                    None => {
                        let _err = err.bind(py);
                        let msg = format!(
                            "mapped must contain a handler for exception type {}. Original err message: {}",
                            _err.as_any().get_type(),
                            _err,
                        );
                        Err(PyValueError::new_err(msg))
                    },
                }
            },
        }
    }

    #[pyo3(signature=(err, handler))]
    fn add_err_handler(&mut self, py: Python<'_>, err: Py<PyType>, handler: Py<PyFunction>) -> PyResult<()> {
        match err.bind(py).is_subclass_of::<PyBaseException>()? {
            true => {
                let hash_key = self.get_py_hash(py, err.as_any().as_ref())?;
                let value = (err, handler);
                self._err_handlers.insert(hash_key, value);
                Ok(())
            },
            false => {
                let msg = format!("err must be subclass `Exception` not `{}`", err.bind(py));
                Err(PyTypeError::new_err(msg))
            },
        }
    }

    #[pyo3(signature=(mapped_handlers))]
    fn add_err_handlers(&mut self, py: Python<'_>, mapped_handlers: Py<PyDict>) -> PyResult<()> {
        for (exc, handler) in mapped_handlers.bind(py).iter() {
            if exc.is_instance_of::<PyType>() {
                let exc_type = exc.extract::<Py<PyType>>()?;
                if exc_type.bind(py).is_subclass_of::<PyBaseException>()? && handler.is_callable() {
                    let func = handler.extract::<Py<PyFunction>>()?;
                    let _ = self.add_err_handler(py, exc_type, func);
                }
            }
        }
        Ok(())
    }

    #[pyo3(signature=())]
    fn unwrap_with_handlers(&self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        match self.err() {
            None => Ok(self.ok()),
            Some(err) => {
                let dict = PyDict::new(py);
                for (_k, (exc_type, handler)) in &self._err_handlers {
                    dict.set_item(exc_type.clone_ref(py), handler.clone_ref(py))?;
                }
                let handler = self.get_err_handler(py, err.clone_ref(py), dict.unbind())?;
                match handler {
                    Some(_handler) => Ok(Some(_handler.call0(py)?)),
                    None => {
                        let msg = format!("unset handler for `{}` exception type. Original err message: {}", err.bind(py).as_any().get_type(), self.err_string());
                        Err(PyValueError::new_err(msg))
                    },
                }
            },
        }
    }

    #[pyo3(signature=(default))]
    fn unwrap_with_handlers_or(&self, py: Python<'_>, default: Py<PyAny>) -> Option<Py<PyAny>> {
        let unwrapped = self.unwrap_with_handlers(py);
        match unwrapped {
            Ok(ok) => ok,
            Err(_) => Some(default),
        }
    }

    #[pyo3(signature=(func))]
    fn unwrap_with_handlers_or_else(&self, py: Python<'_>, func: Py<PyFunction>) -> PyResult<Option<Py<PyAny>>> {
        match self.unwrap_with_handlers(py) {
            Ok(ok) => Ok(ok),
            Err(_) => {
                let default = func.call0(py)?;
                Ok(Some(default))
            },
        }
    }

    #[pyo3(signature=())]
    fn is_err_handled(&self, py: Python<'_>) -> PyResult<bool> {
        match self.err() {
            None => Ok(true),
            Some(err) => {
                let dict = PyDict::new(py);
                for (_k, (exc_type, handler)) in &self._err_handlers {
                    dict.set_item(exc_type, handler)?;
                }
                let handler = self.get_err_handler(py, err, dict.unbind())?;
                match handler {
                    Some(_) => Ok(true),
                    None => Ok(false),
                }
            },
        }
    }

    #[pyo3(signature=())]
    fn err_type(&self, py: Python<'_>) -> PyResult<Option<Py<PyType>>> {
        match self.err() {
            Some(err) => Ok(Some(err.bind(py).get_type().unbind())),
            None => Ok(None),
        }
    }

    #[pyo3(signature=(err_type))]
    fn check_err_type(&self, py: Python<'_>, err_type: Py<PyType>) -> PyResult<bool> {
        match self.err() {
            Some(_err) => {
                _err.bind(py).as_any().is_instance(err_type.bind(py))
            },
            None => Ok(false),
        }
    }

    fn __repr__(&self) -> String {
        format!("Result(ok={}, err={})", self.ok_string(), self.err_string())
    }
}
