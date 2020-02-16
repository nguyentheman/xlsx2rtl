from docx import Document 
import sys, getopt
import pandas as pd
import re

class xlsx_reader:

    # Parameters
    USED_COLS = ['Type','Field','Bit_Range', 'Reset_Value','Access','Port_Name']

    def __init__(self,xlsx_file,xlsx_sheet) :
        self.wb = pd.read_excel(io=xlsx_file,sheet_name=xlsx_sheet,usecols=self.USED_COLS)
        self.__get_index_of_registers()

    def lint_check(self) :
        #TODO: add xlsx_input validation here
        pass

    def get_design_params(self) :
        param_idx  = self.wb[self.wb['Type'] == 'parameter'].index.values
        self.dsgn_name  = self.wb.iloc[param_idx[0]]['Field']
        self.addr_width = self.wb.iloc[param_idx[0]]['Bit_Range']
        self.data_width = self.wb.iloc[param_idx[0]]['Reset_Value']
        self.strb_width = int(self.data_width/8)

    def get_register_short_info(self,start_row,end_row) :
        reg_name    = self.wb.iloc[start_row]['Field']
        reg_address = self.wb.iloc[start_row]['Bit_Range']
        reg_info = {
             'name'        : reg_name
            ,'address'     : reg_address
        }
        return reg_info

    def get_register_info(self,start_row,end_row) :
        reg_name    = self.wb.iloc[start_row]['Field']
        reg_fields  = self.wb.iloc[start_row +1 : end_row] 
        reg_address = self.wb.iloc[start_row]['Bit_Range']

        reg_reset_value = 0x0
        reg_bit_width   = 0x0
        reg_field_lst   = list()
        pre_reg_msb = 0x0
        for i in range(0,len(reg_fields)) :
            field_name      = reg_fields.iloc[i]['Field']         
            field_bit_range = reg_fields.iloc[i]['Bit_Range']         
            field_acc_type  = reg_fields.iloc[i]['Access']        
            field_rst_value = reg_fields.iloc[i]['Reset_Value']       
            field_port_name = reg_fields.iloc[i]['Port_Name']         

            # Extract register fields 
            field_bit_indexs = self.__get_bit_indexs(field_bit_range)
            port_bit_indexs  = self.__get_bit_indexs(field_port_name)
            field_bit_width  = (field_bit_indexs['msb'] - field_bit_indexs['lsb']) + 1
            if(re.match(r'reserved',field_name.lower())):
                reg_lsb = 'inf'
                reg_msb = 'inf' 
            else :
                reg_lsb = pre_reg_msb
                reg_msb = reg_lsb + field_bit_width -1 
                pre_reg_msb = reg_msb + 1 

                # Calculate Reset_Value & Bit_Width
                int_field_rst_value = int(field_rst_value,0)
                bit_mask = (2**self.data_width-1) >> (self.data_width - field_bit_width)
                reg_reset_value += (int_field_rst_value & bit_mask) << reg_lsb
                reg_bit_width += field_bit_width

            reg_field_lst.append({
                 'name'      : field_name
                ,'bit_range' : field_bit_range
                ,'access'    : field_acc_type
                ,'wdat_lsb'  : field_bit_indexs['lsb'] 
                ,'wdat_msb'  : field_bit_indexs['msb']
                ,'reg_lsb'   : reg_lsb
                ,'reg_msb'   : reg_msb 
                ,'port_name' : re.sub(r'\[[\s]*\d+[\s\:]*[\s\d]*\]',"",str(field_port_name))
                ,'port_lsb'  : port_bit_indexs['lsb']
                ,'port_msb'  : port_bit_indexs['msb']
            })


        reg_info = {
             'name'        : reg_name
            ,'address'     : reg_address
            ,'bit_width'   : reg_bit_width
            ,'reset_value' : reg_reset_value
            ,'fields'      : reg_field_lst
        }

        return reg_info
    #---------------------------------------------
    # Private functions
    #---------------------------------------------
    def __get_bit_indexs(self,bit_range) :
        if(pd.isna(bit_range) == True) :
            lsb = 'inf'
            msb = 'inf'
        else :
            bit_indexs = list(map(int,re.findall(r'\d+',bit_range)))
            num_indexs = len(bit_indexs)
            if(num_indexs == 1): 
                bit_indexs.append(bit_indexs[0]) # append dummy value to avoid syntax error
            lsb = min(bit_indexs)
            msb = max(bit_indexs)
        index_out = {'lsb' : lsb, 'msb': msb}
        return index_out

    def __get_index_of_registers(self) :
        self.reg_start_rows = self.wb[self.wb['Type'] == 'register'].index.values
        self.reg_end_rows   = self.wb[self.wb['Type'] == 'comment'].index.values
        assert(len(self.reg_start_rows) == len(self.reg_end_rows)) , "Missing 'register' or 'comment' field !!!!"

#----------------------------------------
# Main Scripts
#----------------------------------------
def print_help() :
    print ("xlsx2rtl.py -i <excel-based register input file -v <verilog templete file> -o <output dir>")

def generate_csr_vh(csr,filename):
    f_csr_vh = open(filename,"w")
    csr_vh_str = "`ifndef " + "__" + csr.dsgn_name.upper() + "_CSR_" + "VH__\n"
    csr_vh_str += "`define " + "__" + csr.dsgn_name.upper() + "_CSR_" + "VH__\n\n\n"
    for i in range(0,len(csr.reg_start_rows)) :
        reg   = csr.get_register_short_info(csr.reg_start_rows[i],csr.reg_end_rows[i])
        csr_vh_str += "`define ADDR_" + reg['name'].upper() + " "
        csr_vh_str += reg['address'].replace('0x',str(csr.addr_width)+'\'h') + ";\n"
    csr_vh_str += "\n\n`endif\n"
    f_csr_vh.write(csr_vh_str)
    f_csr_vh.close()

def get_bit_select_str(msb,lsb) :
    if(msb != lsb) :
        tmp_str = "[" + str(msb) + ":" + str(lsb) + "]"
    else :
        tmp_str = "[" + str(msb) + "]"
    return tmp_str

def main(argv) :

    # Terminal Arguments
    XLSX_IN   = ""
    CSR_TEMP  = ""
    OUT_DIR   = "./"
    try :
        opts,args = getopt.getopt(argv,"hi:v:o:",["ifile=","vfile=","odir="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if(opt == '-h') :
            print_help()
            sys.exit()
        elif opt in ("-i","--ifile"):
            XLSX_IN = arg
        elif opt in ("-v","--vfile"):
            CSR_TEMP = arg
        elif opt in ("-o","--odir"):
            OUT_DIR = arg

    csr = xlsx_reader(XLSX_IN,"register_set")

    # perform lint check for excel file
    csr.lint_check()

    # get design paramter
    csr.get_design_params()
    print("Generating CSR-RTL code for:")
    print("+ dsgn_name : " + csr.dsgn_name)
    print("+ addr_width: " + str(csr.addr_width))
    print("+ data_width: " + str(csr.data_width))
    print("+ total registers : " + str(len(csr.reg_start_rows)))

    pf_csr_vh   = OUT_DIR + csr.dsgn_name.lower() + "_csr.vh"
    pf_csr_v    = OUT_DIR + csr.dsgn_name.lower() + "_csr.v"

    # Create csr.vh
    print("Generating " + pf_csr_vh + " ...")
    generate_csr_vh(csr,pf_csr_vh)

    # Create csr.v
    print("Generating " + pf_csr_v + " ...")
    f = open(CSR_TEMP,"rt")
    vcode = f.read()
    f.close()

    regex_loops = r'^[\s]*__LOOP_START__[\s\r\n]*[\s\S]*?__LOOP_END__.*[\r\n]'
    regex_wstrb = r'^[\s]*__STRB_START__[\s\r\n]*[\s\S]*?__STRB_END__.*[\r\n]'
    regex_reset = r'.*\${__REG_VAR__}.*<=.*\${__REG_RESET_VALUE__}.*[\r\n]'
    regex_write = r'.*\${__REG_VAR__}.*<=.*[\r\n]'
    regex_read  = r'.*=.*\${__REG_VAR__}.*[\r\n]'


    reg_declare_blk = ""
    cfg_assign_blk  = ""
    sts_assign_blk  = ""
    port_list_blk   = ""
    port_dclr_blk   = ""

    rtl_loops_pat = re.findall(regex_loops,vcode,re.MULTILINE)
    rtl_insert_lists = [""]*len(rtl_loops_pat)

    rtl_port_list_pat = re.findall(r'.*__CSR_PORT_LIST__.*[\r\n]',vcode)
    rtl_port_dclr_pat = re.findall(r'.*__CSR_PORT_DECLARE__.*[\r\n]',vcode)
    rtl_asgn_pat      = re.findall(r'.*__CSR_ASSIGN_BLK__.*[\r\n]',vcode)

    rtl_port_info = list()
    for reg_no in range(0,len(csr.reg_start_rows)) :
        reg = csr.get_register_info(csr.reg_start_rows[reg_no],csr.reg_end_rows[reg_no])
        reg_name = reg['name']
        reg_bw   = reg['bit_width']
        reg_rst  = reg['reset_value']
        lst_reg_fields = reg['fields']
        print("Generating " + reg_name + " ...")

        for i in range(0,len(rtl_loops_pat)) :
            rtl_pat = rtl_loops_pat[i] #get pattern of the RTL code
            rtl_code = re.sub(r'.*__LOOP_START__.*[\r\n]|.*__LOOP_END__.*[\r\n]',"",rtl_pat) #remove __LOOP_START__ and __LOOP_END__

            # generate reg's reset
            rtl_pat = re.findall(regex_reset,rtl_code)
            if(len(rtl_pat) > 0) :
                code_tmp = rtl_pat[0]
                code_tmp = code_tmp.replace("${__REG_RESET_VALUE__}",hex(reg_rst).replace("0x",str(reg_bw)+"'h"))
                code_tmp = code_tmp.replace("${__REG_VAR__}"      ,"var_" + reg_name.lower())
                code_tmp = code_tmp.replace("${__REG_RANGE__}"    , "[" + str(reg_bw-1) + ":0]" )
                rtl_code = rtl_code.replace(rtl_pat[0],code_tmp)

            # generate reg's read/write
            rtl_rd_pat = re.findall(regex_read,rtl_code)
            rtl_wstrb_pat = re.findall(regex_wstrb,rtl_code,re.MULTILINE)
            if(len(rtl_wstrb_pat) > 0) :
                rtl_wr_pat = rtl_wstrb_pat
            else :
                rtl_wr_pat = re.findall(regex_write,rtl_code)

            rtl_rd_code = ""
            rtl_wr_code = ""
            for field_no in range(0,len(lst_reg_fields)) :
                field = lst_reg_fields[field_no]
                field_name      = field['name']
                field_bit_range = re.sub(r'\[|\]',"",field['bit_range'])
                field_access    = field['access']
                field_port_name = field['port_name']
                field_port_lsb  = field['port_lsb']
                field_port_msb  = field['port_msb']

                # generate CSR port list
                if(not re.match(r'reserved',field_name.lower())) : 
                    if(field_port_name not in port_list_blk ) :
                        rtl_port_list_code = rtl_port_list_pat[0].replace("__CSR_PORT_LIST__",field_port_name)
                        port_list_blk += rtl_port_list_code
                        if(re.match(r'RO',field_access)) : 
                            rtl_port_type = "input"
                        else :
                            rtl_port_type = "output"

                        rtl_port_info.append({
                             'port_name': field_port_name
                            ,'port_type': rtl_port_type
                            ,'port_lsb' : field_port_lsb
                            ,'port_msb' : field_port_msb
                        })
                    else:
                        for port_id in range(0,len(rtl_port_info)):
                            if(rtl_port_info[port_id]['port_name'] == field_port_name) :
                                rtl_port_info[port_id]['port_lsb'] = min(rtl_port_info[port_id]['port_lsb'],field_port_lsb)
                                rtl_port_info[port_id]['port_msb'] = max(rtl_port_info[port_id]['port_msb'],field_port_msb)

                #Register read
                if(len(rtl_rd_pat) > 0 and re.match(r'RO|RW',field_access) and not re.match(r'reserved',field_name.lower())) : 
                    code_tmp = rtl_rd_pat[0]
                    rhs_str = "var_" + reg_name.lower() + get_bit_select_str(field['reg_msb'],field['reg_lsb'])
                    code_tmp = code_tmp.replace("${__REG_VAR__}[${__REG_RANGE__}]",rhs_str)
                    code_tmp = code_tmp.replace("${__REG_RANGE__}", field_bit_range)
                    code_tmp = code_tmp.replace("${__FIELD_NAME__}", field_name)
                    rtl_rd_code += code_tmp

                    # generate CSR assign blocks
                    if(re.match(r'RO',field_access)):
                        port_str    = field_port_name + get_bit_select_str(field_port_msb,field_port_lsb)
                        rtl_asgn_str = rhs_str + " = " + port_str + ";" 
                        rtl_asgn_code = rtl_asgn_pat[0].replace("__CSR_ASSIGN_BLK__",rtl_asgn_str)
                        sts_assign_blk += rtl_asgn_code
                
                #Register write
                if(len(rtl_wr_pat) > 0 and re.match(r'WO|RW',field_access) and not re.match(r'reserved',field_name.lower())) : 
                    code_tmp = rtl_wr_pat[0]
                    if(len(rtl_wstrb_pat) > 0) : 
                        code_tmp = re.sub(r'.*__STRB_START__.*[\r\n]|.*__STRB_END__.*[\r\n]',"",code_tmp)
                        field_msb = field['wdat_msb']
                        field_lsb = field['wdat_lsb']
                        field_msb_strb = int(field_msb/8)
                        field_lsb_strb = int(field_lsb/8)
                        if(field_lsb_strb != field_msb_strb) :
                            wstr_code_tmp = ""
                            lsb_diff = field['wdat_lsb'] - field['reg_lsb']
                            msb_diff = field['wdat_msb'] - field['reg_msb']
                            for strb_index in range(field_lsb_strb,field_msb_strb+1):
                                wstr_code_tmp += code_tmp;
                                wdat_lsb = max(strb_index*8,field_lsb)
                                wdat_msb = min((strb_index+1)*8-1,field_msb)
                                wstr_code_tmp = wstr_code_tmp.replace("${__STRB_INDEX__}",str(strb_index))
                                lhs_str = "var_" + reg_name.lower() + get_bit_select_str(wdat_msb-msb_diff,wdat_lsb-lsb_diff)
                                wstr_code_tmp = wstr_code_tmp.replace("${__REG_VAR__}[${__REG_RANGE__}]"  ,lhs_str)
                                wstr_code_tmp = wstr_code_tmp.replace("${__REG_RANGE__}", str(wdat_msb)+":"+str(wdat_lsb))
                            code_tmp = wstr_code_tmp
                        else:
                            code_tmp = code_tmp.replace("${__STRB_INDEX__}",str(field_msb_strb))
                    lhs_str = "var_" + reg_name.lower() + get_bit_select_str(field['reg_msb'],field['reg_lsb'])
                    code_tmp = code_tmp.replace("${__REG_VAR__}[${__REG_RANGE__}]",lhs_str)
                    code_tmp = code_tmp.replace("${__REG_RANGE__}", field_bit_range)
                    code_tmp = code_tmp.replace("${__FIELD_NAME__}", field_name)
                    rtl_wr_code += code_tmp

                    # generate CSR assign blocks
                    port_str    = field_port_name + get_bit_select_str(field_port_msb,field_port_lsb)
                    rtl_asgn_str = port_str + " = " + lhs_str + ";"
                    rtl_asgn_code = rtl_asgn_pat[0].replace("__CSR_ASSIGN_BLK__",rtl_asgn_str)
                    cfg_assign_blk += rtl_asgn_code

            if(len(rtl_rd_pat) > 0 ) :
                rtl_code = rtl_code.replace(rtl_rd_pat[0],rtl_rd_code)
            if(len(rtl_wr_pat) > 0 ) :
                rtl_code = rtl_code.replace(rtl_wr_pat[0],rtl_wr_code)
            rtl_code = rtl_code.replace("${__REG_ADDR__}","`ADDR_"+reg_name.upper())
            rtl_insert_lists[i] += rtl_code;

        # generate register defines
        rtl_dclr_pat = re.findall(r'.*__REG_DECLARE_BLK__.*[\r\n]',vcode)
        rtl_dclr_str  = "reg [" + str(reg_bw-1) + ":0] " + "var_" + reg_name.lower() + ";"
        rtl_dclr_code = rtl_dclr_pat[0].replace("__REG_DECLARE_BLK__",rtl_dclr_str)
        reg_declare_blk += rtl_dclr_code

    # edit templete file
    vcode = vcode.replace("${__MODULE_NAME__}"     ,csr.dsgn_name.lower() + "_csr")
    vcode = vcode.replace("${__DATA_WIDTH_VAL__}"  ,str(csr.data_width),1)
    vcode = vcode.replace("${__ADDR_WIDTH_VAL__}"  ,str(csr.addr_width),1)
    vcode = vcode.replace("${__STRB_WIDTH_VAL__}"  ,str(csr.strb_width),1)
    vcode = re.sub(r'.*__REG_DECLARE_BLK__.*[\r\n]',reg_declare_blk,vcode)
    vcode = re.sub(r'.*__CSR_ASSIGN_BLK__.*[\r\n]', cfg_assign_blk + sts_assign_blk,vcode)
    vcode = re.sub(r'.*__CSR_PORT_LIST__.*[\r\n]',port_list_blk,vcode)

    for i in range(0,len(rtl_port_info)):
        port_type = rtl_port_info[i]['port_type']
        port_name = rtl_port_info[i]['port_name']
        port_bw   = "[" + str(rtl_port_info[i]['port_msb']) + ":" + str(rtl_port_info[i]['port_lsb']) + "]" 
        dclr_str  = port_type + " " + port_bw + " " + port_name  + ";"
        dclr_code = rtl_port_dclr_pat[0].replace("__CSR_PORT_DECLARE__",dclr_str)
        port_dclr_blk += dclr_code
    vcode = re.sub(r'.*__CSR_PORT_DECLARE__.*[\r\n]',port_dclr_blk ,vcode)
    for i in range(0,len(rtl_loops_pat)):
        vcode = vcode.replace(rtl_loops_pat[i],rtl_insert_lists[i])
    # write to CSR.V
    f = open(pf_csr_v,"wt")
    f.write(vcode)
    f.close();

if __name__ == "__main__" :
    main(sys.argv[1:])