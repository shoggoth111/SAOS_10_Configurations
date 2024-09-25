
import unittest
from unittest.mock import patch
from FlexE_Configurator import get_flexe_device_info, get_client_ports, get_flexe_ports, get_NNI_ports, get_valid_speed, validate_capacity, flexe_no_protection, flexe_protection, send_to_file, get_flexe_protection_info

class TestFlexEConfigurator(unittest.TestCase):

    @patch('builtins.input', side_effect=['5130'])
    def test_device_type_5130_no_protection(self, mock_input):
        device_type, device_info = get_flexe_device_info()
        self.assertEqual(device_type, '5130')
        self.assertEqual(device_info['client_ports'], 12)
        self.assertEqual(device_info['nni_ports'], 2)

    @patch('builtins.input', side_effect=['5164'])
    def test_device_type_5164_with_protection(self, mock_input):
        device_type, device_info = get_flexe_device_info()
        self.assertEqual(device_type, '5164')
        self.assertEqual(device_info['client_ports'], 32)
        self.assertEqual(device_info['nni_ports'], 4)

    @patch('builtins.input', side_effect=['5166'])
    def test_device_type_5166_no_protection(self, mock_input):
        device_type, device_info = get_flexe_device_info()
        self.assertEqual(device_type, '5166')
        self.assertEqual(device_info['client_ports'], 32)
        self.assertEqual(device_info['nni_ports'], 2)

    @patch('builtins.input', side_effect=['5184'])
    def test_device_type_5184_with_protection(self, mock_input):
        device_type, device_info = get_flexe_device_info()
        self.assertEqual(device_type, '5184')
        self.assertEqual(device_info['client_ports'], 32)
        self.assertEqual(device_info['nni_ports'], 4)

    @patch('builtins.input', side_effect=['9999', '5130'])
    def test_invalid_device_type(self, mock_input):
        device_type, device_info = get_flexe_device_info()
        self.assertEqual(device_type, '5130')

    @patch('builtins.input', side_effect=['32'])
    def test_get_client_ports(self, mock_input):
        num_client_ports = get_client_ports(32)
        self.assertEqual(num_client_ports, 32)

    @patch('builtins.input', side_effect=['4', '32', '100G', '33', '100G', '34', '100G', '35', '100G'])
    def test_get_flexe_ports(self, mock_input):
        num_flexe_ports, nni_ports_with_speeds, client_ports = get_flexe_ports(32, 4, '5164')
        self.assertEqual(num_flexe_ports, 4)
        self.assertEqual(len(nni_ports_with_speeds), 4)
        self.assertEqual(nni_ports_with_speeds['32'], '100G')
        self.assertEqual(nni_ports_with_speeds['33'], '100G')
        self.assertEqual(nni_ports_with_speeds['34'], '100G')
        self.assertEqual(nni_ports_with_speeds['35'], '100G')
        self.assertEqual(client_ports, 32)

    @patch('builtins.input', side_effect=['32', '100G', '33', '100G', '34', '100G', '35', '100G'])
    def test_get_nni_ports(self, mock_input):
        nni_ports = get_NNI_ports(4, '5164')
        self.assertEqual(len(nni_ports), 4)
        self.assertEqual(nni_ports['32'], '100G')
        self.assertEqual(nni_ports['33'], '100G')
        self.assertEqual(nni_ports['34'], '100G')
        self.assertEqual(nni_ports['35'], '100G')

    @patch('builtins.input', side_effect=['100G'])
    def test_get_valid_speed(self, mock_input):
        speed = get_valid_speed('5164')
        self.assertEqual(speed, '100G')

    def test_validate_capacity(self):
        nni_ports_with_speeds = {'32': '100G', '33': '100G', '34': '100G', '35': '100G'}
        self.assertRaises(ValueError, validate_capacity, 40, nni_ports_with_speeds)

    @patch('builtins.input', side_effect=['yes', '16', '32', '33'])
    def test_flexe_protection(self, mock_input):
        max_client_ports = 32
        device_type = '5164'
        use_protection, num_protected_clients, protection_ports = get_flexe_protection_info(max_client_ports, device_type)
        self.assertTrue(use_protection)
        self.assertEqual(num_protected_clients, 16)
        self.assertEqual(protection_ports, ['32', '33'])

    @patch('builtins.input', side_effect=['no'])
    def test_flexe_no_protection(self, mock_input):
        max_client_ports = 32
        device_type = '5164'
        use_protection, num_protected_clients, protection_ports = get_flexe_protection_info(max_client_ports, device_type)
        self.assertFalse(use_protection)

if __name__ == '__main__':
    unittest.main()
