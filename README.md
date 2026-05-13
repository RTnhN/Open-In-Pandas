# Open in Pandas  

![Usage](Assets/usage.gif)

This is a quick way that you can add a right click context to open a csv, xlsx, json, c3d, or h5 file in an interactive python instance. Note that the name is kind of a misnomer since json files or h5 files don't actually use pandas. Json loads as a dictionary as default, and h5 loads with its unique format. I will probably add other files as I go along.

## Prerequisites

- Python installed and added to PATH
- Pandas library installed (`pip install pandas matplotlib ezc3d h5py` and others). You can also use the requirements.txt file to install all the dependencies.
- Administrative access to modify the Windows Registry

## Steps

First, download the repo, and then edit the registry:

1. Open the Registry Editor:
   - Press `Win + R`, type `regedit`, and press Enter.

2. Navigate to the following key:
`HKEY_CLASSES_ROOT\*\shell`

3. Create a new key for the context menu:
- Right-click on `shell`, select `New` -> `Key`, and name it `Open in Pandas`.
- In the `Open in Pandas` key, set the default value to `Open in Pandas`.

4. Set the icon for the context menu entry:
- Right-click on the `Open in Pandas` key, select `New` -> `String Value`, and name it `Icon`.
- Set the value of `Icon` to:
  ```
  C:\path\to\icon\open_in_pandas.ico
  ```

5. Set the command for the context menu entry:
- Right-click on `Open in Pandas`, select `New` -> `Key`, and name it `command`.
- In the `command` key, set the default value to:
  ```plaintext
  "C:\path\to\your\bat\file\open_in_pandas.bat" "%1"
  ```

Note that you might want to to use a different python interpreter, so you can edit the .bat file to point to a specific interpreter with either directly putting the path to the interpreter. Or you can also just directly add the python interpreter to your registry with something like the string below which bypasses the bat file directly, but I like the flexibility of changing the bat file rather than digging into the registry.  
```
 "C:\Path\To\Python\python.exe" -i "C:\path\to\your\script\open_in_pandas.py" "%1"
```

Since I use this for lightweight and quick analysis of files (sort of in between excel and writing a real script), I have not looked into getting this to work with Anaconda environments. If you need that, then you probably should write a real script. 

  




