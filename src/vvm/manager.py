"""Upper-layer facade that wires collaborators and dispatches features.

``VenvManager`` holds the shared configuration and a list of action classes.
Each action exposes a ``build`` factory that assembles its own collaborators;
the manager simply looks the requested command up and delegates to it::

    manager = VenvManager()
    manager.run("detect", directory=Path("."))

Actions are supplied as a list, so new commands only need to be added there.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vvm.actions import BestAction, ConfigAction, DetectAction, UnlinkAction
from vvm.actions.base import Action
from vvm.config import Config, ConfigLoader

DEFAULT_ACTIONS: tuple[type[Action], ...] = (
    DetectAction,
    BestAction,
    UnlinkAction,
    ConfigAction,
)


class VenvManager:
    """Feature facade for the CLI and library consumers."""

    def __init__(
        self,
        config: Config | None = None,
        config_path: Path | None = None,
        actions: tuple[type[Action], ...] = DEFAULT_ACTIONS,
    ) -> None:
        if config is not None:
            self.config = config
            self.config_path = (
                Path(config_path).expanduser() if config_path is not None else ConfigLoader.default_path()
            )
        else:
            loader = ConfigLoader(config_path)
            self.config = loader.load()
            self.config_path = loader.path
        self.actions: dict[str, type[Action]] = {
            self._action_name(action): action for action in actions
        }

    @staticmethod
    def _action_name(action: type[Action]) -> str:
        """Derive the command name from an action class's module (e.g. ``detect``)."""
        return action.__module__.rsplit(".", 1)[-1]

    def run(self, command: str, **kwargs: Any) -> int:
        """Build and run the action registered under ``command``."""
        try:
            action = self.actions[command]
        except KeyError:
            raise ValueError(f"unknown action: {command}") from None
        return action.build(self.config, **kwargs).run()
