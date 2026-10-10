# AGENTS.md

## Architecture

### VenvManager

`VenvManager` (`src/vvm/manager.py`) is a thin composition/dispatch facade, not
a place where features are built:

- It owns the resolved `Config` and the path it was loaded from (`config_path`),
  plus a registry of action classes.
- It is constructed with a list of action classes (`actions`, defaulting to
  `DEFAULT_ACTIONS`) and registers each under a command name derived from the
  action's **module name** (e.g. `vvm.actions.detect` -> `detect`).
- `run(command, **kwargs)` looks the action up, delegates to
  `action.build(self.config, **kwargs)`, and calls `.run()` on the result,
  returning its exit code.
- It does **not** construct detectors, classifiers, matchers, linkers or any
  other collaborator for the actions.

Adding a new command means adding an action class to `DEFAULT_ACTIONS`; no
manager logic changes are needed.

### Actions

Every feature is a self-contained action class living in its own module under
`src/vvm/actions/`:

- Each action subclasses the shared `Action` base (`src/vvm/actions/base.py`), an
  `ABC` that provides the `out` stream and declares `run(self) -> int`.
- Each action exposes a **`@classmethod build(...)` factory** that initializes
  all of its own dependencies and returns a fully-wired action instance,
  e.g. `DetectAction.build`, `BestAction.build`, `UnlinkAction.build`,
  `ConfigAction.build`. Actions create their collaborators directly inside
  `build` (matchers, linkers, readers, the detector, ...).
- The factory signature is `build(cls, config: Config, *, ...) -> Self`; the
  manager always passes the `Config` positionally, and command-specific options
  (plus `out`) are keyword-only.
- Action modules **never import `VenvManager`** and never receive it. This keeps
  the dependency direction one-way (`manager -> action -> domain services`) and
  avoids circular imports.
- Actions are exported from `src/vvm/actions/__init__.py`, and the CLI
  (`src/vvm/cli.py`) dispatches through `VenvManager.run(...)`.

Shared assembly that several actions need is extracted into the relevant lower
layer, not the manager, e.g. `build_detector(config, directory, *, use_cache)`
in `src/vvm/detection/factory.py`.
