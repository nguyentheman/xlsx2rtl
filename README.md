# xlsx2rtl

A python3-based utility script to generate verilog design of Configuration and Status Register (CSR) from an excel input file

## Installation

This script require to install "pandas" and "xlrd" package to execute. They can be installed via "pip"

```
pip install pandas
pip install xlrd
```

## Usage

Using command below to generate the verilog design 

```
xlsx2rtl.py -i <excel input file> -v <templete of verilog CSR code> -o <output directory>
```

## Examples

The example of "excel input file" and "verilog templete files" are availabled on [test](https://github.com/nguyentheman/xlsx2rtl/tree/master/test). User can execute the below command for test.

For generating the RTL code of CSR without "write stroble" feature
``` 
xlsx2rtl.py -i ./test/test.xlsx -v ./test/csr_templete.v -o ./test/
``` 

For generating the RTL code of CSR with "write stroble" feature
```
xlsx2rtl.py -i ./test/test.xlsx -v ./test/csr_wsrtb_templete.v -o ./test/
```

## Userguide

### Create register input file

![Register input file format](https://github.com/nguyentheman/xlsx2rtl/blob/master/docs/register_define.jpg)

### Create CSR templete file

The xlsx2rtl script simply replaces the "code sections" and "variables" in verilog templete file to create the RTL code. Meaning of supported "code sections" and "variables at below:

#### Code sections
| Code section | Meanning |
| ------------- | ------------- |
| \_\_CSR_PORT_LIST\_\_     | list of Configuration and Status ports. It is extracted from the "Port_Name" column in excel file
| \_\_CSR_PORT_DECLARE\_\_  | the definition of configuration and status ports
| \_\_REG_DECLARE_BLK\_\_   | the definition of internal registers. The name of registers is get from "Register_Name" field in excel file
| \_\_REG_ASSIGN_BLK\_\_    | the assigment between Configuration and Status ports with register's fields.
| \_\_LOOP_START\_\_ \<code templete\> \_\_LOOP_END\_\_ | repeat the \<code templete\> for all registers
| \_\_STRB_START\_\_ \<code templete\> \_\_STRB_END\_\_ | insert write strobe following \<code templete\>  

#### Variables

| Variable | Meanning |
| ------------- | ------------- |
| ${\__DATA_WIDTH_VAL\_\_} | bit-width of write data and read data
| ${\__ADDR_WIDTH_VAL\_\_} | bit-width of register's address
| ${\__STRB_WIDTH_VAL\_\_} | bit-width of write_strobe input, this value is calculated from ${__DATA_WIDTH_VAL__} automatically.
| ${\__REG_VAR\_\_} | internal register variable, it is defined at __REG_DECLARE_BLK__ code section
| ${\__REG_ADDR\_\_} | register's address, it is extracted from the "Register Address" field in excel file
| ${\__REG_RANGE\_\_} | bit-part selection of register read/write opreation. This value is calculated by script automatically. 
| ${\__FIELD_NAME\_\_} | the name of register's field
| ${\__STRB_INDEX\_\_} | the write_stroble bit selection

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/nguyentheman/xlsx2rtl/blob/master/LICENSE) file for details

