import pandas as pd
import re

#-------------------------------------------
# Functions
#-------------------------------------------
def cat_str(*tuple_strs):    
    ostr = tuple_strs[0]
    for i in range(1,len(tuple_strs)):
        ostr = ostr + "_" + tuple_strs[i];
    return ostr

def get_port_list(wb,port_indexs) :
    port_list = list()
    for i in range(0,len(port_indexs)):
        if(wb.iloc[port_indexs[i]]['Field'].lower() != 'reserved') : 
            port_name  = re.sub(r'\[[\s]*\d+[\s\:]*[\s\d]*\]',"",wb.iloc[port_indexs[i]]['Port_Name'])
            bit_indexs = list(map(int,re.findall(r'\d+',wb.iloc[port_indexs[i]]['Port_Name'])))
            lsb = min(bit_indexs)
            msb = max(bit_indexs)
            new_port = True
            for j in range(0,len(port_list)) :
                if(port_name == port_list[j]['port_name']) :
                    new_port = False
                    port_list[j]['lsb'] = min(lsb,port_list[j]['lsb'])
                    port_list[j]['msb'] = max(msb,port_list[j]['msb'])
                    break;
            if(new_port == True) :         
                port_list.append({'port_name' : port_name, 'lsb' : lsb, 'msb': msb})
    return port_list
#-------------------------------------------
# Main Scripts
#-------------------------------------------

# Terminal Arguments
# T.B.D
XLSX_IN   = "./test/test.xlsx"
CSR_TEMP  = "./test/csr_templete.v"

#load workbook
filepath = XLSX_IN
wb = pd.read_excel(io=filepath,sheet_name="register_set",usecols=['Type','Field','Bit_Range', 'Reset_Value','Access','Port_Name'])

#-------------------------------------------------------------------------------
# Get design parameter
#-------------------------------------------------------------------------------

# get design parameter
param_idx = wb[wb['Type'] =='parameter'].index.values
dsgn_name  = wb.iloc[param_idx[0]]['Field'      ]
addr_width = wb.iloc[param_idx[0]]['Bit_Range'  ]
data_width = wb.iloc[param_idx[0]]['Reset_Value']

# input validation
assert (len(param_idx) == 1), "Invalid parameter block!!!"
assert (wb.isna().iloc[param_idx[0]]['Field'      ] == False and isinstance(dsgn_name,str) == True), "DESIGN_NAME must be input as string !!!"
assert (wb.isna().iloc[param_idx[0]]['Bit_Range'  ] == False and isinstance(addr_width,int)== True), "ADDR_WIDTH value must be integer !!!"
assert (wb.isna().iloc[param_idx[0]]['Reset_Value'] == False and isinstance(data_width,int)== True), "DATA_WIDTH value must be integer !!!"

# Program paramters
pf_csr_vh   = dsgn_name.lower() + "_csr.vh"
pf_csr_v    = dsgn_name.lower() + "_csr.v"

#-------------------------------------------------------------------------------
# Create csr.vh
#-------------------------------------------------------------------------------
#select register rows
regs_start = wb[wb['Type'] == 'register'].index.values
regs_end   = wb[wb['Type'] == 'comment'].index.values
assert(len(regs_start) == len(regs_end)) , "Missing 'register' or 'comment' field !!!!"

# Create csr.vh
f_csr_vh = open(pf_csr_vh,"w")
wstr = "`ifndef " + "__" + dsgn_name.upper() + "_CSR_" + "VH__\n"
wstr += "`define " + "__" + dsgn_name.upper() + "_CSR_" + "VH__\n\n\n"
f_csr_vh.write(wstr)
for i in range(0,len(regs_start)) :
    wstr = "`define "
    wstr = wstr + cat_str("ADDR",wb.iloc[regs_start[i]]['Field'].upper()) + " " 
    wstr = wstr + wb.iloc[regs_start[i]]['Bit_Range'].replace('0x',str(addr_width)+'\'h') + "\n"
    f_csr_vh.write(wstr)
f_csr_vh.write("\n\n`endif\n")
f_csr_vh.close()

#-------------------------------------------------------------------------------
# Create csr.v
# FIXME: below solution will consume huge ram when sovling a big register set
#-------------------------------------------------------------------------------

# open templete file for edit
f_csr_temp = open(CSR_TEMP,"rt");
vcode = f_csr_temp.read();
f_csr_temp.close();

# get RTL code patterns
REGEX_TO_DETECT_MULTI_LINE_REG_PATTERN = r'[\s]*__LOOP_START__[\s\r\n]*[\s\S]*?__LOOP_END__[\s\r\n]*'
reg_loop_patterns =  re.findall(REGEX_TO_DETECT_MULTI_LINE_REG_PATTERN,vcode)
#print(reg_loop_patterns[0])
#print(reg_loop_patterns[1])

reg_declare_blk = ""
cfg_assign_blk  = ""
sts_assign_blk  = ""
rtl_insert_lists = [""]*len(reg_loop_patterns)
for i in range(0,len(regs_start)) :
    reg_name        = wb.iloc[regs_start[i]]['Field']
    reg_fields      = wb.iloc[regs_start[i]+1:regs_end[i]]

    # calculate register's reset value and register's bit-widht
    reg_rst_value   = 0x0;
    reg_bit_width   = 0x0;
    for j in range(0,len(reg_fields)): # loop for-each row
        field_name      = reg_fields.iloc[j]['Field'      ]
        bit_range       = reg_fields.iloc[j]['Bit_Range'  ]
        acc_type        = reg_fields.iloc[j]['Access'     ]
        field_rst_value = reg_fields.iloc[j]['Reset_Value'] 
        if(field_name.lower() != 'reserved') :
            # validate register 's field inputs
            assert(reg_fields.iloc[j]['Type'] == 'field'), "register '" + reg_name + "' has invalid format!!!"
            assert(acc_type in {'RW','RO','WO'}), "field '" + field_name + "' of register '" + reg_name + "' has invalid Access type!!!"
            assert(re.match(r'^0x[0-9a-fA-F]$',field_rst_value)), "field '" + field_name + "' of register '" + reg_name + "' has invalid Reset_Value!!!"

            #extract bit-position
            bit_indexs = list(map(int,re.findall(r'\d+',bit_range)))
            num_indexs = len(bit_indexs)
            if(num_indexs == 1): bit_indexs.append(0) # append dummy value to avoid syntax error
            assert(num_indexs in [1,2] and bit_indexs[0] >= bit_indexs[1]), "field '" + field_name + "' of register '" + reg_name + "' has invalid Bit_Range!!!"

            # calulate register reset value
            int_field_rst_value = int(field_rst_value,0)
            if(num_indexs == 1 or bit_indexs[0] == bit_indexs[1]):
                reg_rst_value += (int_field_rst_value & 0x1) << bit_indexs[0]
                reg_bit_width += 1
            else:
                bit_width = (bit_indexs[0] - bit_indexs[1]) + 1
                bit_mask  = (2**data_width-1) >> (data_width - bit_width)
                reg_rst_value += (int_field_rst_value & bit_mask) << min(bit_indexs)
                reg_bit_width += bit_width
                #print("reg_rst_value \t= " + hex(reg_rst_value) + "\t\t;bit_mask \t= " + hex(bit_mask))

    #generate RTL code
    for k in range(0,len(reg_loop_patterns)) :
        rtl_pat = reg_loop_patterns[k] #get pattern of the RTL code
        rtl_code = re.sub(r'.*__LOOP_START__.*[\r\n]|.*__LOOP_END__.*[\r\n]',"",rtl_pat) #remove __LOOP_START__ and __LOOP_END__
        #----------------------------
        # Generate RTL code
        #----------------------------
        reg_reset_pattern = r'.*\${__REG_VAR__}.*<=.*\${__REG_RESET_VALUE__}.*[\r\n]'
        reg_write_pattern = r'.*\${__REG_VAR__}.*<=.*[\r\n]'
        reg_read_pattern  = r'.*=.*\${__REG_VAR__}.*[\r\n]'
        #find out reset-patern, then replace it
        rtl_rst_pat = re.findall(reg_reset_pattern,rtl_code)
        if (len(rtl_rst_pat) == 1 ) :
            rtl_rst_code = rtl_rst_pat[0]
            rtl_rst_code = rtl_rst_code.replace("${__REG_RESET_VALUE__}",hex(reg_rst_value).replace("0x",str(reg_bit_width)+"'h"))
            rtl_rst_code = rtl_rst_code.replace("${__REG_VAR__}",cat_str("var",reg_name.lower()))
            rtl_code = rtl_code.replace(rtl_rst_pat[0],rtl_rst_code)

        #find out write-patern, then replace it
        rtl_wr_pat  = re.findall(reg_write_pattern,rtl_code)
        if (len(rtl_wr_pat) == 1 ) :
            rtl_wr_code = ""
            for j in range(0,len(reg_fields)): # loop for-each row
                field_name = reg_fields.iloc[j]['Field'      ]
                bit_range  = reg_fields.iloc[j]['Bit_Range'  ]
                acc_type   = reg_fields.iloc[j]['Access'     ]
                port_name  = reg_fields.iloc[j]['Port_Name'  ]
                if(field_name.lower() != 'reserved') :
                    if(re.match(r'RW',acc_type) or re.match(r'WO',acc_type)):
                        rtl_wr_code_tmp = rtl_wr_pat[0]
                        rtl_wr_code_tmp = rtl_wr_code_tmp.replace("${__REG_VAR__}",cat_str("var",reg_name.lower()))
                        rtl_wr_code_tmp = rtl_wr_code_tmp.replace("[${__REG_RANGE__}]",bit_range)
                        rtl_wr_code_tmp = rtl_wr_code_tmp.replace("${__FIELD_NAME__}",field_name)
                        rtl_wr_code += rtl_wr_code_tmp

                        # generate CSR assign blocks
                        rtl_asgn_pat = re.findall(r'.*__CSR_ASSIGN_BLK__.*[\r\n]',vcode)
                        rtl_asgn_str = "assign " + port_name + " = " + cat_str("var",reg_name.lower()) + bit_range + ";"
                        rtl_asgn_code = rtl_asgn_pat[0].replace("__CSR_ASSIGN_BLK__",rtl_asgn_str)
                        cfg_assign_blk += rtl_asgn_code
            rtl_code = rtl_code.replace(rtl_wr_pat[0],rtl_wr_code)

        #find out read-pattern, then replace it
        rtl_rd_pat = re.findall(reg_read_pattern ,rtl_code)
        if (len(rtl_rd_pat) == 1 ) :
            rtl_rd_code = ""
            for j in range(0,len(reg_fields)): # loop for-each row
                field_name = reg_fields.iloc[j]['Field'      ]
                bit_range  = reg_fields.iloc[j]['Bit_Range'  ]
                acc_type   = reg_fields.iloc[j]['Access'     ]
                port_name  = reg_fields.iloc[j]['Port_Name'  ]
                if(field_name.lower() != 'reserved') :
                    if(re.match(r'RW',acc_type) or re.match(r'RO',acc_type)):
                        rtl_rd_code_tmp = rtl_rd_pat[0]
                        rtl_rd_code_tmp = rtl_rd_code_tmp.replace("${__REG_VAR__}",cat_str("var",reg_name.lower()))
                        rtl_rd_code_tmp = rtl_rd_code_tmp.replace("[${__REG_RANGE__}]",bit_range)
                        rtl_rd_code_tmp = rtl_rd_code_tmp.replace("${__FIELD_NAME__}",field_name)
                        rtl_rd_code += rtl_rd_code_tmp

                        # generate CSR assign blocks
                        if(re.match(r'RO',acc_type)):
                            rtl_asgn_pat = re.findall(r'.*__CSR_ASSIGN_BLK__.*[\r\n]',vcode)
                            rtl_asgn_str = "assign " + cat_str("var",reg_name.lower()) + bit_range + " = " + port_name + ";" 
                            rtl_asgn_code = rtl_asgn_pat[0].replace("__CSR_ASSIGN_BLK__",rtl_asgn_str)
                            sts_assign_blk += rtl_asgn_code
            rtl_code = rtl_code.replace(rtl_rd_pat[0],rtl_rd_code)

        #find out REG_ADDR, then replace it
        rtl_code = rtl_code.replace("${__REG_ADDR__}",cat_str("`ADDR",reg_name.upper()))
        rtl_insert_lists[k] += rtl_code;

    # generate register defines
    rtl_dclr_pat = re.findall(r'.*__REG_DECLARE_BLK__.*[\r\n]',vcode)
    rtl_dclr_str  = "reg [" + str(reg_bit_width-1) + ":0] " + cat_str("var",reg_name.lower()) + ";"
    rtl_dclr_code = rtl_dclr_pat[0].replace("__REG_DECLARE_BLK__",rtl_dclr_str)
    reg_declare_blk += rtl_dclr_code

#find out Port lists
cfg_port_indexs = wb[wb['Access'].isin(['RW','WO'])].index.values
sts_port_indexs = wb[wb['Access'] == 'RO'].index.values

cfg_port_list = get_port_list(wb,cfg_port_indexs)
sts_port_list = get_port_list(wb,sts_port_indexs)

# generate config port list
rtl_port_list_pat = re.findall(r'.*__CSR_PORT_LIST__.*[\r\n]',vcode)
rtl_port_dclr_pat = re.findall(r'.*__CSR_PORT_DECLARE__.*[\r\n]',vcode)
rtl_port_list_code = ""
rtl_port_dclr_code = ""
for i in range(0,len(cfg_port_list)):
    port_dclr_str = "wire [" + str(cfg_port_list[i]['msb']) + ":" + str(cfg_port_list[i]['lsb']) + "] " + cfg_port_list[i]['port_name'] + ";";
    rtl_port_list_code += rtl_port_list_pat[0].replace("__CSR_PORT_LIST__"   ,cfg_port_list[i]['port_name'])
    rtl_port_dclr_code += rtl_port_dclr_pat[0].replace("__CSR_PORT_DECLARE__",port_dclr_str)

for i in range(0,len(sts_port_list)):
    port_dclr_str = "wire [" + str(sts_port_list[i]['msb']) + ":" + str(sts_port_list[i]['lsb']) + "] " + sts_port_list[i]['port_name'] + ";";
    rtl_port_list_code += rtl_port_list_pat[0].replace("__CSR_PORT_LIST__"   ,sts_port_list[i]['port_name'])
    rtl_port_dclr_code += rtl_port_dclr_pat[0].replace("__CSR_PORT_DECLARE__",port_dclr_str)

# edit templete file
vcode = vcode.replace("${__MODULE_NAME__}"     ,cat_str(dsgn_name.lower(),"csr")  )
vcode = vcode.replace("${__DATA_WIDTH_VAL__}"  ,str(data_width)                 ,1)
vcode = vcode.replace("${__ADDR_WIDTH_VAL__}"  ,str(addr_width)                 ,1)
vcode = re.sub(r'.*__REG_DECLARE_BLK__.*[\r\n]',reg_declare_blk,vcode)
vcode = re.sub(r'.*__CSR_ASSIGN_BLK__.*[\r\n]', cfg_assign_blk + sts_assign_blk,vcode)
vcode = re.sub(r'.*__CSR_PORT_LIST__.*[\r\n]',rtl_port_list_code,vcode)
vcode = re.sub(r'.*__CSR_PORT_DECLARE__.*[\r\n]',rtl_port_dclr_code,vcode)
for i in range(0,len(reg_loop_patterns)):
    vcode = vcode.replace(reg_loop_patterns[i],rtl_insert_lists[i])

# write to CSR.V
f_csr_v = open(pf_csr_v,"wt")
f_csr_v.write(vcode)

# close all file
f_csr_v.close();

