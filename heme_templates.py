class Template(object):
    date_re = "(\d\d\/\d\d\/\d\d\d\d)"
    info_re = "\s+(\w+)\s+%s\s+(\d{4,4})\s+([\w\-\,]+)\s+(\d+)\s+\w+\s+%s" % (date_re, date_re)

    def make_report(template, **vars):
        f = open(self.__getattribute__(template))
        text = f.read()
        f.close()
        return self.replace(text, vars)

    def parse_result(self, result):
        return j

    def parse_worksheet(self, text):
        results = {}
        for i, j in zip(re.findall(self.info_re, text), re.findall(self.result_re, text)):
            acc, accdate, acctime, name, mrn, bdate = i
            results[acc] = {'acc': acc,
                          'accdate': accdate.replace('/','.'),
                          'acctime': acctime,
                          'name': name,
                          'mrn': mrn,
                          'bdate': bdate.replace('/','.'),
                          'result': self.parse_result(j)
                          }
        self.results = results
        return results
    
    def make_identifier(self, acc):
        id_args = [self.results[acc][i] for i in ['name', 'mrn', 'acc', 'accdate']]
        return = "%s %s %s %s" % tuple(id_args)

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

class HEXA(Template):
    result_re = "{HEXA([\s\w]+)"
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

class RVVT(Template):
    result_names = ["DVVTS", "DISS", "DVVN", "ISR", "DVVCS", "DVVCR"]
    result_re = "\s+".join(["{%s([\s\d\.\,\*\w]+) \(RVVTD,6910\)" % name for name in result_names])

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
    
    def interpret(self, pts):
        MANUF_THRESH = {'DVVTS': 43.2, 'DVVCR': 1.17}
        ISTH_THRESH = {'DVVTS': 44.5, 'DVVCR': 1.07}
        DISS_ALT = 44.5
        DISS_THRESH = 41.6
    
        for name, res in zip(rvvt_names, test['result']):
           val[name] = float(res.split(',')[0])
        # if PTT prolonged
        pass
        # PL dependent
    
