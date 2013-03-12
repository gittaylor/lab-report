# coding: utf-8
import re
from datetime import datetime

class Result(float):
    def __new__(self, val, flag=None, other={}):
        self.flag = flag
        self.other = other
        return super(Result, self).__new__(self, val)

class RVVTresult(Result):
    def __new__(self, result):
        res = result.split(',')
        if len(res) == 2:
            return super(Result, self).__new__(self, res[0], other={'st': res[1]})
        elif len(res) == 3:
            return super(Result, self).__new__(self, res[0], flag=res[2])
        else:
            raise ValueError("cannot parse result: %s" % result)


class Test(object):
    re_date = "(\d\d\/\d\d\/\d\d\d\d)"
    re_time = "([\d\:]+)"
    re_name = "([\w\-\,]+)"
    re_acc = "(\w\d+)"
    re_mrn = "(\d+)"
    re_wo_info1 = "\s+".join([re_acc, re_date, re_time, re_name])
    re_wo_info2 = "\s+%s\s+\w+\s+%s" % (re_mrn, re_date)

    def make_report(template, **vars):
        f = open(self.__getattribute__(template))
        text = f.read()
        f.close()
        return self.replace(text, vars)

    def parse_result(self, result):
        return Result(result)

    def parse_text(self, text):
        results = {}
        for i, j, k in zip(re.finditer(self.re_wo_info1, text), re.finditer(self.re_wo_info2, text), re.finditer(self.re_result, text)):
            # sanity check to make sure the regex results are near each other
            # if wo_info2.start() - wo_info1.start() < 0 or > 200 these are likely from different entries
            # if re_result.start() - wo_info2.start() < 0 or > 400 these are likely from different entries

            if j.start() - i.start() < 0 or j.start() - i.start() > 200:
                raise ValueError("error parsing result near position %s" % min(i.start(), j.start()))
            if k.start() - j.start() < 0 or k.start() - j.start() > 400:
                raise ValueError("error parsing result near position %s" % min(j.start(), k.start()))
            
            acc, accdate, acctime, name = i.groups()
            mrn, bdate = j.groups()
            results[acc] = {'acc': acc,
                                   'date': datetime.strptime(accdate + ' ' + acctime, '%m/%d/%Y %H:%M'),
                          'name': name,
                          'mrn': mrn,
                          'bdate': datetime.strptime(bdate, '%m/%d/%Y'),
                          'result': self.parse_result(k.groups())
                          }
        self.results = results
        return results
    
    def make_identifier(self, acc):
        id_args = [self.results[acc][i] for i in ['name', 'mrn', 'acc', 'accdate']]
        return "%s %s %s %s" % tuple(id_args)

    def replace(astring, adict, find=r"<(\w+)>"):
      expr = re.compile(find, re.M)
      astring= str(astring)
      match = expr.search(astring)
      while match is not None:
        stringEnd = astring[match.end():]
        if match.group(1) in adict:
          matchStr = replace(adict[match.group(1)], adict, find)
          astring = astring[:match.start()] + matchStr + stringEnd
        match = expr.search(astring, len(astring) - len(stringEnd))
      return astring    

class PT(Test):
    def __init__(self):
        self.re_iq_info1 = "Pat:\s+%s\s+\(%s\)" % (self.re_name, self.re_mrn)
        self.re_iq_info2 = "%s\s+COLL:\s+%s\s+%s\s+REC:" % (self.re_acc, self.re_date, self.re_time)
        self.re_result_value = "([\d\.]+)"
        self.re_iq_inr = "INT'L NORMLIZ RATIO\s+([\w\*]{0,2})\s+%s\s+([\[\]\w\d\.\-]+)" % self.re_result_value

        super(PT, self).__init__()

    def parse_text(self, text):
        patients = {}
        # discard the patient info leading up to the first test
        rslts = text.split("TEST-")[1:]
        for rslt in rslts:
            ids = re.findall(self.re_iq_info1, rslt)
            name, mrn = ids.pop(0)
            results = {}
            accs = re.finditer(self.re_iq_info2, rslt)
            ress = [i for i in re.finditer(self.re_iq_inr, rslt)]
            res_i = 0
                    
            for acc in accs:
                # if the accession and the result are too far apart, there is a problem
                if res_i < len(ress):
                    res = ress[res_i]
                else:
                    raise ValueError("Accession %s beyond last result" % str(acc.groups()))
                print res.start() - acc.start()
                print acc.start(), res.start(), acc.groups(), res.groups()
                credit = re.search('REQUEST CREDITED', rslt[acc.start():res.start()])
                    # if there is a credit then the next accession is the right one
                if credit is not None:
                        continue
                if res.start() - acc.start() < 0:
                    raise ValueError("Could not parse result %s" % str(res.groups()))
                acc, accdate, acctime = acc.groups()
                accdatetime = datetime.strptime(accdate + ' ' + acctime, '%m/%d/%Y %H:%M')
                flag, val, ref = res.groups()
                results[accdatetime] = {'acc': acc,
                                        'name': name,
                                        'mrn': mrn,
                                        'date': accdatetime,
                                        'val': Result(val, flag, {'ref': ref})
                                        }
                # next iteration
                res_i += 1

            patients[mrn] = results
        self.patients = patients
        return patients

    def get_latest(self):
        latest_pts = {}
        for i in self.patients:
            times = self.patients[i].keys()
            times.sort(reverse=True)
            if len(times) > 0:
                print times
                latest_pts[i] = self.patients[i][times[0]]
            else:
                latest_pts[i] = None
        return latest_pts

class HEXA(Test):
    re_result = "{HEXA([\s\w]+)"
    rvvt_result = {'POS': 'also positive', 'NEG': 'negative', 'EQUIV': 'equivocal'}
    positive = "templates/HEXA Positive.txt"
    negative = "templates/HEXA Negative.txt"

    def make_reports(self, rvvt_results, outdir='.'):
        for interpreted_result in self.interpret(rvvt_results):
            template = interpreted_result.pop('template')
            text = super(HEXA, self).make_reports(template, interpreted_result)
            outfile = interpreted_result['identifier'] + ' HEXA.txt'
            f = open(path.join(outdir, outfile), 'wU')
            f.write(text.replace('\n', '\r\n'))
            f.close()

    def interpret(self, rvvt_results):
        for acc in self.results:
            template_args = {}
            template_args['identifier'] = self.make_identifier(acc)
            if acc in rvvt_results:
                template_args['rvvt_result'] = hexa_rvvt_vals[rvvt_results[acc]['result']]
            else:
                # TODO:  check to see if the value is _always_ negative if not returned
                template_args['rvvt_result'] = hexa_rvvt_vals['NEG']
            if self.results[acc]['result'].strip() == "POS":
                template_args['template'] = self.positive
            elif self.results[acc]['result'].strip() == "EQHEX":
                template_args['template'] = self.equivalent
            else:
                print "result not interpretable: %s\n%s" % (self.results[acc]['result'], i)
                import pdb; pdb.set_trace()
            yield template_args

class RVVT(Test):
    result_names = ["DVVTS", "DISS", "DVVN", "ISR", "DVVCS", "DVVCR"]
    re_result = "\s+".join(["{%s([\s\d\.\,\*\w]+) \(RVVTD,6910\)" % name for name in result_names])

    hexa_result = {'POS': 'also positive', 'NEG': 'negative', 'EQUIV': 'equivocal'}
    strong_positive = "; in this sample a false positive is however unlikely given the strength of the positive result."
    both_neg = "Given the negative results in both the RVVT and Lupus Anticoagulant by HEXA assays, the findings are negative for Lupus Anticoagulant."

    positive = "tempates/RVVT Positive.txt"
    equivocal = "tempates/RVVT Equivocal.txt"
    borderline_negative = "tempates/RVVT Borderline.txt"
    negative = "tempates/RVVT Negative.txt"


    equiv_paragraph = {'MANUFACTURER':  """The RVVT test is positive for lupus anticoagulant according to the manufacturer’s guidelines for the interpretation of test results.   However, the RVVT test does not meet criteria for lupus anticoagulant according to published international guidelines (J Thromb Haemost 2009; 7: 1737-40).  The result is therefore EQUIVOCAL.""",
                       'ISTH': """The RVVT test is negative for lupus anticoagulant according to the manufacturer’s guidelines for the interpretation of test results.   However, the results appear to be meet criteria for lupus anticoagulant according to published international guidelines (J Thromb Haemost 2009; 7: 1737-40).   The results are therefore EQUIVOCAL. """,
                       'ISTH PT': """Although the RVVT test is positive for lupus anticoagulant according to the manufacturer’s guidelines for interpretation, review of the clinical history indicates [current warfarin therapy/a prolonged prothrombin time] and the results do not definitively demonstrate an inhibitor, a criterion for lupus anticoagulant according to published international guidelines (J Thromb Haemost 2009; 7: 1737-40).  Therefore, the result is EQUIVOCAL."""}
 
    MANUF_THRESH = {'DVVTS': 43.2, 'DVVCR': 1.17}
    ISTH_THRESH = {'DVVTS': 44.5, 'DVVCR': 1.07}
    DISS_ALT = 44.5
    DISS_THRESH = 41.6
    
    def parse_result(self, result):
        rdict = {}
        for i in range(len(result)):
            rdict[self.result_names[i]] = RVVTResult(result[i])
        return rdict

    def requires_pt(self):
        pt_mrns = []
        for test in self.results.values():
            if test['result']['DVVCR'] > self.ISTH_THRESH['DVVCR']:
                if self.DISS_THRESH < test['result']['DISS'] <= self.DISS_ALT:
                    pt_mrns.append(test['mrn'])
        return pt_mrns

    def interpret(self, latest_pts):
        for test in self.results.values():
    
        # if PTT prolonged
        pass
        # PL dependent
    
