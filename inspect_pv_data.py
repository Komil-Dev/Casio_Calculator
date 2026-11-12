
from pathlib import Path
from scipy.io import loadmat
import numpy as np

# 1. Find the project folder
project_folder = Path(__file__).resolve().parent

print("Project folder:", project_folder)

# 2. Find MATLAB files
mat_files = list(project_folder.rglob("*.mat"))

print("\nMATLAB files found:")

for file in mat_files:
    print(file)

# 3. Check whether a file exists
if not mat_files:
    print("\nERROR: No .mat file found!")
else:
    # Select the first MATLAB file found
    mat_file = mat_files[0]

    print("\nLoading:", mat_file.name)

    try:
        data = loadmat(mat_file)

        print("\nVariables in dataset:")

        for key, value in data.items():

            if not key.startswith("__"):

                print("\nVariable:", key)
                print("Type:", type(value))
                print("Shape:", getattr(value, "shape", "N/A"))

                if isinstance(value, np.ndarray):
                    print("First values:")
                    print(value.flatten()[:10])

    except NotImplementedError:
        print("MATLAB v7.3 detected.")
        print("We need to inspect it using h5py.")
