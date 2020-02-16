//--------------------------------------------------------------------------
//  Project         : CSR templete
//  Module name     : ${__MODULE_NAME__}
//  Author          : ntman
//  Date Created    : 8 Feb 2020
//  Revision History:
//--------------------------------------------------------------------------
`include "${__MODULE_NAME__}.vh"
module ${__MODULE_NAME__} (
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
       ,__CSR_PORT_LIST__
);
    //-------------------------------------------------------------
    //  Parameter
    //-------------------------------------------------------------
    localparam DATA_WIDTH = ${__DATA_WIDTH_VAL__} ;
    localparam ADDR_WIDTH = ${__ADDR_WIDTH_VAL__} ;
    localparam STRB_WIDTH = ${__STRB_WIDTH_VAL__} ;

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
    __CSR_PORT_DECLARE__

    //Internal Registers
    __REG_DECLARE_BLK__

    //-------------------------------------------------------------
    //  Design Architecture
    //-------------------------------------------------------------

    //Register write
    always @(posedge clk, negedge rstn) begin
        if(!rstn) begin
            __LOOP_START__ 
            ${__REG_VAR__} <= ${__REG_RESET_VALUE__};
            __LOOP_END__
        end else begin
            if(cs === 1 && wen === 1) begin
                case(addr[ADDR_WIDTH-1:0]) begin
                    __LOOP_START__
                    ${__REG_ADDR__} : begin
                        __STRB_START__
                        if(strb[${__STRB_INDEX__}]) begin
                            ${__REG_VAR__}[${__REG_RANGE__}] <= wdata[${__REG_RANGE__}]; //${__FIELD_NAME__}
                        end
                        __STRB_END__
                    end
                    __LOOP_END__
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
            __LOOP_START__
            ${__REG_ADDR__} : begin
                rdata_int[${__REG_RANGE__}] = ${__REG_VAR__}[${__REG_RANGE__}]; //${__FIELD_NAME__}
            end
            __LOOP_END__
            default: begin
                rdata_int[DATA_WIDTH-1:0] = {DATA_WIDTH{1'b0}};
            end
        endcase
    end

    //Configuration & Status assign blocks
    assign __CSR_ASSIGN_BLK__
endmodule : ${__MODULE_NAME__}
