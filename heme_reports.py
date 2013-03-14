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
    if argv[1] == 'rvvt_inrs':
        hexa_txt, rvvt_txt = read_hexa_rvvt_worksheet(argv[2])
        rvvt = ht.RVVT()
        rvvt.parse_text(rvvt_txt)
        for mrn in rvvt.requires_inr():
            print(mrn + '\r')
    elif argv[1] == 'report_templates':
        hexa_txt, rvvt_txt = read_hexa_rvvt_worksheet(argv[2])
        rvvt = ht.RVVT()
        rvvt.parse_text(rvvt_txt)
        hexa = ht.HEXA()
        hexa.parse_text(hexa_txt)
        hexa.make_reports(open(argv[4]).read(), 'HEXA', argv[5])
        rvvt.make_reports(open(argv[3]).read(), 'RVVT', argv[5])

    elif argv[1] == 'interpret_rvvts_hexas':
        hexa_txt, rvvt_txt = read_hexa_rvvt_worksheet(argv[2])
        rvvt = ht.RVVT()
        rvvt.parse_text(rvvt_txt)
        inr = ht.PT()
        inr.parse_text(open(argv[3]).read())
        hexa = ht.HEXA()
        hexa.parse_text(hexa_txt)
        rvvt.make_reports(hexa, inr, argv[4])
        hexa.make_reports(rvvt, inr, argv[4])

        
