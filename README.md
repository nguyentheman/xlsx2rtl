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

### Examples

The example of "excel input file" and "verilog templete files" are availabled on [test](https://github.com/nguyentheman/xlsx2rtl/tree/master/test). User can execute the below command for test.

For generating the RTL code of CSR without "write stroble" feature
``` 
xlsx2rtl.py -i ./test/test.xlsx -v ./test/csr_templete.v -o ./test/
``` 

For generating the RTL code of CSR with "write stroble" feature
```
xlsx2rtl.py -i ./test/test.xlsx -v ./test/csr_wsrtb_templete.v -o ./test/
```

### Userguide

#### Create register input file

T.B.D

#### Create CSR templete file

T.B.D


## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/nguyentheman/xlsx2rtl/blob/master/LICENSE) file for details

