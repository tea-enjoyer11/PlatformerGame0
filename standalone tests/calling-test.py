from typing import Callable, Any


def call_after(callable_after: Callable[..., Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            callable_after(*args, **kwargs)
            return result
        return wrapper
    return decorator


def foo2() -> None:
    print("foo2 called")


@call_after(foo2)
def foo() -> None:
    print("foo called")


foo()
