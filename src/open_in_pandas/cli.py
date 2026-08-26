from __future__ import annotations

import argparse
import code
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

MENU_LABEL = "Open in Pandas"
SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".json", ".c3d", ".h5")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ICON_PATH = PROJECT_ROOT / "icon.ico"


class OpenInPandasError(Exception):
    """Base exception for CLI failures."""


class UnsupportedFileTypeError(OpenInPandasError):
    """Raised when a selected file extension is not supported."""


def _missing_dependency(package_name: str, exc: Exception) -> OpenInPandasError:
    return OpenInPandasError(
        f"Missing dependency '{package_name}'. Run `uv sync` to install project dependencies."
    )


def _load_plot_modules() -> tuple[Any, Any]:
    try:
        import matplotlib.pyplot as plt
        import mplcursors
    except ImportError as exc:
        raise _missing_dependency("matplotlib mplcursors", exc)
    return plt, mplcursors


def enable_hover() -> Any:
    plt, mplcursors = _load_plot_modules()
    cursor = mplcursors.cursor(plt.gca().lines, hover=True)

    @cursor.connect("add")
    def on_add(sel: Any) -> None:
        x, y = sel.target
        label = sel.artist.get_label()
        sel.annotation.set(text=f"{label}\nIndex: {x:g}\nValue: {y:g}")

    return cursor


def plot() -> None:
    plt, _ = _load_plot_modules()
    enable_hover()
    plt.show()


def c3d_to_dict(path: Path) -> dict[str, Any]:
    try:
        import ezc3d
    except ImportError as exc:
        raise _missing_dependency("ezc3d", exc)

    c3d = ezc3d.c3d(str(path))
    header = c3d["header"]
    header_dict = {key: header[key] for key in header.keys()}

    parameters = c3d["parameters"]
    param_dict: dict[str, dict[str, dict[str, Any]]] = {}
    for group, params in parameters.items():
        param_dict[group] = {}
        for param, details in params.items():
            if param.startswith("__"):
                continue
            param_dict[group][param] = {
                "description": details["description"],
                "values": details.get("value"),
            }

    c3d_data = c3d["data"]
    data_dict = {
        "points": c3d_data["points"],
        "analogs": c3d_data["analogs"],
    }
    return {
        "header": header_dict,
        "parameters": param_dict,
        "data": data_dict,
    }


def reshape_points_data(input_array: Any) -> Any:
    if input_array.shape[0] != 4:
        raise ValueError(
            "The first dimension of the input array must be 4 (representing XYZ1)."
        )

    _, _, num_rows = input_array.shape
    array_transposed = input_array.transpose(2, 1, 0)
    array_no_ones = array_transposed[:, :, :-1]
    return array_no_ones.reshape(num_rows, -1)


def c3d_to_df(path: Path) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    c3d_data_dict = c3d_to_dict(path)
    points_names = c3d_data_dict["parameters"]["POINT"]["LABELS"]["values"]
    point_axis_names = [
        f"{label}{axis}" for label in points_names for axis in ("_x", "_y", "_z")
    ]
    analog_names = c3d_data_dict["parameters"]["ANALOG"]["LABELS"]["values"]
    analog_data = c3d_data_dict["data"]["analogs"][0].T
    analog_df = pd.DataFrame(analog_data, columns=analog_names)
    points_data = reshape_points_data(c3d_data_dict["data"]["points"])
    points_df = pd.DataFrame(points_data, columns=point_axis_names)
    return c3d_data_dict, points_df, analog_df


def load_csv(path: Path) -> tuple[dict[str, Any], str]:
    return {"df": pd.read_csv(path)}, f"CSV file '{path}' loaded into DataFrame `df`."


def load_excel(path: Path) -> tuple[dict[str, Any], str]:
    return {"df": pd.read_excel(path)}, f"Excel file '{path}' loaded into DataFrame `df`."


def load_json(path: Path) -> tuple[dict[str, Any], str]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {"data": data}, f"JSON file '{path}' loaded into dictionary `data`."


def load_c3d(path: Path) -> tuple[dict[str, Any], str]:
    data, df_points, df_analog = c3d_to_df(path)
    points_rate = data["header"]["points"]["frame_rate"]
    analog_rate = data["header"]["analogs"]["frame_rate"]
    namespace = {
        "data": data,
        "df_points": df_points,
        "df_analog": df_analog,
        "points_rate": points_rate,
        "analog_rate": analog_rate,
    }
    banner = (
        f"C3D file '{path}' loaded into `data`.\n"
        "DataFrames: `df_points` and `df_analog`.\n"
        f"Sampling rates: points_rate={points_rate}, analog_rate={analog_rate}."
    )
    return namespace, banner


def load_hdf5(path: Path) -> tuple[dict[str, Any], str]:
    try:
        import h5py
    except ImportError as exc:
        raise _missing_dependency("h5py", exc)

    data = h5py.File(path, "r")
    return {"data": data}, f"HDF5 file '{path}' loaded into `data`. Explore with `data.keys()`."


LOADERS = {
    ".csv": load_csv,
    ".xlsx": load_excel,
    ".json": load_json,
    ".c3d": load_c3d,
    ".h5": load_hdf5,
}


def build_namespace(path: Path) -> tuple[dict[str, Any], str]:
    extension = path.suffix.lower()
    if extension not in LOADERS:
        supported = ", ".join(SUPPORTED_EXTENSIONS)
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or '<none>'}'. Supported extensions: {supported}."
        )

    namespace, banner = LOADERS[extension](path)
    namespace.update(
        {
            "file_path": str(path),
            "pd": pd,
            "plot": plot,
        }
    )

    try:
        plt, _ = _load_plot_modules()
    except OpenInPandasError:
        pass
    else:
        namespace["plt"] = plt
        banner += "\n`plot()` provides hover cursor labels for line plots."

    banner += "\n`file_path` is always available."
    if "plt" not in namespace:
        banner += "\nRun `uv sync` to restore plotting dependencies and enable `plot()` and `plt`."

    return namespace, banner


def embed_shell(namespace: dict[str, Any], banner: str) -> None:
    try:
        from IPython import embed
    except ImportError:
        code.interact(banner=banner, local=namespace)
        return

    embed(
        header=banner,
        user_ns=namespace,
        colors="neutral",
        using="asyncio",
    )


def open_interactive(file_path: str | os.PathLike[str]) -> int:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise OpenInPandasError(f"File not found: {path}")

    namespace, banner = build_namespace(path)
    embed_shell(namespace, banner)
    return 0


def launch_selected_files(selected_paths: list[str], _: str) -> None:
    if not selected_paths:
        raise OpenInPandasError("No file was selected from the context menu.")

    open_interactive(selected_paths[0])


def resolve_icon_path(icon: str | os.PathLike[str] | None) -> str | None:
    if icon is None:
        if DEFAULT_ICON_PATH.exists():
            return str(DEFAULT_ICON_PATH)
        return None

    icon_path = Path(icon).expanduser().resolve()
    if not icon_path.exists():
        raise OpenInPandasError(f"Icon file not found: {icon_path}")
    return str(icon_path)


def install_menu(label: str = MENU_LABEL, icon: str | os.PathLike[str] | None = None) -> int:
    if os.name != "nt":
        raise OpenInPandasError("Context menu installation is only supported on Windows.")

    try:
        from context_menu import menus
    except ImportError as exc:
        raise _missing_dependency("context-menu", exc)

    menu = menus.FastCommand(
        label,
        type="FILES",
        python=launch_selected_files,
        icon_path=resolve_icon_path(icon),
    )
    menu.compile()
    print(f"Installed Windows Explorer menu '{label}'.")
    return 0


def uninstall_menu(label: str = MENU_LABEL) -> int:
    if os.name != "nt":
        raise OpenInPandasError("Context menu removal is only supported on Windows.")

    try:
        from context_menu import menus
    except ImportError as exc:
        raise _missing_dependency("context-menu", exc)

    menus.removeMenu(label, "FILES")
    print(f"Removed Windows Explorer menu '{label}'.")
    return 0


def launch_from_menu(file_path: str) -> int:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise OpenInPandasError(f"File not found: {path}")

    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(
        [sys.executable, "-m", "open_in_pandas", "open", str(path)],
        creationflags=creationflags,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oi",
        description="Open supported data files in an interactive Python session.",
    )
    subparsers = parser.add_subparsers(dest="command")

    open_parser = subparsers.add_parser("open", help="Open a file in an interactive Python session.")
    open_parser.add_argument("file_path", help="Path to a supported file.")

    install_parser = subparsers.add_parser(
        "install-menu",
        help="Install a Windows Explorer context menu entry using context-menu.",
    )
    install_parser.add_argument("--label", default=MENU_LABEL, help="Menu label to install.")
    install_parser.add_argument(
        "--icon",
        help="Optional path to a .ico file. Defaults to the repo's icon.ico when present.",
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall-menu",
        help="Remove the Windows Explorer context menu entry.",
    )
    uninstall_parser.add_argument("--label", default=MENU_LABEL, help="Menu label to remove.")

    launch_parser = subparsers.add_parser(
        "launch",
        help="Open a file in a new Python console window. Intended for menu integration.",
    )
    launch_parser.add_argument("file_path", help="Path to a supported file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    known_commands = {"open", "install-menu", "uninstall-menu", "launch", "-h", "--help"}
    if args_list and args_list[0] not in known_commands:
        args_list.insert(0, "open")

    args = parser.parse_args(args_list)

    try:
        if args.command == "open":
            return open_interactive(args.file_path)
        if args.command == "install-menu":
            return install_menu(args.label, args.icon)
        if args.command == "uninstall-menu":
            return uninstall_menu(args.label)
        if args.command == "launch":
            return launch_from_menu(args.file_path)
    except OpenInPandasError as exc:
        print(exc, file=sys.stderr)
        return 1

    parser.print_help()
    return 0
