from outputGridScan_aux import outputDataDict
import sys
# Keys definition
stau = "m(stau)"
chi = "m(chi1)"
off = "officialUL"
pyhf = "pyhfUL"
dis = "discrepancy"
dash = "---"
markdownTab = f"|{'m(stau) [GeV]':^15s}|{'m(chi1) [GeV]':^15s}|{'official 95% UL [pb]':^22s}|{'pyhf 95% UL [pb]':^18s}|{'discrepancy [%]':^18s}|\n"
markdownTab += f"|{dash:^15s}|{dash:^15s}|{dash:^22s}|{dash:^18s}|{dash:^18s}|\n"
formatter = "|{:<15.0f}|{:<15.0f}|{:<22.5f}|{:<18.5f}|{:<18.1f}|\n"
for d in outputDataDict:
    markdownTab += formatter.format(d[stau], d[chi], d[off], d[pyhf], d[dis]*100)
with open("ULtab-aux.txt", "w") as output:
    output.write(markdownTab)
