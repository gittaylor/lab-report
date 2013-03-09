# coding: utf-8
import re
from os import path

def rvvt_test_results():
    return {"W13590": {"result": "NEG"}, 
            "F55075": {"result": "POS"}, 
            "H3231": {"result": "NEG"}, 
            "M58876": {"result": "NEG"}, 
            "T65658": {"result": "NEG"}, 
            "T61615": {"result": "POS"}, 
            "H6779": {"result": "POS"}}

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
