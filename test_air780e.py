import unittest
from air780e import Chip


class TestChip(unittest.TestCase):
    def setUp(self):
        self.chip = Chip()

    def test_parse_imei_response_valid(self):
        response = "\r\nconfig,imei,ok,868488071666208\r\n"
        imei = self.chip.parse_imei_response(response)
        self.assertEqual(imei, "868488071666208")

    def test_parse_imei_response_invalid(self):
        response = "\r\nconfig,imei,error\r\n"
        imei = self.chip.parse_imei_response(response)
        self.assertIsNone(imei)


if __name__ == "__main__":
    unittest.main()
