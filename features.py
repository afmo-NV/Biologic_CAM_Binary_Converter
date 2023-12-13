import pandas as pd
import numpy as np
import logging


class Features:
    def __init__(self, input_key):
        self.input_key = input_key

    def extract(self, df, mass=1.0):
        # Create an empty dictionary
        features = {}

        # Extract the initial charge capacity in mAh/g (The default mass is 1.0)
        features = self.extract_initial_charge_capacity(df, features, mass)

        # Extract the initial discharge capacity in mAh/g (The default mass is 1.0)
        features = self.extract_initial_discharge_capacity(df, features, mass)

        # Here the cycles can be modified to extract the capacities of selected cycles.
        # By default, the cycles are an array from 2 to 50
        features = self.extract_capacities_for_cycles(df, features, cycles=np.arange(2, 51))

        # Extract the difference between consecutive discharge capacities
        features = self.extract_discharge_capacity_difference(df, features, cycles=np.arange(2, 51))

        # Extract the open circuit potential for formation and formation + capacity check experiments.
        # This is not used for cycle life experiments
        features = self.extract_ocv(df, features)

        # Convert all the features to a dataframe
        feature_df = pd.DataFrame(features, index=[0])

        return feature_df

    def extract_ocv(self, df, features):
        """
        :param df: cloud format dataframe
        :param features: a dictionary
        :returns: a dictionary with the value of the open circuit potential
        """
        logging.debug("FEATURES. Extracting OCV")
        # Finds the index of last value of the REST step for cycle 1
        idx = np.logical_and(df["step_type"] == "REST", df["step_number"] == 0, df["cycle"] == 1)

        # Using the index from idx, extracts the voltage value
        open_circuit_potential = round(df[idx]["voltage"].iloc[-1], 3)

        features["Open Circuit Potential (V)"] = open_circuit_potential

        logging.debug("FEATURES. OCV extracted successfully")

        return features

    def extract_initial_charge_capacity(self, df, features, mass=1.0):
        """
        :param df: cloud format dataframe
        :param features: dictionary
        :param mass: mass of the active material extracted from the filename. The default value is 1.0
        :return: a dictionary with the values of
                                            initial charge capacity
                                            initial specific charge capacity
        """
        logging.debug("FEATURES. Extracting initial charge capacity")

        # Find the index of the charge step of the first cycle
        idx = np.logical_and(df["step_type"] == "CHARGE", df["cycle"] == 1)

        # Using the previous index, find the maximum value of capacity which corresponds to
        # the initial charge capacity. This value is in A.h
        initial_charge_capacity = df[idx]["step_amp_hours"].max()

        # Converts the initial charge capacity to specific charge capacity using the mass
        # of the active material extracted from the filename. If the mass cannot be extracted
        # from the filename, it sets the mass value to 1.0. The units are mAh/g
        initial_specific_charge_capacity = initial_charge_capacity * 1000 / mass

        features["Initial Charge Capacity (mAh)"] = round(initial_charge_capacity * 1000, 3)

        features["Initial Specific Charge Capacity (mAh/g) "] = round(initial_specific_charge_capacity, 1)

        logging.debug(
            f"FEATURES. Initial charge capacity extract successfully. Initial specific charge capacity calculated "
            f"with mass {mass}")

        return features

    def extract_initial_discharge_capacity(self, df, features, mass=1.0):
        """

        :param df: cloud format dataframe
        :param features: dictionary
        :param mass: mass of the active material extracted from the filename. The default value is 1.0
        :return: a dictionary with the values of
                                            initial discharge capacity
                                            initial specific discharge capacity
        """
        logging.debug("FEATURES. Extracting initial discharge capacity")

        # Find the index of the discharge step of the first cycle
        idx = np.logical_and(df["step_type"] == "DISCHARGE", df["cycle"] == 1)

        # Using the previous index, find the maximum value of capacity which corresponds to
        # the initial discharge capacity. This value is in A.h
        initial_discharge_capacity = df[idx]["step_amp_hours"].max()

        # Converts the initial discharge capacity to specific discharge capacity using the mass
        # of the active material extracted from the filename. If the mass cannot be extracted
        # from the filename, it sets the mass value to 1.0. The units are mAh/g
        initial_specific_discharge_capacity = initial_discharge_capacity * 1000 / mass

        features["Initial Discharge Capacity (mAh)"] = round(initial_discharge_capacity * 1000, 3)

        features["Initial Specific Discharge capacity (mAh/g)"] = round(initial_specific_discharge_capacity, 1)

        logging.debug(
            f"FEATURES. Initial discharge capacity extract successfully. Initial specific discharge capacity "
            f"calculated with mass {mass}")
        return features

    def extract_initial_coulombic_efficiency(self, df, features):
        """
        This function calculates the coulombic efficiency in formation and formation + capacity check
        experiments.

        :param df: cloud format dataframe
        :param features: dictionary
        :return: a dictionary with the values of the initial coulombic efficiency
        """

        logging.debug("FEATURES. Extracting initial coulombic efficiency")

        # Takes the value of the initial discharge capacity from the features dictionary
        initial_discharge_capacity = features["Initial Discharge Capacity (mAh)"]

        # Takes the value of the initial charge capacity from the features dictionary
        initial_charge_capacity = features["Initial Charge Capacity (mAh)"]

        # Calculates the Coulombic efficiency
        initial_coulombic_efficiency = round((initial_discharge_capacity / initial_charge_capacity) * 100, 1)

        features["Initial Coulombic Efficiency (%)"] = initial_coulombic_efficiency

        logging.debug("FEATURES. Initial coulombic efficiency extracted successfully")

        return features

    def extract_capacities_for_cycles(self, df, features, cycles):
        """

        :param df: cloud format dataframe
        :param features: dictionary
        :param cycles: a numpy array containing the cycles for which we want to extract the
        charge, discharge capacities and state of health (SoH).
        :return:
        """
        logging.debug("FEATURES. Extracting discharge capacities for all cycles")

        df_discharge = (
            df[df["step_type"] == "DISCHARGE"]
            .groupby(["cycle"])
            .agg(
                discharge_step_amp_hours=("step_amp_hours", "max"),
            )
        ).reset_index()

        df_discharge = df_discharge[df_discharge["cycle"] > 1]

        initial_discharge_capacity = features["Initial Discharge Capacity (mAh)"]

        for cycle in cycles:
            idx_discharge = df_discharge["cycle"] == cycle
            discharge_capacity = df_discharge[idx_discharge]["discharge_step_amp_hours"].max()
            # features[f"soh_{cycle}"] = round(discharge_capacity / (initial_discharge_capacity/1000),3)
            features[f"Retention Cycle {cycle} (%)"] = round(
                (discharge_capacity * 100 / (initial_discharge_capacity / 1000)), 1)

        logging.debug("FEATURES. Discharge capacities extracted successfully for all cycles")

        return features

    def extract_discharge_capacity_difference(self, df, features, cycles):
        logging.debug("FEATURES. Extracting discharge capacities difference for all cycles")

        # Find the index of the discharge step of the first cycle
        df_discharge = (
            df[df["step_type"] == "DISCHARGE"]
            .groupby(["cycle"])
            .agg(
                discharge_step_amp_hours=("step_amp_hours", "max"),
            )
        ).reset_index()

        df_discharge = df_discharge[df_discharge["cycle"] > 1]

        prev_discharge_capacity = df_discharge[df_discharge["cycle"] == 2]["discharge_step_amp_hours"].max()

        for cycle in cycles:
            idx_discharge = df_discharge["cycle"] == cycle
            discharge_capacity = df_discharge.loc[idx_discharge, "discharge_step_amp_hours"].max()
            discharge_capacity_difference = (discharge_capacity - prev_discharge_capacity)/ (prev_discharge_capacity/100)
            features[f"Retention Difference for {cycle} (%)"] = round(discharge_capacity_difference,3)
            prev_discharge_capacity = discharge_capacity  # Update for the next iteration

        return features



