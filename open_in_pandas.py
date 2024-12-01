import pandas as pd
import json
import sys
import os
import ezc3d

# Even though we don't use matplotlib here, it is nice to have it
# for when you want to plot the data. So when you plot with
# `df.plot()`, you can use `plt.show()` to show the plot.
import matplotlib.pyplot as plt


def c3d_to_dict(path):
    c3d = ezc3d.c3d(path)

    header = c3d["header"]
    header_dict = {key: header[key] for key in header.keys()}

    parameters = c3d["parameters"]
    param_dict = {}
    for group, params in parameters.items():
        param_dict[group] = {}
        for param, details in params.items():
            # This mostly just skips the metadata for the header
            if param[:2] == "__":
                continue
            param_dict[group][param] = {
                "description": details["description"],
                "values": details.get("value"),
            }
        c3d_data = c3d["data"]
        points = c3d_data["points"]
        analog = c3d_data["analogs"]
        data_dict = {"points": points, "analogs": analog}

    return {
        "header": header_dict,
        "parameters": param_dict,
        "data": data_dict,
    }


def reshape_points_data(input_array):
    if input_array.shape[0] != 4:
        raise ValueError(
            "The first dimension of the input array must be 4 (representing XYZ1)."
        )
    _, _, num_rows = input_array.shape
    array_transposed = input_array.transpose(2, 1, 0)
    array_no_ones = array_transposed[:, :, :-1]
    array_reshaped = array_no_ones.reshape(num_rows, -1)
    return array_reshaped


def c3d_to_df(path):
    c3d_data_dict = c3d_to_dict(path)
    points_names = c3d_data_dict["parameters"]["POINT"]["LABELS"]["values"]
    point_axis_names = [
        f"{label}{axis}" for label in points_names for axis in ["_x", "_y", "_z"]
    ]
    analog_names = c3d_data_dict["parameters"]["ANALOG"]["LABELS"]["values"]
    analog_data = c3d_data_dict["data"]["analogs"][0].T
    analog_df = pd.DataFrame(analog_data, columns=analog_names)
    points_data = reshape_points_data(c3d_data_dict["data"]["points"])
    points_df = pd.DataFrame(
        points_data,
        columns=point_axis_names,
    )

    return c3d_data_dict, points_df, analog_df


if len(sys.argv) != 2:
    print("Usage: open_in_pandas.py <file_path>")
else:
    file_path = sys.argv[1]
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == ".csv":
            df = pd.read_csv(file_path)
            print(f"CSV file '{file_path}' loaded into DataFrame 'df'.")
        elif file_ext == ".xlsx":
            df = pd.read_excel(file_path)
            print(f"Excel file '{file_path}' loaded into DataFrame 'df'.")
        elif file_ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"JSON file '{file_path}' loaded into dictionary 'data'.")
        elif file_ext == ".c3d":
            data, df_points, df_analog = c3d_to_df(file_path)
            points_rate = data["header"]["points"]["frame_rate"]
            analog_rate = data["header"]["analogs"]["frame_rate"]
            print(
                f"""C3D file '{file_path}' loaded into dictionary 'data'.\nDataframes of the data: 'df_points' and 'df_analog'.\npoints_rate = {points_rate} and analog_rate = {analog_rate}."""
            )
        else:
            print(f"Unsupported file type: {file_ext}")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
