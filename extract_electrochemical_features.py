import features
import numpy as np
import logging


def extract_formation_features(filename, cloud_data_df, mass=1.0):
    """
    Extract features from the cloud data frame for formation and formation +
    capacity check experiments.

    Args:
        filename (str): The name of the file.
        cloud_data_df (DataFrame): The cloud data frame.

    Returns:
        dict: The dictionary of extracted features.
    """
    logging.debug(f"EXTRACT-ELECTROCHEMICAL-FEATURES. Extracting formation features for {filename}")

    features_dict = {}
    features_obj = features.Features(filename)

    features_obj.extract_ocv(cloud_data_df, features_dict)
    features_obj.extract_initial_charge_capacity(cloud_data_df, features_dict, mass)
    features_obj.extract_initial_discharge_capacity(cloud_data_df, features_dict, mass)
    features_obj.extract_initial_coulombic_efficiency(cloud_data_df, features_dict)

    logging.debug(f"EXTRACT-ELECTROCHEMICAL-FEATURES. Formation features extracted successfully for {filename}")

    return features_dict


def extract_qc_cycle_life_features(filename, cloud_data_df, mass):
    """
        Extract a summary of features from the cloud data frame for cycle life experiments.

        Args:
            filename (str): The name of the file.
            cloud_data_df (DataFrame): The cloud data frame.

        Returns:
            dict: The dictionary of extracted features.
        """

    logging.debug(f"EXTRACT-ELECTROCHEMICAL-FEATURES. Extracting QC cycle life features for {filename}")

    features_dict = {}
    features_obj = features.Features(filename)

    features_obj.extract_initial_charge_capacity(cloud_data_df, features_dict, mass)
    features_obj.extract_initial_discharge_capacity(cloud_data_df, features_dict, mass)
    features_obj.extract_capacities_for_cycles(cloud_data_df, features_dict, np.array([50]))
    # features_obj.extract_capacities_for_cycles(cloud_data_df, features_dict, np.array([2, 5, 10, 25, 50]))

    logging.debug(f"EXTRACT-ELECTROCHEMICAL-FEATURES. QC cycle life features extracted successfully for {filename}")
    return features_dict


def extract_all_cycle_life_features(filename, cloud_data_df, mass):
    """
        Extract all features from the cloud data frame for cycle life experiments.

        Args:
            filename (str): The name of the file.
            cloud_data_df (DataFrame): The cloud data frame.

        Returns:
            dict: The dictionary of extracted features.
        """
    logging.debug(f"EXTRACT-ELECTROCHEMICAL-FEATURES. Extracting all cycle life data for {filename}")

    features_dict = {}
    features_obj = features.Features(filename)

    features_obj.extract_initial_charge_capacity(cloud_data_df, features_dict, mass)
    features_obj.extract_initial_discharge_capacity(cloud_data_df, features_dict, mass)
    features_obj.extract_capacities_for_cycles(cloud_data_df, features_dict, np.arange(2, 51))
    features_obj.extract_discharge_capacity_difference(cloud_data_df, features_dict, np.arange(2, 51))

    logging.debug(f"EXTRACT-ELECTROCHEMICAL-FEATURES. All cycle life features extracted successfully for {filename}")

    return features_dict
