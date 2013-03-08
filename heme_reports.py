# coding: utf-8
import re
from os import path

date = "(\d\d\/\d\d\/\d\d\d\d)"
info_re = "\s+(\w+)\s+%s\s+(\d{4,4})\s+([\w\-\,]+)\s+(\d+)\s+\w+\s+%s" % (date, date)
hexa_re = "{HEXA([\s\w]+)"

rvvt_names = ["DVVTS", "DISS", "DVVN", "ISR", "DVVCS", "DVVCR"]
rvvt_re = "\s+".join(["{%s([\s\d\.\,\*\w]+) \(RVVTD,6910\)" % name for name in rvvt_names])


hexa_rvvt_vals = {'POS': 'also positive', 'NEG': 'negative', 'EQUIV': 'equivocal'}

hexa_pos_template = """
Result:  
Positive (lupus anticoagulant detected); see comment.

Clinical Interpretation by Pathologist:

The Lupus Anticoagulant by HEXA test is POSITIVE for lupus anticoagulant according to the manufacturer’s guidelines for interpretation.

Current guidelines suggest testing for lupus anticoagulant with two clot based tests (J Thromb Haemost 2009; 7: 1737-40) and it is noted that the concurrent RVVT assay is %s in this patient.  Lupus anticoagulant testing should be considered positive if one of the two tests gives a positive result.

Testing for lupus anticoagulant in the presence of anticoagulant therapy (including warfarin, direct thrombin inhibitors & direct factor 10a inhibitors, and supratherapeutic heparin) is not recommended due to possible interference with test results.  Clinical correlation is advised as anticoagulation therapy may result in a false positive result; [in this sample a false positive is unlikely given the strength of the positive result.]  The presence of factor deficiencies or a factor specific inhibitor may also interfere with this assay.

Positive test results must be interpreted in their clinical context if a diagnosis of antiphospholipid syndrome is being considered.  J Thromb Haemost 2006; 4: 295–306 provides consensus guidelines for diagnosis of antiphospholipid syndrome.



Scott Kogan, MD
82493
""".replace('\n', '\r\n')

hexa_equiv_template = """
Result:  
Equivocal; see comment.

Clinical Interpretation by Pathologist:
The Lupus Anticoagulant by HEXA test is at the border between a negative and a positive result.  The results are therefore EQUIVOCAL.  If clinically indicated and at an appropriate time, the Lupus Anticoagulant by HEXA test could by repeated.

Current guidelines suggest testing for lupus anticoagulant with two clot based tests (J Thromb Haemost 2009; 7: 1737-40) and it is noted that the concurrent RVVT assay is %s in this patient.  Lupus anticoagulant testing should be considered positive if one of the two tests gives a positive result. [Given the negative results in both the Lupus Anticoagulant by HEXA and RVVT assays, the findings are negative for Lupus Anticoagulant.]

Testing for lupus anticoagulant in the presence of anticoagulant therapy (including warfarin, direct thrombin inhibitors & direct factor 10a inhibitors, and supratherapeutic heparin) is not recommended due to possible interference with test results.  The presence of factor deficiencies or a factor specific inhibitor may also interfere with this assay.  Clinical correlation is advised.

Test results must be interpreted in their clinical context if a diagnosis of antiphospholipid syndrome is being considered.  J Thromb Haemost 2006; 4: 295–306 provides consensus guidelines for diagnosis of antiphospholipid syndrome.



Scott Kogan, MD
82493
""".replace('\n', '\r\n')

def get_worksheet_test(text, info_re, test_re):
    test = {}
    for i, j in zip(re.findall(info_re, text), re.findall(test_re, text)):
        acc, accdate, acctime, name, mrn, bdate = i
        result = j
        test[acc] = {'acc': acc,
                      'accdate': accdate.replace('/','.'),
                      'acctime': acctime,
                      'name': name,
                      'mrn': mrn,
                      'bdate': bdate.replace('/','.'),
                      'result': j
                      }
    return test

def interpret_rvvt(test, pt):
    MANUF_THRESH = {'DVVTS': 43.2, 'DVVCR': 1.17}
    ISTH_THRESH = {'DVVTS': 44.5, 'DVVCR': 1.07}
    DISS_ALT = 44.5
    DISS_THRESH = 41.6

    val = {}
    for name, res in zip(rvvt_names, test['result']):
       val[name] = float(res.split(',')[0])
    # if PTT prolonged
    pass
    # PL dependent

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

    for acc in hexas:
        hexa_args = [hexas[acc][i] for i in ['name', 'mrn', 'acc', 'accdate']]
        hexa_title = "%s %s %s %s HEXA" % tuple(hexa_args)
        f = open(path.join(outdir, hexa_title) + '.txt', 'w')
        f.write(hexa_title + '\n')
        if acc in rvvts:
            hexa_rvvt_text = hexa_rvvt_vals[rvvts[acc]['result']]
        else:
            # TODO:  check to see if the value is _always_ negative if not returned
            hexa_rvvt_text = hexa_rvvt_vals['NEG']
        if hexas[acc]['result'].strip() == "POS":
            f.write(hexa_pos_template % hexa_rvvt_text)
        elif hexas[acc]['result'].strip() == "EQHEX":
            f.write(hexa_equiv_template % hexa_rvvt_text)
        else:
            print "result uninterpreted: %s\n%s" % (hexas[acc]['result'], i)
            import pdb; pdb.set_trace()
        
