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
    input  wire       rst_n     // reset_n - low to reset
);
	reg [30:0] lfsr_1, lfsr_2;
    reg SN_Bit_1, SN_Bit_2, SN_Bit_Out;
    reg [3:0] clk_counter;
    reg [2:0] prob_counter;
    reg [2:0] output_prob;
    reg overflow;
     
    always @(posedge clk or posedge rst_n) begin
        if (rst_n) begin
        lfsr_1 <= 31'd1; // Reset 1st counter
	    lfsr_2 <= 31'd2; // Reset 2nd counter to different value
	    SN_Bit_1 <= 1'b0; // Reset SN bits
	    SN_Bit_2 <= 1'b0; 
	    SN_Bit_Out <= 1'b0; 
	    clk_counter <= 4'b0000; // Reset clk counter
	    output_prob <= 3'b000; // Reset output
	    overflow <= 0; // Reset overflow
    end else begin
        // Increment counter on each clock cycle
        lfsr_1[0] <= lfsr_1[27] ^ lfsr_1[30] ;
        lfsr_1[30:1] <=lfsr_1[29:0] ;

	    lfsr_2[0] <= lfsr_2[12] ^ lfsr_2[16] ; //using different gates to get different pattern
        lfsr_2[30:1] <=lfsr_2[29:0] ;

	    // Comparator used to generate Bipolar Stochastic Number from 4-bit probability.
	    // Compare RN from LFSR with probability wanted in BN and generate 1 when RN < BN
	    SN_Bit_1 <= (lfsr_1[30:27] < ui_in[3:0]) ;
	    SN_Bit_2 <= (lfsr_2[30:27] < ui_in[7:4]) ;

	    // Stochastic Multiplier for Bipolar SN uses XNOR gate
	    SN_Bit_Out <= !(SN_Bit_1 ^ SN_Bit_2) ;
	
	    // To convert back to binary probability, use an up-counter, outputting the number of 1s in every 8 bits
	    if (SN_Bit_Out == 1) begin
	        if (prob_counter == 3'b111) begin
		    overflow <= 1; // if the number of bits is 8, overflow
	        end
	    prob_counter <= prob_counter + 3'b001;
	    end 
        
	    if (clk_counter == 4'b1000) begin // output only when clk_counter has counted 8 cycles.
	    output_prob <= prob_counter;
	    overflow <= 0;
	    end
	    clk_counter <= clk_counter + 4'b0001;
    end
end  
  // All output pins must be assigned. If not used, assign to 0.
  assign uo_out[0] = 0;
  assign uo_out[3:1] = clk? output_prob : 3'b000;
  assign uo_out[4] = clk? overflow:1'b0;
  assign uio_out = 0;
  assign uio_oe  = 0;
  assign uo_out[7:5] = 3'b000;
  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in, 1'b0}; 
endmodule
