from logger_configurator import configure_logging
from cam_biologic_data_import import *
from pathlib import Path
from extract_electrochemical_features import *
import warnings
import logging
import yaml

# Define the path to the base directory where the python files are.
base_directory = '/XXXXX/xxxxxxx'

# Load logger configuration
configure_logging(base_directory)

# Log the start of the program
logging.debug("MAIN. CAM BINARY CONVERTER STARTED")

# Suppress FutureWarnings about frame.append method
warnings.filterwarnings('ignore', category=FutureWarning, message="The frame.append method is deprecated")

# Folder where the exported files will be saved
try:
    logging.debug("MAIN. Getting export folder from directory_config.yaml")
    with open(os.path.join(base_directory, 'directory_config.yaml')) as file:
        doc = yaml.load(file, Loader=yaml.FullLoader)
    export_folder = doc['path_export_folder']
    logging.debug(f"MAIN. Export folder is {export_folder}")
except Exception as e:
    logging.error(f"MAIN. An error occurred while getting export folder: {e}")
    raise

# Open a tkinter interface to get the path of all the files
#mpr_file_path_unfiltered = get_file_path(base_directory)
mpr_file_path_unfiltered = get_file_path('/Users/andresmolina/Documents/')

# Filter to remove all files with OCV in the name
mpr_file_path = filter_OCV_files(mpr_file_path_unfiltered)

# Ensure mpr_file_path is always a list
if not isinstance(mpr_file_path, list):
    mpr_file_path = [mpr_file_path]

# Initialize empty dataframes
qc_sample_summary = pd.DataFrame()
cycle_life_sample_data = pd.DataFrame()
sample_ID_list = []

for path in mpr_file_path:
    try:
        # Extract filename from path
        filename = (Path(path)).stem
    
        logging.debug(f"MAIN. Starting data extraction for filename {filename}")
    
        # Convert to cloud data format
        cloud_data_df = convert_file_to_cloud(path)
    
        # Extract sample ID from filename
        sample_ID = process_filenames_CC(filename)
    
        if sample_ID == None:
            logging.debug(f"MAIN. Sample ID not found in {filename}. Extracting from filename")
            pattern = (re.compile(r'(.*?)-CC'))
            sample_ID = (pattern.findall(filename))[0]
            logging.debug(f"MAIN. Sample ID ID extracted as  {sample_ID}.")
    
        # Extract mass from filename
        mass = extract_mass_from_filename(filename)
    
        # Extract protocol type from filename
        protocol_type = get_protocol_type(filename)
    
        if protocol_type in ['F', 'FC']:
    
            features_dict = extract_formation_features(filename, cloud_data_df, mass)
            qc_cc_summary = create_dataframe(features_dict)
            qc_sample_summary = qc_sample_summary._append(qc_cc_summary)
    
        elif protocol_type == 'CL':
    
            # Features extraction of selected cycles
            features_qc_dict = extract_qc_cycle_life_features(filename, cloud_data_df, mass)
            qc_cc_summary = create_dataframe(features_qc_dict)
            qc_sample_summary = qc_sample_summary._append(qc_cc_summary)
    
            # Features extraction of all cycles
            features_dict = extract_all_cycle_life_features(filename, cloud_data_df, mass)
            cycle_life_data_cc_data = create_dataframe(features_dict)
            cycle_life_sample_data = cycle_life_sample_data._append(cycle_life_data_cc_data)
    
        logging.debug(f"MAIN. Data extraction for {filename} finished")

        # Append sample ID name of files that were correctly processed
        sample_ID_list.append(sample_ID)
    except Exception as e:
        logging.error(f"MAIN. Error processing file {filename}: {e}")
        continue # In case of error, skip to the next file


########################################################################################################################
# Export summary for qc ################################################################################################
########################################################################################################################
# Add sample IDs to qc_sample_summary DataFrame
qc_sample_summary.insert(0, 'Sample IDs', sample_ID_list)
try :
    logging.debug("MAIN. Summarising all results")
    qc_sample_summary.to_excel(os.path.join(export_folder, sample_ID + '_summary.xlsx'), index=False)
except Exception as e:
    logging.error(f"MAIN. An error occurred while exporting summary: {e}")
    raise

########################################################################################################################
# Export all data for cycle life experiments ###########################################################################
########################################################################################################################
# Add sample IDs to cycle_life_sample_data DataFrame
cycle_life_sample_data['Sample IDs'] = sample_ID_list

if not cycle_life_sample_data.empty:
    logging.debug('MAIN. Exporting all data for cycle life experiments')
    with pd.ExcelWriter(os.path.join(export_folder, 'Cycle_Life_All_Data', sample_ID + '_data.xlsx')) as writer:
        # Separate 'Sample ID' column
        sample_id_col = cycle_life_sample_data[['Sample IDs']]

        # Split columns based on keywords, excluding 'Sample ID'
        initial_cols = [col for col in cycle_life_sample_data.columns if 'Initial' in col and col != 'Sample IDs']
        cycle_cols = [col for col in cycle_life_sample_data.columns if 'Cycle' in col and col != 'Sample IDs']
        difference_cols = [col for col in cycle_life_sample_data.columns if 'Difference' in col and col != 'Sample IDs']

        # Concatenate 'Sample ID' column at the beginning of each DataFrame
        df_initial_results = pd.concat([sample_id_col, cycle_life_sample_data[initial_cols]], axis=1)
        df_cycle_results = pd.concat([sample_id_col, cycle_life_sample_data[cycle_cols]], axis=1)
        df_difference_results = pd.concat([sample_id_col, cycle_life_sample_data[difference_cols]], axis=1)

        # Now write to Excel within the with block
        if not df_initial_results.empty:
            df_initial_results.to_excel(writer, sheet_name='Initial Results', index=False)
        if not df_cycle_results.empty:
            df_cycle_results.to_excel(writer, sheet_name='Cycle Results', index=False)
        if not df_difference_results.empty:
            df_difference_results.to_excel(writer, sheet_name='Difference Results', index=False)
else:
    logging.debug(f"MAIN. No cycle life data found for {sample_ID}")

logging.info(
    f'MAIN. Results were successfully extracted from {sample_ID} and were exported to {export_folder}')
logging.debug("MAIN. CAM BINARY CONVERTER FINISHED")

# input("Press Enter to exit.")
sys.exit(1)

