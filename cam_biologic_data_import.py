import os
from biologic_reader import BiologicReader
from pathlib import Path
import sys
import logging
import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog


def get_protocol_type(filename):
    """
    This function identifies the protocol type from the filename.

    :param filename: str, the name of the file.
    :return: str, the protocol type.
    """
    try:
        if 'OCV' in filename:
            print(filename + ' corresponds to open circuit potential which is not supported. Select another file')
            sys.exit(1)
        elif 'Life' in filename:
            return 'CL'
        elif 'Formation-Capacity-Check' in filename:
            return 'FC'
        elif 'Formation' in filename:
            return 'F'
        else:
            return input('I cannot identify the protocol type from the filename. Please enter F for Formation, FC'
                         ' for Formation + Capacity Check or CL for cycle life')
    except Exception as e:
        logging.error(f"CAM-BIOLOGIC-DATA-IMPORT. An error occurred while identifying protocol type: {e}")
        raise


def get_mpr_files(data_folder):
    """
    This function gets all the mpr files in a folder and its subfolders.

    :param data_folder: str, the path of the folder.
    :return: list, a list of the mpr files.
    """
    try:
        mpr_file_list = []
        for root, dirs, files in os.walk(data_folder):
            for filename in files:
                if filename.endswith(".mpr"):
                    mpr_file_list.append(os.path.join(root, filename))
        return mpr_file_list

    except Exception as e:
        logging.error(f"CAM-BIOLOGIC-DATA-IMPORT. An error occurred while getting mpr files: {e}")
        raise


def extract_mass_from_filename(filename):
    """
    This function extracts the mass from the filename.

    :param filename: str, the name of the file.
    :return: float, the mass of the active material.
    """
    try:
        logging.debug("CAM-BIOLOGIC-DATA-IMPORT. Extracting mass from filename")
        # Extract mass from filenames
        mass = float((filename.split('_'))[1])
    except:
        # If there is a problem, set mass = 1
        mass = 1.0
    logging.debug(f"CAM-BIOLOGIC-DATA-IMPORT. Mass extracted succesfully from {filename}")
    return mass


def filter_mpr_files(mpr_files, lower_limit_kb, upper_limit_kb):
    """
    This function filters out mpr files from a list which are within a given size range.

    Args:
        mpr_files (list): List of file paths to filter.
        lower_limit_kb (int): Lower size limit in kilobytes. Files lighter than this will be ignored.
        upper_limit_kb (int): Upper size limit in kilobytes. Files heavier than this will be ignored.

    Returns:
        list: A list of paths for each file that is within the specified size range.
    """
    filtered_files = []
    lower_limit_bytes = lower_limit_kb * 1024
    upper_limit_bytes = upper_limit_kb * 1024
    for file in mpr_files:
        file_size = os.path.getsize(file)
        if lower_limit_bytes <= file_size < upper_limit_bytes:
            filtered_files.append(Path(file))
    return filtered_files


def convert_file_to_cloud(mpr_file_path):
    """
    This function converts an mpr file at the provided path to the NV cloud format DataFrame
    using the BiologicReader. If an error occurs while reading or converting the file,
    the function will return None.

    Args:
        mpr_file_path (str): The file path to process.

    Returns:
        DataFrame: The Biologic data converted to cloud format, or None if an error occurred.
    """
    try:
        file_path = Path(mpr_file_path)
        logging.debug(f"CAM-BIOLOGIC-DATA-IMPORT. Converting {file_path.stem} to cloud format")
        # create an instance of the BiologicReader class
        reader = BiologicReader()
        biologic_data = reader.read(file_path)
        cloud_data = reader.convert_to_cloud(biologic_data)
        logging.debug(f"{file_path.stem} converted succesfully to cloud format")
        return cloud_data
    except Exception as e:
        print(f"CAM-BIOLOGIC-DATA-IMPORT. An error occurred while processing file {mpr_file_path}: {e}")
        return None


def create_dataframe(dictionary):
    """
    Create a dataframe from the features dictionary.

    Args:
        dict: The dictionary of features.

    Returns:
        DataFrame: The created dataframe.
    """
    return pd.DataFrame(dictionary, index=[0])


def process_filenames(filename):
    """
        This function takes a single filename or a list of filenames and returns
        a joined match of groups in the filename(s) based on the defined regex pattern.

        Args:
            filename (str or list): A single filename or a list of filenames.

        Returns:
            str or list: A string for a single filename input or a list of strings
                         for a list of filenames input. Each string contains the
                         joined match of groups in the filename. If the pattern does
                         not match the filename, the function returns None.
        """

    pattern = r'^(QCL-\d+|Lims-\d+)(.*?)-(Cycle-Life|Formation-Capacity-Check|Formation)'
    separator = '-'

    # Check if input is a list of filenames
    logging.debug(f"CAM-BIOLOGIC-DATA-IMPORT. Processing {filename} filename")
    if isinstance(filename, list):
        return [separator.join(re.match(pattern, f).groups()) for f in filename if re.match(pattern, f) is not None]
    else:
        match = re.match(pattern, filename)
        if match is not None:
            return match[0]
        else:
            logging.error(f"CAM-BIOLOGIC-DATA-IMPORT. No sample ID found for {filename}")
            return None


def process_filenames_CC(filename):
    """
        This function takes a single filename or a list of filenames and returns
        a joined match of groups in the filename(s) based on the defined regex pattern.

        Args:
            filename (str or list): A single filename or a list of filenames.

        Returns:
            str or list: A string for a single filename input or a list of strings
                         for a list of filenames input. Each string contains the
                         joined match of groups in the filename. If the pattern does
                         not match the filename, the function returns None.
        """

    pattern = r'^(.*?)(CC-\d{1,2})'
    separator = '-'

    # Check if input is a list of filenames
    logging.debug(f"CAM-BIOLOGIC-DATA-IMPORT. Processing {filename} filename")
    if isinstance(filename, list):
        return [separator.join(re.match(pattern, f).groups()) for f in filename if re.match(pattern, f) is not None]
    else:
        match = re.match(pattern, filename)
        if match is not None:
            return match[0]
        else:
            logging.error(f"CAM-BIOLOGIC-DATA-IMPORT. No sample ID found for {filename}")
            return None


def get_file_path(default_folder):
    """
    Open a file dialog and return the selected file path(s).

    Returns:
        str or list: The file path of the selected file(s).
    """
    logging.debug(f"CAM-BIOLOGIC-DATA-IMPORT. Extracting path for mpr files")
    print("Select the files to analyse")
    root = tk.Tk()  # Create a new Tk root
    root.withdraw()  # Hide the main window

    # Open the file selection dialog
    mpr_files = filedialog.askopenfilenames(initialdir=default_folder)

    # Check if the user cancelled the file dialog
    if not mpr_files:
        return None

    # Check if multiple files are selected
    if len(mpr_files) > 1:
        return list(mpr_files)  # return a list of paths
    else:
        return mpr_files[0]  # return a single path as string


def filter_OCV_files(input_filenames):
    """
        Filters out any filenames containing the character 'OCV'.
        If the input is a single filename, it returns the string if it doesn't contain 'OCV', otherwise returns None.
        If the input is a list of filenames, it returns a new list containing only the filenames that don't contain 'OCV'.

        :param input_filenames: A single filenames or a list of filenames to be filtered.
        :return: A single filename or a list of filenames without the substring 'OCV', depending on the input type.
        """
    logging.debug("CAM-BIOLOGIC-DATA-IMPORT. Removing OCV files")
    if isinstance(input_filenames, str):
        return input_filenames if 'OCV' not in input_filenames else None
    elif isinstance(input_filenames, list):
        return [s for s in input_filenames if 'OCV' not in s]
    else:
        raise TypeError("Problem with the filename in the filter_OCV_files function")
