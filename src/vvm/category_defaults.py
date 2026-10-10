"""Built-in category detection rules used to seed a fresh config file.

Order matters: rules are evaluated top to bottom and the first one with an
installed "prolific" package wins. A rule with an empty package list is the
catch-all (``other``). The ordering lives here (and in the generated config),
never in :mod:`vvm.config`.
"""

from __future__ import annotations

import json

DEFAULT_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "ai",
        (
            "torch",
            "tensorflow",
            "tokenizers",
            "transformers",
            "keras",
            "jax",
            "onnx",
            "sentencepiece",
        ),
    ),
    (
        "data_science",
        (
            "pandas",
            "matplotlib",
            "numpy",
            "scipy",
            "scikit-learn",
            "seaborn",
            "plotly",
            "statsmodels",
            "jupyter",
            "polars",
        ),
    ),
    (
        "server",
        (
            "fastapi",
            "flask",
            "django",
            "uvicorn",
            "gunicorn",
            "starlette",
            "aiohttp",
            "tornado",
            "sanic",
            "bottle",
            "pyramid",
        ),
    ),
    ("other", ()),
)

_HEADER = (
    "# vvm configuration.\n"
    "# Categories are matched in order: the first category with an installed\n"
    '# "prolific" package wins. An empty package list is the catch-all.\n'
)


def render_default_config() -> str:
    """Render the initial config file contents (currently just categories)."""
    lines = [_HEADER, "[categories]"]
    for name, packages in DEFAULT_CATEGORY_RULES:
        rendered = ", ".join(json.dumps(package) for package in packages)
        lines.append(f"{name} = [{rendered}]")
    return "\n".join(lines) + "\n"


DEFAULT_CONFIG_TOML = render_default_config()
