# Open in Pandas

![Usage](Assets/usage.gif)

Open a `.csv`, `.xlsx`, `.json`, `.c3d`, or `.h5` file in an interactive Python session from the command line or a Windows Explorer context menu.

## Setup

Install [`uv`](https://docs.astral.sh/uv/) and sync the project dependencies:

```bash
uv sync
```

## Usage

Open a file directly:

```bash
uv run oi path/to/file.csv
```

This opens an interactive session with:

- `df` for `.csv` and `.xlsx`
- `data` for `.json` and `.h5`
- `data`, `df_points`, `df_analog`, `points_rate`, and `analog_rate` for `.c3d`
- `file_path` for the selected file path

`plot()` enables hover labels for line plots and `plt` is available in the session.

## Windows Context Menu

Install the Explorer entry:

```bash
uv run oi install-menu
```

That command uses the repository's `icon.ico` automatically when it is present. You can override it with a custom icon:

```bash
uv run oi install-menu --icon "C:\path\to\custom.ico"
```

Remove it later:

```bash
uv run oi uninstall-menu
```

The menu is installed through `context-menu` and writes to the current user's registry hive, so manual Registry Editor steps are no longer required.
On Windows 11, the entry may appear under `Show more options`.
If you update the project after installing the menu, run `uv run oi uninstall-menu` and then `uv run oi install-menu` to refresh the registered command.
