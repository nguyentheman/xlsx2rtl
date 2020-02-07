import pandas as pd

# set file path
filepath="./test/test.xlsx"
csr_vh = "./test/csr.vh"
csr_v  = "./test/csr.v"

#load workbook
wb = pd.read_excel(io=filepath,sheet_name=0,usecols=['Type','Field','Bit Range', 'Reset Value','Access'])
#print(wb.columns.ravel())
#print(wb['Type'])
#print(wb)

#select register rows
regs_start = wb[wb['Type'] == 'register'].index.values
regs_end   = wb[wb['Type'] == 'comment'].index.values
assert(len(regs_start) == len(regs_end)) , "Number of 'register' and 'comment' has not equal!!!"

#Get parameter
param_idx = wb[wb['Type'] =='parameter'].index.values
dsgn_block = wb.iloc[param_idx[0]]['Field'      ]
addr_width = wb.iloc[param_idx[0]]['Bit Range'  ]
data_width = wb.iloc[param_idx[0]]['Reset Value']
assert (len(param_idx) == 1), "Invalid paramter block!!!"

#Create address_define.vh
f = open(csr_vh,"w")
for i in range(0,len(regs_start)) :
    wstr = "`define"                                  + " " 
    wstr = wstr + wb.iloc[regs_start[i]]['Field'    ] + " " 
    wstr = wstr + wb.iloc[regs_start[i]]['Bit Range'].replace('0x',str(addr_width)+'\'h') + "\n"
    f.write(wstr)
f.close()

#Create csr.v
#for i in range(0,len(regs_start)) :
#    reg = wb.iloc[regs_start[i]:regs_end[i]]
#    print(reg)