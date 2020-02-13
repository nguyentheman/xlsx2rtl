//--------------------------------------------------------------------------
//  Project         : CSR templete
//  Module name     : uart_csr
//  Author          : ntman
//  Date Created    : 8 Feb 2020
//  Revision History:
//--------------------------------------------------------------------------
`include "uart_csr.vh"
module uart_csr (
        clk
       ,rstn
        //memory interface
       ,addr
       ,strb
       ,wdata
       ,rdata
       ,wen
       ,cs
       //Configuration & Status
       ,portA
       ,portC
       ,portB
);
    //-------------------------------------------------------------
    //  Parameter
    //-------------------------------------------------------------
    localparam DATA_WIDTH = 32 ;
    localparam ADDR_WIDTH = 16 ;
    localparam STRB_WIDTH = 4 ;

    //-------------------------------------------------------------
    //  Pins/ports
    //-------------------------------------------------------------

    //Memory Interface
    input                           clk   ;
    input                           rstn  ;
    input   wire [ADDR_WIDTH-1:0]   addr  ;
    input   wire [STRB_WIDTH-1:0]   strb  ;
    input   wire [DATA_WIDTH-1:0]   wdata ;
    output  wire [DATA_WIDTH-1:0]   rdata ;
    input   wire                    wen   ;
    input   wire                    cs    ;

    //Configuration & Status
    output [7:0] portA;
    output [6:0] portC;
    input [7:0] portB;

    //Internal Registers
    reg [10:0] var_reg1;
    reg [11:0] var_reg2;

    //-------------------------------------------------------------
    //  Design Architecture
    //-------------------------------------------------------------

    //Register write
    always @(posedge clk, negedge rstn) begin
        if(!rstn) begin
            var_reg1 <= 11'h603;
            var_reg2 <= 12'h63;
        end else begin
            if(cs === 1 && wen === 1) begin
                case(addr[ADDR_WIDTH-1:0]) begin
                    `ADDR_REG1 : begin
                        if(strb[0]) begin
                            var_reg1[ 3: 0] <= wdata[ 3: 0]; //field1
                        end
                    end
                    `ADDR_REG2 : begin
                        if(strb[0]) begin
                            var_reg2[ 3: 0] <= wdata[ 3: 0]; //field1
                        end
                        if(strb[0]) begin
                            var_reg2[5:7] <= wdata[5:7]; //field3
                        end
                        if(strb[1]) begin
                            var_reg2[11   ] <= wdata[11   ]; //field4
                        end
                    end
                    default: begin
                        
                    end
                endcase
            end
        end
    end
    
    //Register read
    reg [DATA_WIDTH-1:0] rdata_int;
    always @(*) begin
        rdata_in [DATA_WIDTH-1:0] = {DATA_WIDTH{1'b0}};
        case(addr[ADDR_WIDTH-1:0])
            `ADDR_REG1 : begin
                rdata_int[ 3: 0] = var_reg1[ 3: 0]; //field1
                rdata_int[ 8: 4] = var_reg1[ 8: 4]; //field2
                rdata_int[10: 9] = var_reg1[10: 9]; //field3
            end
            `ADDR_REG2 : begin
                rdata_int[ 3: 0] = var_reg2[ 3: 0]; //field1
                rdata_int[ 4   ] = var_reg2[ 4   ]; //field2
                rdata_int[10: 5] = var_reg2[10: 5]; //field3
                rdata_int[11   ] = var_reg2[11   ]; //field4
            end
            default: begin
                rdata_int[DATA_WIDTH-1:0] = {DATA_WIDTH{1'b0}};
            end
        endcase
    end

    //Configuration & Status assign blocks
    assign portA[ 3: 0] = var_reg1[ 3: 0];
    assign portA[ 7: 4] = var_reg2[ 3: 0];
    assign portC[5: 0] = var_reg2[10: 5];
    assign portC[6   ] = var_reg2[11   ];
    assign var_reg1[ 8: 4] = portB[ 4: 0];
    assign var_reg1[10: 9] = portB[ 6: 5];
    assign var_reg2[ 4   ] = portB[7   ];
endmodule : uart_csr
