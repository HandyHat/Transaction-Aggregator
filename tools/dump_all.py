import sys, json, openpyxl
wb = openpyxl.load_workbook(sys.argv[1], data_only=True, read_only=True)
rows = list(wb.worksheets[0].iter_rows(values_only=True))[1:]
json.dump([[r[0], r[1], r[3], r[4].split('|')[1].strip(), r[5].strftime('%Y-%m-%d'), r[6].strip(), r[7], round(r[8], 2), '' if r[9] == 'None' else r[9].replace(' (simulated)', ''), round(r[10], 2)] for r in rows], open(sys.argv[2], 'w'))
