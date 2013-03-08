from datetime import datetime
from operator import itemgetter

def bbank(unitno):
    if unitno[:8] == 'W1170 12' or unitno[:7] == 'W117012':
        return 'BCP'
    else:
        return ''

def pltct_eventtime(piece, data, ident, date):
    for line in piece.split('\n'):
        if len(line) == 0 or '(continued from previous page)' in line:
            try:
                date = datetime(int(line[6:10]), int(line[0:2]), 
                                int(line[3:5]))
            except ValueError:
                pass
            continue
        elif line[0] != ' ':
            date = datetime(int(line[6:10]), int(line[0:2]), 
                            int(line[3:5]), int(line[12:14]), 
                            int(line[14:16]))
        else:
            # year/month/day same as previous date
            if len(line)>12 and line[12] != ' ':
                date = datetime(date.year, date.month, date.day, 
                                int(line[12:14]), int(line[14:16]))
        acc = line[20:26]
        # line[31] is where the unit number should be
        if line[31] == ' ':
            # skip adding this platelet count if it is listed as 'credit'
            if line[60:67].strip() not in ['credit', 'pend']:
                plt = {'date': date, 'acc': acc, 'count': line[60:67].strip()}
                data[ident].setdefault('plt', []).append({'date': plt['date'], 'count': plt['count']})
        else:
            unit = {'unit': line[31:39].strip().split(),
                    'comp': line[39:49].strip(),
                    'vol': line[50:56].strip(),
                    'date': date}
            data[ident].setdefault('units', []).append(unit)
    # hold onto the last platelet and prevunit status in case
    # we are spanning pages
    return date

def pltct_pltids(piece, data, ident):
    for line in piece.split('\n'):
        line = line.split()
        if len(line) == 0:
            continue
        for plt in data[ident]['plt']:
            if plt['count'] == line[0]:
                plt['count'] = line[2]

def pltct_unitids(piece, data, ident):
    for line in piece.split('\n'):
        line = line.split()
        if len(line) == 0:
            continue
        for unit in data[ident]['units']:
            if unit['unit'][1] == line[0]:
                unit['unit'] = "%s %s %s" % tuple(line[1:4])

def pltct(reports):
    rptheader = """===============================================================================
HOSP NO.   PATIENT NAME            AGE   SEX
(HOSP ID)
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
    rptdata = []
    for rpt in reports:
        data = {}
        sections = rpt.split(rptheader)
        prevident = None
        for section in sections:
            pieces = section.split('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n')
            # there should be at least 3 pieces in a valid section
            if len(pieces) == 1:  continue
            identity = pieces[0].split('\n')[0].split()
            # set the identifier to be used by the system
            # must be a tuple because lists are unhashable
            ident = tuple(identity[:2])
            if ident != prevident:
                data[ident] = {'sex': identity[-1]}
                # as long as identity is the same, 
                # carry the date over to the 
                # next section, don't reset
                # this is because sections can span pages
                date = None
                prevident = ident
            for piece in pieces[1:]:
                piece_check = piece.split('\n')
                if len(piece_check[0]) == 0:
                    continue
                elif piece_check[0].split()[0] == "UNIT":
                    pltct_unitids(piece, data, ident)
                elif piece_check[0] == '(continued from previous page)':
                    if piece_check[1].split()[0][1] == "F" or piece_check[1].split()[0] == "UNIT":
                        pltct_unitids(piece, data, ident)
                    elif piece_check[1].split()[0][1] == "T":
                        pltct_pltids(piece, data, ident)
                    else:
                        date = pltct_eventtime(piece, data, ident, date)
                elif piece_check[0].split()[0][1] == "T":
                    pltct_pltids(piece, data, ident)
                else:
                    date = pltct_eventtime(piece, data, ident, date)
        for ident in data:
            data[ident]['units'].sort(key=itemgetter('date'))
            for i in range(len(data[ident]['plt']) -1, -1, -1):
                # remove entries marked as "credit" since there is no valid lab value
                if data[ident]['plt'][i]['count'] == "credit":
                    data[ident]['plt'].pop(i)
            data[ident]['plt'].sort(key=itemgetter('date'))
        rptdata.append(data)
    return rptdata

def pdtlist(reports):
    rptheader = """               UNIT NO.                     SUPPLIER/DESTINATION      COMPONENT TYPE        Dv  ABO/RH    CONTAINER VOL.     EXP.

"""
    now = datetime.today()
    rptdata = []
    for rpt in reports:
        data = {}
        sections = rpt.split(rptheader)
        prevident = None
        for section in sections:
            lines = section.split('\n')
            for entry in range(len(lines)-2):
                try:
                    unit = {'unit': lines[entry][15:30], 
                            'org': lines[entry][44:64], 
                            'comp': lines[entry][70:90].strip(), 
                            'div': lines[entry][92:94], 
                            'type': lines[entry][96:102], 
                            'vol': lines[entry][116:119],
                            'expires': lines[entry][124:].strip(),
                            'pltcount': ''
                    }

                except IndexError:
                    continue
                # check to make sure this is a real unit
                if not(unit['comp'] == unit['comp'].upper()) or len(unit['expires']) == 0:
                    continue

                offset = 1
                for offset in range(1,5):
                    nextline = lines[entry + offset].split()
                    if len(nextline) <=1:
                        break
                    if nextline[0] == 'COMMENTS':
                        unit['pltcount'] = lines[entry + offset][33:]
                    elif nextline[0] == 'ATTRIBUTES':
                        pass
                    elif nextline[0] == 'ASSIGNEE':
                        # ident = (MRN, NAME)
                        ident = (lines[entry + offset][30:38], lines[entry + offset][48:80].split()[0])
                        unit['expires']= datetime(int(lines[entry + offset][86:90]), int(lines[entry + offset][80:82]),int(lines[entry + offset][83:85]), 23, 59)
                        if unit['expires'] > now:
                            if not(ident in data):
                                patient = {'info':  lines[entry + offset + 1][51:].strip()}
                                data[ident] = {'units': {
                                        unit['unit'] + unit['comp']: unit}
                                               }
                                data[ident].update(patient)
                            else:
                                data[ident]['units'][unit['unit'] 
                                                     + unit['comp']] = unit
                    else:
                        break
                data[unit['unit'] + unit['comp']] = unit
        rptdata.append(data)
    return rptdata

def format_platelet_summary(rptdata):
    pdtdata = {}
    for data in rptdata['BLOOD BANK - PRODUCT FILELIST\tFor Hospital P']:
        pdtdata.update(data)
    for report in rptdata['BLOOD BANK - TRANSFUSION EPISODE REPORT\tPLATELET COUNTS']:
        for ident in report:
            for unit in report[ident]['units']:
                # get unit blood type and plt count
                # unit key = DIN# + comp
                try:
                    unitkey = unit['unit'] + unit['comp']
                except TypeError:
                    import pdb; pdb.set_trace()
                # if the unit is in the product list
                if unitkey in pdtdata:
                    if ident in pdtdata and unitkey in pdtdata[ident]['units']:
                        # if this unit is one of the crossmatched units, 
                        # it has already been transfused so remove it
                        del pdtdata[ident]['units'][unitkey]
                    pdtunit = pdtdata[unitkey]
                    unit['type'] = pdtunit['type']
                    if 'pltcount' in pdtunit:
                        unit['pltcount'] = pdtunit['pltcount']
                    else:
                        unit['pltcount'] = 'N/A'
                else:
                    # unit not found
                    import pdb; pdb.set_trace()
                # assign pre and post counts
                plts = report[ident]['plt']
                if plts[-1]['date'] < unit['date']:
                    unit['pre'] = plts[-1]['count']
                    unit['comments'] = unit.get('comments', '') + 'no post'
                else:
                    for i in range(len(plts)):
                        if plts[i]['date'] > unit['date']:
                            unit['post'] = plts[i]['count']
                            unit['comments'] = unit.get('comments', '') + 'post +%2.1fh ' % (
                                (plts[i]['date'] - unit['date']).total_seconds() / 3600)
                            # if the post is less than 1.5h from issue time, record 2nd post
                            if (plts[i]['date'] - unit['date']).total_seconds() < 3600 * 1.5 and i+1 < len(plts):
                                unit['comments'] += ' 2nd post %s at %s' % (plts[i+1]['count'], plts[i+1]['date'])
                            if i > 0:
                                unit['pre'] = plts[i-1]['count']
                                if plts[i-1]['date'].hour == 2 and plts[i-1]['date'].minute == 22:
                                    unit['comments'] = unit.get('comments', '') + 'pre 222 '
                            if plts[i]['date'].hour == 2 and plts[i]['date'].minute == 22:
                                unit['comments'] = unit.get('comments', '') + 'post 222 '
                            break

def print_platelet_summary(rptdata, buffer):
    outformat = '%s\t%s\t%s\t\t%s\t%s\t\t%s\t%s\t\t%s\t%s\t\n'
    for report in rptdata['BLOOD BANK - TRANSFUSION EPISODE REPORT\tPLATELET COUNTS']:
        for ident in report:
            buffer.write('%s\t%s\n\nDate\tUnit\tComponent\t\tType\tLocation\t\tPre\tPost\tCCI\tUnit Count\tComments\n' % ident)
            for unit in report[ident]['units']:
                try:
                    buffer.write(outformat % (unit['date'], unit['unit'], unit['comp'], unit['type'], bbank(unit['unit']), unit['pre'], unit.get('post', ''), unit['pltcount'], unit['comments']))
                except:
                    import pdb; pdb.set_trace()
            for pdtreport in rptdata['BLOOD BANK - PRODUCT FILELIST\tFor Hospital P']:
                buffer.write('\nDate\tUnit\tComponent\t\tType\tLocation\t\t\t\t\tUnit Count\tExpires\n')
                if ident in pdtreport:
                    allocated = pdtreport[ident]['units'].values()
                    allocated.sort(key=itemgetter('expires'))
                    for unit in allocated:
                        if len(unit) == 0:
                            continue
                        buffer.write(outformat % ('', unit['unit'], unit['comp'], unit['type'], bbank(unit['unit']), '', '', unit['pltcount'], unit['expires']))
            buffer.write('\n\n')
            
def extract_data(report_types):
    rptdata = {}
    for i in report_types:
        if i == 'BLOOD BANK - CURRENTLY ALLOCATED UNITS\t':
            pass
        elif i == 'BLOOD BANK - TRANSFUSION EPISODE REPORT\tPLATELET COUNTS':
            rptdata[i] = pltct(report_types[i])
        elif i == 'BLOOD BANK - PRODUCT FILELIST\tFor Hospital P':
            rptdata[i] = pdtlist(report_types[i])

    return rptdata

def get_reports(fileName):
    f = open(fileName)
    header = "UCSF MEDICAL CENTER CLINICAL LABORATORIES"
    reports = {}
    currpt = ""
    for line in f:
        if header in line.strip():
            f.next()
            f.next()
            name = f.next().strip() + "\t" + f.next().strip()
            f.next()
            f.next()
            if currpt is None:
                currpt = ""
        elif "REPORT COMPLETED" in line.strip():
            reports.setdefault(name, []).append(currpt)
            currpt = None
        elif currpt is not None:
            currpt += line.replace('\r\n', '\n')
    if currpt is not None:
        reports.setdefault(name, []).append(currpt)
    return reports

def run_rpts(infile, outfile):
    rpts = get_reports(infile)
    data = extract_data(rpts)
    format_platelet_summary(data)
    f = open(outfile, 'w')
    print_platelet_summary(data, f)
    f.close()


if __name__ == '__main__':
    infile = 'TRIAL.txt'
    outfile = 'PLTCT report.tsv'
    run_rpts(infile, outfile)
