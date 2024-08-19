/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */


/*
 * Copyright (c) 2024 David Parent
 * SPDX-License-Identifier: Apache-2.0
 * tt_um_davidparent_prbs31
 */
 
`default_nettype none

module tt_um_stochastic_test_CL123abc(
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n    // reset_n - low to reset
);
	reg [30:0] lfsr_1, lfsr_2;
    reg SN_Bit_1, SN_Bit_2, SN_Bit_Out; 
	reg [7:0] clk_counter;
	reg [6:0] prob_counter;
    reg over_flag;
	reg [31:0] average;
    
    always @(posedge clk or posedge rst_n) begin
        if (rst_n) begin
        lfsr_1 <= 31'd1; // Reset 1st counter
	    lfsr_2 <= 31'd2; // Reset 2nd counter to different value
	    SN_Bit_1 <= 1'b0; // Reset SN bits
	    SN_Bit_2 <= 1'b0; 
        SN_Bit_Out <= 1'b0; 
	    clk_counter <= 4'b0000; // Reset clk counter
	    prob_counter <= 3'b000; // Reset output counter
	    over_flag <= 0; // Reset overflag
	average <= 0;
        end else begin
        // Increment counter on each clock cycle
        lfsr_1[0] <= lfsr_1[27] ^ lfsr_1[30] ;
        lfsr_1[30:1] <= lfsr_1[29:0] ;
        
	    lfsr_2[0] <= lfsr_2[27] ^ lfsr_2[30] ; 
        lfsr_2[30:1] <= lfsr_2[29:0] ;
        
	    // Comparator used to generate Bipolar Stochastic Number from 4-bit probability.
	    // Compare RN from LFSR with probability wanted in BN and generate 1 when RN < BN
	    SN_Bit_1 <= (lfsr_1[3:0] < ui_in[3:0]) ;
	    SN_Bit_2 <= (lfsr_2[3:0] < ui_in[7:4]) ;
	    
	    // Stochastic Multiplier for Bipolar SN uses XNOR gate
	    SN_Bit_Out <= !(SN_Bit_1 ^ SN_Bit_2) ;
	    
	    // To convert back to binary probability, use an up-counter, outputting the number of 1s in every 8 bits
	    if (SN_Bit_Out == 1) begin
			if (prob_counter == 7'b1111111) begin
		    over_flag <= 1; // if the number of bits is 8, overflow
		    prob_counter <= 7'b0000000;
	        end
	        else begin
	        prob_counter <= prob_counter + 7'b0000001;
	        end
	    end 
	    
			if (clk_counter == 8'b10000000) begin // output only when clk_counter has counted 8 cycles. Skip every 9th bit to output.
				average <={over_flag,prob_counter, 1'b0} >> 4;
	    over_flag <= 0; //Reset over_flag
	    prob_counter <= 7'b0000000; // Reset prob_counter
	    clk_counter <= 8'b00000000; //Reset clock counter
	    end
	    else begin
	    clk_counter <= clk_counter + 8'b00000001;
	    end
    end
end  
  // All output pins must be assigned. If not used, assign to 0.
	assign uo_out[7:0] = average[7:0];
  assign uio_out = 0;
  assign uio_oe  = 0;
  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in, 1'b0}; 
endmodule

