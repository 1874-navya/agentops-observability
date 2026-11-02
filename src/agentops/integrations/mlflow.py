from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


@contextmanager
def mlflow_span(
    name: str,
    *,
    span_type: str = "UNKNOWN",
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """Create a nested MLflow tracing span without making MLflow a core dependency."""
    try:
        import mlflow
    except ImportError as exc:
        raise RuntimeError("Install MLflow extras: pip install '.[mlflow]'") from exc

    with mlflow.start_span(name=name, span_type=span_type) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)
        yield span
