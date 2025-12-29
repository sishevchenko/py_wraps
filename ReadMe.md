# py_wrap

py_wrap - это библиотека для оборачивания результата выполнения `Python` функций в специальный объект `Result`, который подавляет потенциальные ошибки обернутых в него функций и позволяет их гибко обрабатывать, не приводя к мгновенному возбуждению исключения для его корректной обработки на уровне с достаточным количеством полномочий.

## Дополнительная информация

- Дополнительную информацию по практике использования `Result` можно найти в интернете по запросу **_Result pattern_**
- За рефференс был взят [Result](https://doc.rust-lang.org/std/result/enum.Result.html) из `Rust` и частично реализация из `Java`

## Инструкция по установке (pip)

```bash
python3 -m venv .venv
source ./.venv/bin/activate
pip install maturin
maturin develop
```

## Примеры использования

1. Преобразуем вызов функции, которая приводит к ошибке к `Result`

    ```python
    def exc_func():
        ...
        if some:
            raise ValueError("Some ValueError")
        ...

    res = Result.wrap(exc_func)
    ```

2. Базовый функционал

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
