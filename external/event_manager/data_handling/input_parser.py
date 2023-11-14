import pandas as pd

# TODO: rename parse standarddatafev xlsx input
def parse_standard_xlsx_input(file_path):
    """
    This method parses the standard datafev xlsx input and generates the required input for simulation object creation.

    Parameters
    ----------
    file_path : str
        Input file path.

    Returns
    -------
    clusters_dict
    capacities_dict
    fleet
    tou_tariff

    """

    input_file = pd.ExcelFile(file_path)

    # Create dictionaries for Cluster and Capacity inputs
    clusters_dict = {}
    capacities_dict = {}

    # Loop through the sheet names
    for sheet_name in input_file.sheet_names:
        if sheet_name.startswith('Cluster'):
            # Extract the key (the number after 'Cluster')
            key = str(sheet_name.replace('Cluster', ''))
            # Read the sheet into a DataFrame
            df = input_file.parse(sheet_name)
            clusters_dict[key] = df
        elif sheet_name.startswith('Capacity'):
            # Extract the key (the number after 'Capacity')
            key = str(sheet_name.replace('Capacity', ''))
            # Read the sheet into a DataFrame
            df = input_file.parse(sheet_name)
            capacities_dict[key] = df
    
    service_fleet = pd.read_excel(input_file, "ServiceFleet")
    fleet = pd.read_excel(input_file, "Fleet")

    input_price = pd.read_excel(input_file, "Price")
    price_t_steps = input_price["TimeStep"].round("S")
    tou_tariff = pd.Series(input_price["Price (per/kWh)"].values, index=price_t_steps)

    return clusters_dict, capacities_dict, service_fleet, fleet, tou_tariff
