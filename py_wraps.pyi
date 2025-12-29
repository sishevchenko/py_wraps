from typing import Any, Awaitable, Callable, Coroutine, Mapping, Optional, Self, Tuple, Type, TypeVar, Generic, Union



_Ok = TypeVar("_Ok")
_Err = TypeVar("_Err", bound=Exception)
_ErrHandlerRes = TypeVar("_ErrHandlerRes")
_GetDefaultFromCallback = Callable[..., _Ok]
_ErrHandler = Callable[..., _ErrHandlerRes]


class Result(Generic[_Ok, _Err, _ErrHandlerRes]):
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

        Преобразуем вызов асинхронной функции, которая приводит к ошибке к `Result`:
            ```python
            def exc_func():
                ...
                if some:
                    raise ValueError("Some ValueError")
                ...

            res = await Result.awrap(exc_func)
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

            # Добавляем обработчик исключения
            res.add_err_handlers(
                {
                    ValueError: lambda: 10,
                }
            )

            # Проверяем обрабатывается ли исключение содержащееся в результате
            res.is_err_handled()

            # Извлеваем результат через обработчики, если обработчика не было, то значение по умолчанию
            res.unwrap_with_handlers_or(0)

            # Разворачиваем результат или обрабатываем ошибку переданным хэндлером и получаем результат его выполнения
            res.match(
                {
                    ValueError: lambda: 10,
                }
            )
        ```
    """

    def __new__(cls, *, ok: Optional[_Ok] = None, err: Optional[_Err] = None):
        """
        Args:
            ok (Optional[_Ok], optional): Успешный результат выполнения функции. Defaults to None.
            err (Optional[_Err], optional): Объект ошибки возникшей в ходе выполнения. Defaults to None.
        """
        ...

    @classmethod
    def wrap(
        cls,
        func: _GetDefaultFromCallback,
        args: Optional[Tuple[Any]] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
    ) -> Result[_Ok, _Err, _ErrHandlerRes]:
        """Преобразует вызов функции, которая может вызвать исключение в тип `Result`

        Args:
            func (_GetDefaultFromCallback): _description_
            args (Optional[Tuple], optional): _description_. Defaults to None.
            kwargs (Optional[Mapping], optional): _description_. Defaults to None.

        Returns:
            Result[Union[_Ok, _Err]]: _description_
        """
        ...

    @classmethod
    async def awrap(
        cls,
        func: Awaitable[Coroutine[Any, Any, _Ok]],
        args: Optional[Tuple[Any]] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
    ) -> Result[_Ok, _Err, _ErrHandlerRes]:
        """Преобразует вызов асинхронной функции, которая может вызвать исключение в тип `Result`

        Args:
            func (Awaitable[Coroutine[Any, Any, _Ok]]): _description_
            args (Optional[Tuple[Any]], optional): _description_. Defaults to None.
            kwargs (Optional[Mapping[str, Any]], optional): _description_. Defaults to None.

        Returns:
            Coroutine[Result[Union[_Ok, _Err]]]: _description_
        """
        ...

    def unwrap(self) -> _Ok:
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

    def unwrap_or_else(self, func: _GetDefaultFromCallback) -> _Ok:
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

    def match(self, mapped_handlers: Mapping[Type[_Err], _ErrHandler]) -> Union[_Ok, _ErrHandlerRes]:
        """Развернуть результат или сопоставить ошибку выполнения с переданными обработчиками и вернуть результат обработчика

        Args:
            mapped (Mapping[Type[_Err], _ErrHandler]): _description_

        Пример:
            ```python
            def f(x: int) -> Result[int, ValueError]:
                if x < 0:
                    return Result(err=ValueError("Some ValueError"))
                return x ** 2

            res = f().match(
                {
                    ValueError: lambda: 10,
                }
            )
            ```
        
        Algorithm:
            - Вернуть `_Ok` если ошибки нет
            - Проверить точное совпадение типа ошибки с хендлером
                - Если совпала, то вызвать хендлер
                - Если не совпала, то проверить не является ли ошибка подтипом ближайшего к началу хендлера
                    - Если совпали подтипы вызвать хендлер 
                    - Raise отсутствия обработки ошибки

        Raises:
            ValueError: Сопоставление не содержит обработчик для ошибки

        Returns:
            Optional[Union[_Ok, _ErrHandlerRes]]: _description_
        """
        ...

    def add_err_handler(self, err: Type[_Err], handler: _ErrHandler) -> Self:
        """Добавить обработчик для потенциальной ошибки

        Args:
            err (Type[_Err]): _description_
            handler (_ErrHandler): _description_

        Raises:
            TypeError: Тип `err` не является исключением
            TypeError: Тип `handler` не `Callable`

        Returns:
            Self: _description_
        """
        ...

    def add_err_handlers(self, mapped: Mapping[Type[_Err], _ErrHandler]) -> Self:
        """Добавить обработчики для потенциально возникших ошибок

        Args:
            mapped (Mapping[Type[_Err], _ErrHandler]): _description_

        Returns:
            Self: _description_
        """
        ...

    def is_err_handled(self) -> bool:
        """Проверка на наличие обработчика для ошибки содержащейся в результате

        Примечания:
            Если результат содержит `_Ok`, то всегда True

        Returns:
            bool: _description_
        """
        ...

    def unwrap_with_handlers(self) -> Union[_Ok, _ErrHandlerRes]:
        """Распаковать результат с помощью обработчиков ошибок

        Raises:
            ValueError: _description_

        Returns:
            Union[_Ok, _ErrHandlerRes]: _description_
        """
        ...

    def unwrap_with_handlers_or(self, default: _Ok) -> Union[_Ok, _ErrHandlerRes]:
        """Распаковать результат с помощью обработчиков ошибок или при отсутствии обработчика вернуть значение по умолчанию

        Args:
            default (_Ok): _description_

        Returns:
            Union[_Ok, _ErrHandlerRes]: _description_
        """
        ...

    def unwrap_with_handlers_or_else(self, func: _GetDefaultFromCallback) -> Union[_Ok, _ErrHandlerRes]:
        """Распаковать результат с помощью обработчиков ошибок или при отсутствии обработчика выполнить дополнительную функцию и вернуть ее результат как значение по умолчанию

        Args:
            func (_GetDefaultFromCallback): _description_

        Returns:
            Union[_Ok, _ErrHandlerRes]: _description_
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

    def err_type(self) -> Optional[Type[_Err]]:
        """Получить тип ошибки в результате

        Returns:
            Type[_Err]: _description_
        """
        ...

    def check_err_type(self, err_type: Type[_Err]) -> bool:
        """Проверить на соответствие тип ошибки в результате переданному типу

        Args:
            err (Type[_Err]): _description_

        Примечания:
            Если в результате `ok`, то всегда `False`

        Returns:
            bool: _description_
        """
        ...

    def get_err_handler(self, err: Type[_Err], handlers: Mapping[Type[_Err], _ErrHandler]) -> Optional[_ErrHandler]:
        """Получить обработчик для ошибки

        Args:
            err (Type[_Err]): _description_

        Returns:
            Optional[_ErrHandler]: _description_
        """
        ...

    def __repr__(self) -> str:
        ...
