import unittest

from throttle import protocol


class ProtocolTests(unittest.TestCase):
    def test_frames_match_known_captures(self):
        self.assertEqual(protocol.horn(True), bytes([0x00, 0x48, 0x01, 0xB7]))
        self.assertEqual(protocol.bell(False), bytes([0x00, 0x47, 0x00, 0xB9]))
        self.assertEqual(protocol.speed(31), bytes([0x00, 0x45, 0x1F, 0x9C]))
        self.assertEqual(protocol.direction(False), bytes([0x00, 0x46, 0x02, 0xB8]))
        self.assertEqual(protocol.dialog(), bytes([0x00, 0x4D, 0x00, 0x01, 0xB2]))
        self.assertEqual(protocol.smoke(True), bytes([0x00, 0x50, 0x01, 0xAF]))
        self.assertEqual(protocol.master_volume(7), bytes([0x00, 0x4C, 0x07, 0xAD]))

    def test_payload_and_checksum_sum_to_zero(self):
        for packet in (protocol.lights(True), protocol.bell(True), protocol.speed(12)):
            self.assertEqual(packet[0], 0x00)
            self.assertEqual(sum(packet[1:]) % 256, 0)

    def test_rejects_out_of_range(self):
        for bad in (-1, 32, 3.5, True, None):
            with self.assertRaises(ValueError):
                protocol.speed(bad)
        with self.assertRaises(ValueError):
            protocol.master_volume(8)


if __name__ == "__main__":
    unittest.main()
