from docx import Document 
import sys, getopt
import pandas as pd
import re

class xlsx_reader:

    # Parameters
    USED_COLS = ['Type','Field','Bit_Range', 'Reset_Value','Access','Port_Name']

    def __init__(self,input_file,input_sheet) :
        self.xlsx_file  = input_file
        self.xlsx_sheet = input_sheet
        self.wb = pd.read_excel(io=self.xlsx_file,sheet_name=self.xlsx_read,usecols=USED_COLS)
        self.__get_index_of_registers(self)

    def lint_check(self) :
        #TODO: add xlsx_input validation here
        pass

    def get_design_params(self) :
        param_idx  = self.wb[self.wb['Type'].lower() == 'parameter'].index.values
        self.dsgn_name  = self.wb.iloc[param_idx[0]]['Field']
        self.addr_width = self.wb.iloc[param_idx[0]]['Bit_Range']
        self.data_width = self.wb.iloc[param_idx[0]]['Reset_Value']
        self.strb_width = int(data_width/8)

    def get_register_info(self,start_row,end_row) :
        reg_name   = self.wb.iloc[start_row]['Field']
        reg_fields = self.wb.iloc[start_row +1 : end_row] 

        reg_reset_value = 0x0
        reg_bit_width   = 0x0
        reg_field_lst   = list()
        for i in range(0,len(reg_fields)) :
            field_name      = reg_fields.iloc[i]['Field']
            field_bit_range = reg_fields.iloc[i]['Bit_Range']
            field_acc_type  = reg_fields.iloc[i]['Access']
            field_rst_value = reg_fields.iloc[i]['Reset_Value']
            field_port_name = reg_fields.iloc[i]['Port_Name']

            # Extract register fields 
            field_bit_indexs = self.__get_bit_indexs(self,field_bit_range)
            port_bit_indexs  = self.__get_bit_indexs(self,field_port_name)
            reg_field_lst.append({
                 'name'      : field_name
                ,'bit_range' : field_bit_range
                ,'access'    : field_acc_type
                ,'lsb'       : field_bit_indexs['lsb'] 
                ,'msb'       : field_bit_indexs['msb'] 
                ,'port_name' : re.sub(r'\[[\s]*\d+[\s\:]*[\s\d]*\]',"",field_port_name)
                ,'port_lsb'  : port_bit_indexs['lsb']
                ,'port_msb'  : port_bit_indexs['msb']
            })

            # Calculate Reset_Value & Bit_Width
            if(field_name.lower() == 'reserved') :
                pass
            else :
                int_field_rst_value = int(field_rst_value,0)
                field_bit_width = (field_bit_indexs['msb'] - field_bit_indexs['lsb']) + 1
                bit_mask = (2**self.data_width-1) >> (self.data_width - field_bit_width)

                reg_reset_value += (int_field_rst_value & bit_mask) << field_bit_indexs['lsb']
                reg_bit_width += field_bit_width;

        reg_info = {
             'name'        : reg_name
            ,'bit_width'   : reg_bit_width
            ,'reset_value' : reg_reset_value
            ,'fields'      : reg_field_lst
        }
    #---------------------------------------------
    # Private functions
    #---------------------------------------------
    def __get_bit_indexs(self,bit_range) :
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
    print("dsgn_name : " + csr.dsgn_name  + "\n")
    print("addr_width: " + csr.addr_width + "\n")
    print("data_width: " + csr.data_width + "\n")

