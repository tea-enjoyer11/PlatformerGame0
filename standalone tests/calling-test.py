from typing import Callable, Any


def call_after(callable_after: Callable[..., Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            callable_after(*args, **kwargs)
            return result
        return wrapper
    return decorator


def call_before(callable_before: Callable[..., Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            callable_before(*args, **kwargs)
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def beispiel2() -> None:
    print("beispiel2 called")


@call_after(beispiel2)
def beispiel() -> None:
    print("beispiel called")


def test2() -> None:
    print("test2 called")


@call_before(test2)
def test() -> None:
    print("test called")


beispiel()
test()
