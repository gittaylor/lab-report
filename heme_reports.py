# coding: utf-8
import heme_tests as ht
from os import path

def rvvt_test_results():
    return {"W13590": {"result": "NEG"}, 
            "F55075": {"result": "POS"}, 
            "H3231": {"result": "NEG"}, 
            "M58876": {"result": "NEG"}, 
            "T65658": {"result": "NEG"}, 
            "T61615": {"result": "POS"}, 
            "H6779": {"result": "POS"}}

def read_hexa_rvvt_worksheet(filename):
    f = open(filename)
    txt = f.read()
    f.close()
    hexa, rvvt = txt.split('WORKSHEET: RVVTD', 1)
    return hexa, rvvt

def read_pts(filename):
    f = open(filename)
    txt = f.read()
    f.close()
    pt_txt = txt.split('RESULT INQUIRY',1)[1]
    return pt_txt

def get_hexa_results(filename, outdir):
    f = open(filename)
    txt = f.read()
    f.close()
    txt = txt.split('WORKSHEET: RVVTD', 1)
    if len(txt) < 2:
        print "failed to split reports!"
        import pdb; pdb.set_trace()

    hexas =  get_worksheet_test(txt[0], info_re, hexa_re)
    rvvts = rvvt_test_results()

if __name__ == '__main__':
    from sys import argv
    if argv[1] == 'rvvt_pts':
        hexa_txt, rvvt_txt = read_hexa_rvvt_worksheet(argv[2])
        rvvt = ht.RVVT()
        rvvt.parse_text(rvvt_txt)
        for mrn in rvvt.requires_pt():
            print(mrn + '\r')

    elif argv[1] == 'interpret_rvvts_hexas':
        hexa_txt, rvvt_txt = read_hexa_rvvt_worksheet(argv[2])
        pt_txt = read_pts(argv[3])
        pt = ht.PT()
        pt.parse_text(pt_txt)
        latest_pts = pt.get_latest()
        
