# SAOS-10.x
FlexE Configurator

This script is designed to configure FlexE devices. It supports various FlexE devices including 5130, 5164, 5166, and 5184. The script will prompt the user for the device type, number of client ports, and other necessary configurations, then generate the appropriate configuration files.


Prerequisites


Python 3.x

ncclient library for NETCONF operations


Installation


Clone the repository or download the script.

Ensure you have Python 3 installed.

Install the ncclient library using pip:


pip install ncclient

Usage


Run the script:


python flexe_configurator.py


Follow the prompts to configure your FlexE device:



Enter the device type (5130, 5164, 5166, 5184).

Enter the number of client ports.

Enter the number of FlexE ports to configure.

Enter the NNI port numbers and their speeds.

Specify if you plan on using FlexE protection.

If using protection, enter the number of clients to be protected and the protection ports.



The script will generate the configuration files and save them in the Configurations folder.


Functions


get_valid_speed(device_type): Prompts the user to enter a valid port speed based on the device type.

get_flexe_ports(client_ports, max_nni_ports, device_type): Prompts the user to enter the number of FlexE ports and validates the NNI ports.

get_flexe_device_info(): Prompts the user to enter the device type and returns the device information.

get_NNI_ports(num_flexe_ports, device_type): Prompts the user to enter the NNI ports based on the device type.

get_client_ports(max_client_ports): Prompts the user to enter the number of client ports.

get_flexe_protection_info(max_client_ports, device_type): Prompts the user to enter the protection information if FlexE protection is used.

validate_capacity(num_client_ports, nni_ports_with_speeds): Validates the capacity based on the number of client ports and NNI port speeds.

flexe_no_protection(num_client_ports, nni_ports_with_speeds): Generates the configuration for FlexE without protection.

send_to_file(configuration, use_protection, num_protected_clients, end): Saves the configuration to a file in the Configurations folder.

send_removal_to_file(removal_config, num_protected_clients): Saves the removal configuration to a file in the Configurations folder.

send_to_device(configuration, host, port, username, password): Sends the configuration to the device via NETCONF.

flexe_protection(nni_ports_with_speeds, num_protected_clients, protection_ports, end): Generates the configuration for FlexE with protection.

generate_removal_config(num_protected_clients): Generates the removal configuration.


Example

python flexe_configurator.py

Follow the prompts and the script will generate the necessary configuration files based on your inputs.



Author

William Szwarc
