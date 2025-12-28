from typing import Any, Callable, Mapping, Optional, Tuple, TypeVar, Generic


_Ok = TypeVar("_Ok")
_Err = TypeVar("_Err", bound=Exception)
_GetDefaultFromCallback = Callable[..., _Ok]

class Result(Generic[_Ok, _Err]):
    """Обертка для результата выполнения функции, которая может содержать ошибку, но не приводит к мгновенному возбуждению исключения для его корректной обработки на уровне с достаточным количеством полномочий и вводных

    Примечания:
        - При вызове `Result.unwrap()` в случае ошибки будет сгенерирована **ИСХОДНАЯ ОШИБКА С ЕЕ ОРИГИНАЛЬНОМ СТЕКОМ**, т.е. наличие обертки в виде Result не сказывается на читаемости ошибки
        - Если ошибка **НЕ** была обработана в `Result.match()` или `Result.unwrap_with_handlers()`, то будет **ВОЗБУЖДЕНО ИСКЛЮЧЕНИЕ** отстутствия обработки ошибки, **ВКЛЮЧАЮЩЕЕ В СЕБЯ ВЕСЬ ТРЕЙС ОРИГИНАЛЬНОЙ ОШИБКИ**
        - Дополнительную информацию по практике использования `Result` можно найти в интернете по запросу **_Result pattern_**
        - За рефференс был взят [Result](https://doc.rust-lang.org/std/result/enum.Result.html) из `Rust` и частично из `Java`

    Примеры использования:
        Преобразуем вызов функции, которая приводит к ошибке к `Result`:
            ```python
            def exc_func():
                ...
                if some:
                    raise ValueError("Some ValueError")
                ...

            res = Result.wrap(exc_func)
            ```

        Базовый функционал:
            ```python
            def f(x: int) -> Result[int, ValueError]:
                if x < 0:
                    return Result(err=ValueError("x must be greatest zero"))
                res = x * x
                return Result(ok=res)

            # Получаем ошибку в res
            res = f(-1)

            # Разворачиваем ошибку в значение по умолчанию без возбуждения исключения
            res.unwrap_or(0)

            # Разворачиваем ошибку в значение по умолчанию генерируемое функцией
            res.unwrap_or_else(lambda: 10)
        ```
    """

    def __new__(cls, ok: Optional[_Ok] = None, err: Optional[_Err] = None) -> None:
        ...

    @classmethod
    def wrap(
        cls,
        func: _GetDefaultFromCallback,
        args: Optional[Tuple[Any]] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
    ) -> Result[_Ok, _Err]:
        """Преобразует вызов функции, которая может вызвать исключение в тип `Result`

        Args:
            func (_GetDefaultFromCallback): _description_
            args (Optional[Tuple], optional): _description_. Defaults to None.
            kwargs (Optional[Mapping], optional): _description_. Defaults to None.

        Returns:
            Result[Union[_Ok, _Err]]: _description_
        """
        ...

    def is_ok(self) -> bool:
        """Проверка на успешность полученного результат

        Returns:
            bool: _description_
        """
        ...

    def is_err(self) -> bool:
        """Проверка на наличие ошибки в результате

        Returns:
            bool: _description_
        """
        ...

    def ok(self) -> Optional[_Ok]:
        """Получить результат потенциального успешного выполнения

        Returns:
            Optional[_Ok]: _description_
        """
        ...

    def err(self) -> Optional[_Err]:
        """Получить ошибку потенциально возникшую в результате выполнения

        Returns:
            Optional[_Err]: _description_
        """
        ...

    def unwrap(self) -> Optional[_Ok]:
        """Получить результат успешного выполнения или сгенерировать ошибку возникшую в результате выполнения

        Raises:
            self._err: Ошибка содержащаяся в результате (трейс ошибки полностью соответствует оригинальной ошибке)

        Returns:
            _Ok: _description_
        """
        ...

    def unwrap_or(self, default: _Ok) -> _Ok:
        """Получить результат успешного выполнения или значение по умолчанию

        Args:
            default (_Ok): _description_

        Returns:
            _Ok: _description_
        """
        ...

    def unwrap_or_else(self, func: Callable[..., _Ok]) -> _Ok:
        """Получить результат успешного выполнения или выполнить дополнительную функцию и вернуть ее результат как значение по умолчанию

        Args:
            func (_GetDefaultFromCallback): Callback генерирующий дефолтное значение в случае ошибки в результате

        Returns:
            _Ok: _description_
        """
        ...

    def unwrap_err(self) -> _Err:
        """Получить результат ошибки выполнения или сгенерировать ошибку успешного выполнения

        Примечания:
            Преднозначена для использования в обработчиках ошибок, т.к. уже очевидно, что ошибка возникла, поэтому генерирует ошибку в случае успешного выполнения

        Пример:
            ```python
            res = Result.wrap(raise_value_error_func, args=args, kwargs=kwargs)
            # Представим что value_error_handler логирует сообщение из ValueError, поэтому ему требуется экземпляр ошибки для записи лога
            safe_res = res.add_err_handler(ValueError, lambda: value_error_handler(res.unwrap_err(), some_data)).unwrap_with_handlers()
            ```

        Raises:
            ValueError: Результат имеет статус `ok`

        Returns:
            _Err: _description_
        """
        ...

    def __repr__(self) -> str:
        ...
