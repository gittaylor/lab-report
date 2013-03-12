import unittest
import heme_tests as ht

class TestTemplates(unittest.TestCase):

    def setUp(self):
        self.hexa_rvvt_text = open('../LUPUS.txt').read()
        self.hexa_text, self.rvvt_text = self.hexa_rvvt_text.split('WORKSHEET: RVVT', 1)
    def test_RVVT(self):
        rvvt = ht.RVVT()
        rvvt.parse_worksheet(self.rvvt_text)
        print rvvt.requires_pt()

if __name__ == '__main__':
    unittest.main()
