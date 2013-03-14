# coding: utf-8
import re
from datetime import datetime
from os import path

class Result(float):
    def __new__(self, val, flag=None, other={}):
        self.flag = flag
        self.other = other
        return super(Result, self).__new__(self, val)

class RVVTresult(Result):
    def __new__(self, result):
        res = result.split(',')
        if len(res) == 1:
            return super(RVVTresult, self).__new__(self, res[0])
        if len(res) == 2:
            return super(RVVTresult, self).__new__(self, res[0], other={'st': res[1]})
        elif len(res) == 3:
            return super(RVVTresult, self).__new__(self, res[0], flag=res[2])
        else:
            raise ValueError("cannot parse result: %s" % result)

class HEXAresult(str):
    def __new__(self, val, flag=None, other={}):
        self.flag = flag
        self.other = other
        return super(HEXAresult, self).__new__(self, val)

class Test(object):
    re_date = "(\d\d\/\d\d\/\d\d\d\d)"
    re_time = "([\d\:]+)"
    re_name = "([\w\-\,]+)"
    re_acc = "(\w\d+)"
    re_mrn = "(\d+)"
    re_wo_info1 = "\s+".join([re_acc, re_date, re_time, re_name])
    re_wo_info2 = "\s+%s\s+\w+\s+%s" % (re_mrn, re_date)

    # TODO:  consolidate the make_reports functions to this
    # def make_report(template, **vars):
    #     f = open(self.__getattribute__(template))
    #     text = f.read()
    #     f.close()
    #     return self.replace(text, vars)

    def parse_result(self, result):
        return Result(result)

    def parse_text(self, text):
        results = {}
        # info1 = [i for i in re.finditer(self.re_wo_info1, text)]
        # info2 = [i for i in re.finditer(self.re_wo_info2, text)]
        # result = [i for i in re.finditer(self.re_result, text)]
        # import pdb; pdb.set_trace()
        for i, j, k in zip(re.finditer(self.re_wo_info1, text), re.finditer(self.re_wo_info2, text), re.finditer(self.re_result, text)):
            # sanity check to make sure the regex results are near each other
            # if wo_info2.start() - wo_info1.start() < 0 or > 200 these are likely from different entries
            # if re_result.start() - wo_info2.start() < 0 or > 400 these are likely from different entries
            
            if j.start() - i.start() < 0 or j.start() - i.start() > 200:
                raise ValueError("error parsing result near position %s" % min(i.start(), j.start()))
            if k.start() - j.start() < 0 or k.start() - j.start() > 400:
                raise ValueError("error parsing result near position %s" % min(j.start(), k.start()))
            
            acc, accdate, acctime, name = i.groups()
            if len(acctime) == 4:
                acctime = acctime[:2] + ':' + acctime[2:]
            mrn, bdate = j.groups()
            results[acc] = {'acc': acc,
                            'accdate': datetime.strptime(accdate + ' ' + acctime, '%m/%d/%Y %H:%M'),
                          'name': name,
                          'mrn': mrn,
                          'bdate': datetime.strptime(bdate, '%m/%d/%Y'),
                          'result': self.parse_result(k.groups())
                          }
        self.results = results
        return results

    def make_identifier(self, acc):
        id_args = [self.results[acc][i] for i in ['name', 'mrn', 'acc']]
        id_args.append(self.results[acc]['accdate'].strftime('%Y.%m.%d.%H.%M'))
        return "%s %s %s %s" % tuple(id_args)

    def make_report(self, acc, report_text, test_name, outdir, for_review=False):
        nametext = self.make_identifier(acc)
        if for_review:
            f = open(path.join(outdir, '__review__%s.%s.txt' % (nametext, test_name)),'w')
        else:
            f = open(path.join(outdir, '%s.%s.txt' % (nametext, test_name)),'w')
        f.write(report_text)
        f.close()

    def make_reports(self, report_text, test_name, outdir):
        for result in self.results.values():
            self.make_report(result['acc'], report_text, test_name, outdir)

    def replace(self, astring, adict, find=r"<(\w+)>"):
      expr = re.compile(find, re.M)
      astring= str(astring)
      match = expr.search(astring)
      while match is not None:
        stringEnd = astring[match.end():]
        if match.group(1) in adict:
          matchStr = self.replace(adict[match.group(1)], adict, find)
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
                    credit = re.search('REQUEST CREDITED', rslt[acc.start():acc.start()+700])
                    if credit is not None:
                        continue
                    raise ValueError("Accession %s beyond last result" % str(acc.groups()))
                
                print res.start() - acc.start()
                print acc.start(), res.start(), acc.groups(), res.groups()
                # if there is a credit between acc and res then go to the next acc
                credit = re.search('REQUEST CREDITED', rslt[acc.start():res.start()])

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
                                        'accdate': accdatetime,
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
    re_result = "{HEXA\s+(\w+)"
    rvvt_result = {'POS': 'positive', 'NEG': 'negative', 'EQUIV': 'equivocal', 'BORDERNEG': 'borderline negative'}
    positive = open("templates/HEXA Positive.txt").read()
    negative = open("templates/HEXA Negative.txt").read()
    equivocal = open("templates/HEXA Equivocal.txt").read()


    def parse_result(self, result):
        return HEXAresult(result[0])

    def make_reports(self, rvvt, inr, outdir):
        rvvt.interpret(inr)
        for result, args in self.interpret():
            # don't need to make a report if negative
            if args['result'] == 'NEG':
                continue
            if result['acc'] in rvvt.results:
                rvvtr = rvvt.interpretations[result['acc']]['result']
                args['rvvt_result'] = self.rvvt_result[rvvtr]
                if rvvtr == 'NEG' and args['result'] == 'NEG':
                    args['both_neg'] = self.both_neg
                else:
                    args['both_neg'] = ''
            else:
                # TODO:  flag this report for review?
                args['rvvt_result'] = '[positive/equivocal/negative]'
                args['for_review'] = True
            report_text = self.replace(args['template'], args)
            if 'for_review' in args:
                self.make_report(result['acc'], report_text, 'HEXA', outdir, for_review=True)
            else:
                self.make_report(result['acc'], report_text, 'HEXA', outdir)

    def interpret(self):
        self.interpretations = {}
        for acc in self.results:
            template_args = {}
            template_args['identifier'] = self.make_identifier(acc)
            if self.results[acc]['result'].strip() == "POS":
                template_args['result'] = 'POS'
                template_args['template'] = self.positive
            elif self.results[acc]['result'].strip() == "EQHEX":
                template_args['result'] = 'EQUIV'
                template_args['template'] = self.equivocal
            elif self.results[acc]['result'].strip() == "NEG":
                template_args['result'] = 'NEG'
                template_args['template'] = self.negative
            else:
                print "result not interpretable: %s\n%s" % (self.results[acc]['result'], self.results[acc])
                import pdb; pdb.set_trace()
            self.interpretations[acc] = template_args
        return [(self.results[i], self.interpretations[i]) for i in self.results]

class RVVT(Test):
    result_names = ["DVVTS", "DISS", "DVVN", "ISR", "DVVCS", "DVVCR"]
    re_result = "\s+".join(["{%s([\s\d\.\,\*\w]+) \(RVVTD,\d+\)" % name for name in result_names])

    hexa_result = {'POS': 'positive', 'NEG': 'negative', 'EQUIV': 'equivocal'}
    strong_positive = "; in this sample a false positive is however unlikely given the strength of the positive result."
    both_neg = "Given the negative results in both the RVVT and Lupus Anticoagulant by HEXA assays, the findings are negative for Lupus Anticoagulant."

    positive = open("templates/RVVT Positive.txt").read()
    equivocal = open("templates/RVVT Equivocal.txt").read()
    borderline_negative = open("templates/RVVT Borderline.txt").read()
    negative = open("templates/RVVT Negative.txt").read()


    equiv_paragraph = {'MANUFACTURER':  """The RVVT test is positive for lupus anticoagulant according to the manufacturer's guidelines for the interpretation of test results.   However, the RVVT test does not meet criteria for lupus anticoagulant according to published international guidelines (J Thromb Haemost 2009; 7: 1737-40).  The result is therefore EQUIVOCAL.""",
                       'ISTH': """The RVVT test is negative for lupus anticoagulant according to the manufacturer's guidelines for the interpretation of test results.   However, the results appear to be meet criteria for lupus anticoagulant according to published international guidelines (J Thromb Haemost 2009; 7: 1737-40).   The results are therefore EQUIVOCAL. """,
                       'ISTH PT': """Although the RVVT test is positive for lupus anticoagulant according to the manufacturer's guidelines for interpretation, review of the clinical history indicates [current warfarin therapy/a prolonged prothrombin time] and the results do not definitively demonstrate an inhibitor, a criterion for lupus anticoagulant according to published international guidelines (J Thromb Haemost 2009; 7: 1737-40).  Therefore, the result is EQUIVOCAL."""}
 
    MANUF_THRESH = {'DVVTS': 43.2, 'DVVCR': 1.17}
    ISTH_THRESH = {'DVVTS': 44.5, 'DVVCR': 1.07, 'DISS': 41.6}
    DISS_ALT = 44.5
    ISR_ALT = 1.09

    def parse_result(self, result):
        rdict = {}
        for i in range(len(result)):
            rdict[self.result_names[i]] = RVVTresult(result[i])
        return rdict

    def check_thresh(self, result, thresh):
        criteria_met = 0
        for i in thresh:
            if result['result'][i] > thresh[i]:
                criteria_met += 1
        if criteria_met == len(thresh):
            return True
        else:
            return False

    def interpret(self, inr):
        self.interpretations = {}
        latest_pts = inr.get_latest()
        for acc in self.results:
            template_args = {}
            template_args['identifier'] = self.make_identifier(acc)
            result = self.results[acc]
            meets_manuf = self.check_thresh(result, self.MANUF_THRESH)
            meets_isth = self.check_thresh(result, self.ISTH_THRESH)
            
            # if the result is borderline, see if the pt was elevated
            if meets_isth and result['DISS'] < self.DISS_ALT:
                if result['mrn'] in inr.results:
                    if inr.results[result['mrn']]['result'] > 1.2:
                        meets_isth = False

            # determine whether pos, equiv, or neg
            if meets_manuf and meets_isth:
                template_args['result'] = 'POS'
                template_args['template'] = self.positive
            elif meets_manuf and not(meets_isth):
                if result['result']['ISR'] > self.ISR_ALT:
                    template_args['result'] = 'EQUIV'
                    template_args['template'] = self.equivocal
                    template_args['equiv_paragraph'] = self.equiv_paragraph['MANUFACTURER']
                else:
                    template_args['result'] = 'BORDERNEG'
                    template_args['template'] = self.borderline_negative
            elif not(meets_manuf) and meets_isth:
                template_args['result'] = 'EQUIV'
                template_args['template'] = self.equivocal
                template_args['equiv_paragraph'] = self.equiv_paragraph['ISTH']            
            else:
                    template_args['result'] = 'NEG'
                    template_args['template'] = self.negative
                
            # print "result not interpretable: %s\n%s" % (self.results[acc]['result'], i)
            #import pdb; pdb.set_trace()
            self.interpretations[acc] = template_args
        return [(self.results[i], self.interpretations[i]) for i in self.results]

    def requires_inr(self):
        pt_mrns = []
        for test in self.results.values():
            # if test['result']['DVVCR'] > self.ISTH_THRESH['DVVCR']:
            #     if self.DISS_THRESH < test['result']['DISS'] <= self.DISS_ALT:
            pt_mrns.append(test['mrn'])
        return pt_mrns
    
    def make_reports(self, hexa, inr, outdir):
        hexa.interpret()
        for result, args in self.interpret(inr):
            if result['acc'] in hexa.results:
                hexar = hexa.interpretations[result['acc']]['result']
            else:
                # TODO: fix this to download completed results as well
                # assume that the test was negative if not included
                hexar = 'NEG'
            args['hexa_result'] = self.hexa_result[hexar]
            if hexar == 'NEG' and args['result'] == 'NEG':
                args['both_neg'] = self.both_neg
            else:
                args['both_neg'] = ''
            report_text = self.replace(args['template'], args)
            if 'for_review' in args:
                self.make_report(result['acc'], report_text, 'HEXA', outdir, for_review=True)
            else:
                self.make_report(result['acc'], report_text, 'HEXA', outdir)
