#from ncclient import manager
import os


def get_valid_speed(device_type):
    valid_speeds = {
        "5130": ["100G"],
        "5164": ["100G", "200G"],
        "5166": ["100G", "200G", "400G"],
        "5184": ["100G", "200G", "400G"],
    }
    #Test

    while True:
        speed = input(f"Enter the port speed ({', '.join(valid_speeds[device_type])}): ").strip()
        if speed in valid_speeds[device_type]:
            return speed
        print(f"Invalid speed. Please enter one of the following: {', '.join(valid_speeds[device_type])}.")

def get_flexe_ports(client_ports, max_nni_ports, device_type):
    while True:
        try:
            num_flexe_ports = int(input(f"Enter the number of FlexE ports to configure (1-{max_nni_ports}): "))
            if 1 <= num_flexe_ports <= max_nni_ports:
                nni_ports_with_speeds = get_NNI_ports(num_flexe_ports, device_type)
                validate_capacity(client_ports, nni_ports_with_speeds)
                return num_flexe_ports, nni_ports_with_speeds, client_ports
            else:
                print(f"The number of FlexE ports must be between 1 and {max_nni_ports}. Please try again.")
        except ValueError as e:
            print(e)

def get_flexe_device_info():
    valid_devices = {
        "5130": {"client_ports": 12, "nni_ports": 2},
        "5164": {"client_ports": 32, "nni_ports": 4},
        "5166": {"client_ports": 32, "nni_ports": 2},
        "5184": {"client_ports": 32, "nni_ports": 4},
    }

    while True:
        device_type = input("What FlexE device are you configuring? (5130, 5164, 5166, 5184): ").strip()
        if device_type in valid_devices:
            return device_type, valid_devices[device_type]
        else:
            print("Invalid device. Please enter one of the following: 5130, 5164, 5166, 5184.")

def get_NNI_ports(num_flexe_ports, device_type):
    valid_ports = {
        "5130": [13, 14],
        "5164": [33, 34, 35, 36],
        "5166": [33, 34],
        "5184": [33, 34, 35, 36],
    }

    nni_ports = {}
    while len(nni_ports) < num_flexe_ports:
        try:
            port = input(f"Enter FlexE port {len(nni_ports) + 1} (valid ports for {device_type} are {valid_ports[device_type]}): ")
            if port.isdigit() and int(port) in valid_ports[device_type]:
                if port not in nni_ports:
                    if device_type == "5130":
                        speed = "100G"
                    else:
                        speed = get_valid_speed(device_type)
                    nni_ports[port] = speed
                else:
                    print("Port already entered. Please enter a different port.")
            else:
                print(f"Invalid port. Please enter a value from {valid_ports[device_type]}.")
        except ValueError:
            print("Invalid input. Please enter an integer.")
    return nni_ports

def get_client_ports(max_client_ports):
    while True:
        try:
            num_client_ports = int(input(f"Enter the number of client ports (1-{max_client_ports}): "))
            if 1 <= num_client_ports <= max_client_ports:
                return num_client_ports
            else:
                print(f"The number must be between 1 and {max_client_ports}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

def get_flexe_protection_info(max_client_ports, device_type):
    valid_protection_ports = {
        "5130": [13, 14],
        "5164": [33, 34, 35, 36],
        "5166": [33, 34],
        "5184": [33, 34, 35, 36],
    }[device_type]

    use_protection = input("Do you plan on using FlexE protection? (yes/no): ").strip().lower()
    if use_protection != 'yes':
        return None, None, None

    num_protected_clients = 0
    while num_protected_clients < 1 or num_protected_clients > max_client_ports:
        try:
            num_protected_clients = int(input(f"Enter the number of clients to be protected (1-{max_client_ports}): "))
        except ValueError:
            pass

    protection_ports = []
    while len(protection_ports) < 2:
        port = input(f"Enter protection port {len(protection_ports) + 1} (valid ports are {valid_protection_ports}): ")
        if port.isdigit() and int(port) in valid_protection_ports:
            if port not in protection_ports:
                protection_ports.append(port)
            else:
                print("Port already entered. Please enter a different port.")
        else:
            print(f"Invalid port. Please enter a value from {valid_protection_ports}.")

    return use_protection, num_protected_clients, protection_ports

def validate_capacity(num_client_ports, nni_ports_with_speeds):
    required_capacity = num_client_ports * 10  # Each client port is 10G
    available_capacity = sum(int(speed[:-1]) for speed in nni_ports_with_speeds.values())  # Adjusted to handle "G" suffix
    if required_capacity > available_capacity:
        raise ValueError(f"Insufficient capacity: {required_capacity}G required, but only {available_capacity}G available.")

def flexe_no_protection(num_client_ports, nni_ports_with_speeds):
    configuration = []

    # Classifiers
    configuration.append("classifiers classifier untagged filter-entry 'classifier:vtag-stack' untagged-exclude-priority-tagged true")
    configuration.append("classifiers classifier any filter-entry vtag-stack vtags 1")
    configuration.append("exit")
    configuration.append("exit")
    configuration.append("exit")
    configuration.append("exit")

    # FDs
    for idx, port in enumerate(nni_ports_with_speeds.keys(), start=1):
        configuration.append(f"fds fd fd_any{idx} mode vpws mac-learning disabled")

    # Logical ports and FPS
    for i in range(1, num_client_ports + 1):
        configuration.append(f"no fps fp remote-fp{i}")
        configuration.append(f"logical-ports logical-port {i} binding {i}")
        configuration.append(f"logical-ports logical-port {i} mtu 9800")
        configuration.append(f"fps fp fp{i}")
        configuration.append(f"fd-name fd_any{i}")
        configuration.append("stats-collection on")
        configuration.append(f"logical-port {i}")
        configuration.append("classifier-list any untagged")
        configuration.append("exit")
        configuration.append("exit")

    # FlexE ports and groups
    for port, speed in nni_ports_with_speeds.items():
        configuration.append(f"no fps fp remote-fp{port}")
        configuration.append(f"no logical-ports logical-port {port} binding")
        configuration.append(f"no oc-if:interfaces interface {port} config ptp-id")
        configuration.append(f"flexe-ports flexe-port flexe-nni-{port} ptp-id {port} port-speed {speed}")

    for idx, (port, speed) in enumerate(nni_ports_with_speeds.items(), start=1):
        phy_type = f"flexe-phy-{speed}BASE-R"
        group_name = f"flex{idx}"
        configuration.append(f"flexe-groups flexe-group {group_name}")
        configuration.append(f"group-number {idx}")
        configuration.append("calendar-slot-granularity slot-5G")
        configuration.append(f"phy-type {phy_type}")
        configuration.append(f"flexe-phys 1 local-interface flexe-nni-{port}")
        configuration.append("exit")
        configuration.append("exit")

    # FlexE channels
    channel_number = 601
    for idx, (port, speed) in enumerate(nni_ports_with_speeds.items(), start=1):
        group_name = f"flex{idx}"
        mac_ettp_name = f"ettp_flexe{idx}"
        flexe_lp_name = f"flexe_lp_{idx}"

        configuration.append(f"flexe-channels flexe-channel channel-{channel_number}")
        configuration.append(f"channel-number {channel_number}")
        configuration.append(f"group-name {group_name}")
        configuration.append("channel-mapping L2-mapped")

        #Calendars
        slot_count = 0
        if speed == "100G":
            slot_count = 20
        elif speed == "200G":
            slot_count = 40
        elif speed == "400G":
            slot_count = 80

        for i in range(1, slot_count + 1):
            configuration.append(f"calendar-A-slots-list 1 {i}")
            configuration.append("exit")
            configuration.append(f"calendar-B-slots-list 1 {i}")
            configuration.append("exit")
        configuration.append("exit")
        configuration.append("exit")

        # Flexe ettp
        configuration.append(f"oc-if:interfaces interface {mac_ettp_name} config name {mac_ettp_name} type ettp ettp-mode flexe-mac")
        configuration.append(f"oc-if:interfaces interface {mac_ettp_name} config name {mac_ettp_name} flexe-channel channel-{channel_number}")

        # Flexe Logical Port
        configuration.append(f"logical-ports logical-port {flexe_lp_name} binding {mac_ettp_name}")
        configuration.append(f"logical-ports logical-port {port} mtu 9800")
        configuration.append(f"fps fp flexe-fp{port}")
        configuration.append(f"fd-name fd_any{idx}")
        configuration.append("stats-collection on")
        configuration.append(f"logical-port {flexe_lp_name}")
        configuration.append("classifier-list any untagged")
        configuration.append("exit")
        configuration.append("exit")

        channel_number += 1

        return configuration
    
def send_to_file(configuration, use_protection, num_protected_clients, end):
    if use_protection:
        filename = f"flexe_protection_{num_protected_clients}_configuration{end}.txt"
    else:
        filename = "flexe_configuration.txt"

    folder_path = os.path.join(os.getcwd(), "Configurations")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    
    with open(file_path, "w") as file:
        for line in configuration:
            file.write(line + "\n")


def send_removal_to_file(removal_config, num_protected_clients):
    filename = f"flexe_removal_{num_protected_clients}_configuration.txt"

    folder_path = os.path.join(os.getcwd(), "Configurations")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    
    with open(file_path, "w") as file:
        for line in removal_config:
            file.write(line + "\n")

def send_to_device(configuration, host, port, username, password):
    config_str = "\n".join(configuration)
    with manager.connect(host=host, port=port, username=username, password=password, hostkey_verify=False) as eos:
        eos.edit_config(target='running', config=config_str)

def flexe_protection( nni_ports_with_speeds, num_protected_clients, protection_ports, end):
    configuration = []
    
    # Classifiers
    configuration.append("classifiers classifier untagged filter-entry 'classifier:vtag-stack' untagged-exclude-priority-tagged true")
    configuration.append("classifiers classifier any filter-entry vtag-stack vtags 1")
    configuration.append("exit")
    configuration.append("exit")
    configuration.append("exit")
    configuration.append("exit")

    # FDs
    for idx in range(1, num_protected_clients + 1):
        configuration.append(f"fds fd fd_any{idx} mode vpws mac-learning disabled")

    # Logical ports and FPS
    for i in range(1, num_protected_clients + 1):
        configuration.append(f"no fps fp remote-fp{i}")
        configuration.append(f"logical-ports logical-port {i} binding {i}")
        configuration.append(f"logical-ports logical-port {i} mtu 9800")
        configuration.append(f"fps fp fp{i}")
        configuration.append(f"fd-name fd_any{i}")
        configuration.append("stats-collection on")
        configuration.append(f"logical-port {i}")
        configuration.append("classifier-list any untagged")
        configuration.append("exit")
        configuration.append("exit")

    # FlexE ports
    for idx, (port, speed) in enumerate(nni_ports_with_speeds.items(), start=1):
        configuration.append(f"no fps fp remote-fp{port}")
        configuration.append(f"no logical-ports logical-port {port} binding")
        configuration.append(f"no oc-if:interfaces interface {port} config ptp-id")
        configuration.append(f"flexe-ports flexe-port flexe-nni-{port} ptp-id {port} port-speed {speed}b")

    # FlexE Groups
    for idx, (port, speed) in enumerate(nni_ports_with_speeds.items(), start=1):
        phy_type = f"flexe-phy-{speed}BASE-R"
        group_name = f"flex_{idx}"

        configuration.append(f"flexe-groups flexe-group {group_name}")
        configuration.append(f"group-number {idx}")
        configuration.append("calendar-slot-granularity slot-5G")
        configuration.append(f"phy-type {phy_type}")
        configuration.append(f"flexe-phys 1 local-interface flexe-nni-{port}")
        configuration.append("exit")
        configuration.append("exit")
        

    # FlexE bas-oams
    for idx in range(1, num_protected_clients + 1):
        configuration.append(f"flexe-bas-oams flexe-bas-oam prot_{idx}")
        configuration.append("exit")
        configuration.append("exit")
        configuration.append(f"flexe-bas-oams flexe-bas-oam work_{idx}")
        configuration.append("exit")
        configuration.append("exit")

    
    # FlexE protection profiles
    configuration.append("flexe-protection-profiles flexe-protection-profile profile1")
    configuration.append("exit")
    configuration.append("exit")

    slot_allocation = 1
    group_name_work = f"flex_1"
    group_name_prot = f"flex_2"
    slot_allocation = 1
    channel_number = 601
    Channel_count = 1
    calendar_id = 1
    
    for client_port in range(1, num_protected_clients + 1):
        bas_oam_work = f"work_{Channel_count}"
        bas_oam_prot = f"prot_{Channel_count}"

            # Determine the maximum slots per calendar based on speed
        max_slots_per_calendar = 0
        for port, speed in nni_ports_with_speeds.items():
            if speed == "100G":
                max_slots_per_calendar = 20
            elif speed == "200G":
                max_slots_per_calendar = 40
            elif speed == "400G":
                max_slots_per_calendar = 80
            break
        
        # Working channel
        configuration.append(f"flexe-channels flexe-channel channel-work-{Channel_count}")
        configuration.append(f"bas-oam {bas_oam_work}")
        configuration.append(f"channel-number {channel_number}")
        configuration.append(f"group-name {group_name_work}")
        configuration.append("channel-mapping L2-mapped")

        configuration.append(f"calendar-A-slots-list {calendar_id} {slot_allocation}")
        configuration.append("exit")
        configuration.append(f"calendar-A-slots-list {calendar_id} {slot_allocation + 1}")
        configuration.append("exit")
        configuration.append(f"calendar-B-slots-list {calendar_id} {slot_allocation}")
        configuration.append("exit")
        configuration.append(f"calendar-B-slots-list {calendar_id} {slot_allocation + 1}")
        configuration.append("exit")

        configuration.append("exit")
        configuration.append("exit")
        
        Channel_count += 1
        channel_number += 1

        # Protected channel
        configuration.append(f"flexe-channels flexe-channel channel-prot-{Channel_count-1}")
        configuration.append(f"bas-oam {bas_oam_prot}")
        configuration.append(f"channel-number {channel_number}")
        configuration.append(f"group-name {group_name_prot}")
        configuration.append("channel-mapping L2-mapped")

        configuration.append(f"calendar-A-slots-list {calendar_id} {slot_allocation}")
        configuration.append("exit")
        configuration.append(f"calendar-A-slots-list {calendar_id} {slot_allocation + 1}")
        configuration.append("exit")
        configuration.append(f"calendar-B-slots-list {calendar_id} {slot_allocation}")
        configuration.append("exit")
        configuration.append(f"calendar-B-slots-list {calendar_id} {slot_allocation + 1}")
        configuration.append("exit")

        configuration.append("exit")
        configuration.append("exit")
        


        #FlexE Protection Groups
        configuration.append(f"flexe-protection-groups flexe-protection-group flexe_protection_group{Channel_count - 1} working-channel channel-work-{Channel_count - 1} protection-channel channel-prot-{Channel_count - 1} protection-profile \"profile1\"")
        configuration.append(f"oc-if:interfaces interface 'flexe-protection-group_ettp{Channel_count - 1}' config name flexe-protection-group_ettp{Channel_count - 1} ettp-mode flexe-mac flexe-protection-group \"flexe_protection_group{Channel_count - 1}\" type ettp")
        configuration.append(f"logical-ports logical-port flexe-lp{Channel_count - 1} binding flexe-protection-group_ettp{Channel_count - 1}")
        configuration.append(f"logical-ports logical-port flexe-lp{Channel_count - 1} mtu 9800")
        configuration.append(f"fps fp flexe-fp{Channel_count - 1}")
        configuration.append(f"fd-name fd_any{Channel_count - 1}")
        configuration.append("stats-collection on")
        configuration.append(f"logical-port flexe-lp{Channel_count - 1}")
        configuration.append("classifier-list any untagged")
        configuration.append("exit")
        configuration.append("exit")

        channel_number += 1
        slot_allocation +=2
        
        if slot_allocation > max_slots_per_calendar:
            slot_allocation = 1
            calendar_id += 1


    # CFM global configuration
    configuration.append("cfm-global-config admin-state enable")

    # Maintenance domain and associations
    for idx in range(1, num_protected_clients + 1):
        configuration.append(f"maintenance-domain md{idx}")
        configuration.append("name-type character-string")
        configuration.append(f"name md{idx}")
        configuration.append("md-level 7")
        configuration.append("mhf-creation none")
        configuration.append("id-permission none")
        configuration.append("exit")

        configuration.append(f"maintenance-domain md{idx}")
        configuration.append(f"maintenance-association ma{idx}")
        configuration.append("name-type character-string")
        configuration.append(f"name flexe_protection_group{idx}_port{idx}")
        configuration.append("ccm-interval 10ms")
        configuration.append(f"component-list 1 fd-name fd_any{idx}")
        configuration.append("exit")
        configuration.append("exit")

        configuration.append(f"maintenance-domain md{idx}")
        configuration.append(f"maintenance-association ma{idx}")
        configuration.append(f"maintenance-association-end-point {'1' if end == 'A' else '2'}")
        configuration.append("direction up")
        configuration.append(f"interface fp{idx}")
        configuration.append("administrative-state true")
        configuration.append("ccm-ltm-priority 1")
        configuration.append("continuity-check")
        configuration.append("cci-enabled true lowest-fault-priority-defect remote-mac-error")
        configuration.append("exit")
        configuration.append("exit")
        configuration.append("exit")
        configuration.append("exit")

    # PPM configuration
    configuration.append("ppm config global-state admin-status enable")

    # Action Group config
    configuration.append(f"ppm config action-group ccmag type fault 1 action ccm-stop")
    configuration.append(f"ppm config action-group ccmag type recovery 1 action ccm-resume")
    configuration.append(f"ppm config action-group portag type fault 1 action shut")
    configuration.append(f"ppm config action-group portag type recovery 1 action unshut")

    for idx in range(1, num_protected_clients + 1):

        configuration.append(f"ppm config instance-group clientig{idx} ppm-instance source cfm-instance md{idx} ma{idx} {'1' if end == 'A' else '2'} action-group ccmag")
        configuration.append(f"ppm config instance-group clientig{idx} ppm-instance destination logical-port-instance {idx} action-group portag")
        configuration.append(f"ppm config instance-group clientig{idx} direction bidirectional")
        configuration.append(f"ppm config instance-group clientig{idx} state enable")

    return configuration

def generate_removal_config(num_protected_clients):
    removal_config = []

    # Remove PPM configuration
    removal_config.append("no ppm")

    # Remove maintenance domains
    for idx in range(1, num_protected_clients + 1):
        removal_config.append(f"no maintenance-domain md{idx}")

    # Remove FPS and logical ports
    for idx in range(1, num_protected_clients + 1):
        removal_config.append(f"no fps fp flexe-fp{idx}")
        removal_config.append(f"no logical-ports logical-port flexe-lp{idx}")

    # Remove OC interfaces
    for idx in range(1, num_protected_clients + 1):
        removal_config.append(f"no oc-if:interfaces interface flexe-protection-group_ettp{idx}")

    # Remove FlexE protection groups, channels, and groups
    removal_config.append("no flexe-protection-groups")
    removal_config.append("no flexe-channels")
    removal_config.append("no flexe-groups")
    removal_config.append("no flexe-bas-oams")
    removal_config.append("no flexe-ports")
    removal_config.append("no flexe-protection-profiles")
    removal_config.append("no fps")
    removal_config.append("no fds")
    removal_config.append("no classifiers")

    return removal_config

def main():
    configurations = ""
    configurations_Z = ""
    configurations_A = ""

    configuration_removal = ""

    #Get device info
    device_type, device_info, = get_flexe_device_info()
    print(f"Device info: {device_info}")
    num_client_ports = device_info["client_ports"]
    num_nni_ports = device_info["nni_ports"]

    print(f"Number of client ports: {num_client_ports}")
    print(f"Number of NNI ports: {num_nni_ports}")

    #Get number of client ports to be configured
    client_ports = get_client_ports(num_client_ports)
    num_flexe_ports, nni_ports_with_speeds, num_client_ports = get_flexe_ports(client_ports, num_nni_ports, device_type)

        
    use_protection, num_protected_clients, protection_ports = get_flexe_protection_info(client_ports, device_type)
    

    if use_protection:
        print(f"Number of clients to be protected: {num_protected_clients}")
        print(f"Protection ports: {', '.join(protection_ports)}")

        A = "A"
        Z = "Z"

        configuration_A = flexe_protection(nni_ports_with_speeds, num_protected_clients, protection_ports, A)
        configuration_Z = flexe_protection(nni_ports_with_speeds, num_protected_clients, protection_ports, Z)
        

        send_to_file(configuration_A, use_protection, num_protected_clients, A)
        send_to_file(configuration_Z, use_protection, num_protected_clients, Z)

        configuration_removal = generate_removal_config(num_protected_clients)

        send_removal_to_file(configuration_removal, num_protected_clients)

        '''
        if num_protected_clients == client_ports:
            configuration = flexe_protection(nni_ports_with_speeds, num_protected_clients, protection_ports)
        else:

            configuration = flexe_protection(nni_ports_with_speeds, num_protected_clients, protection_ports)

        send_to_file(configuration, use_protection, num_protected_clients)
        print(f"Configuration written to flexe_protection_{num_protected_clients}_configuration.txt")
        '''
    else:
        print("FlexE protection not used.")
        configuration = flexe_no_protection(num_client_ports, nni_ports_with_speeds)
        send_to_file(configuration, use_protection, num_protected_clients)
        print("Configuration written to flexe_configuration.txt")

    # Unfinished option to send directly to the device via netconf.
    ''''
    'destination = input("Do you want to send the configuration to a file or push via netconf to a device? (file/netconf): ").strip().lower()
    
    if destination == "file":
        send_to_file(configuration)
        print("Configuration written to flexe_configuration.txt")
    elif destination == "netconf":
        host = input("Enter the device IP address: ")
        port = input("Enter the device port (default 830): ") or "830"
        username = input("Enter the username: ")
        password = input("Enter the password: ")
        send_to_device(configuration, host, port, username, password)
        print("Configuration pushed to the device via netconf.")
    else:
        print("Invalid option. Please enter 'file' or 'netconf'.")
    '''


if __name__ == "__main__":
    main()