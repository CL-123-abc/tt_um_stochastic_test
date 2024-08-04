# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT

#import the coco functionality
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

prbs_size=31 #Size of the LSFR

#Fill lists with 0's
#LFSR1
PRBSN1=[0]*prbs_size
PRBSO1=[0]*prbs_size

#LFSR2
PRBSN2=[0]*prbs_size 
PRBSO2=[0]*prbs_size

#It will not work if all the FFs are set to zero.  

#Set the highest register to 1 for LFSR1
PRBSO1[prbs_size-1]=1

#Set the 2nd highest register to 1 for LFSR2
PRBSO2[prbs_size-2]=1

# Set number of clock cycles to test.
n_clock=10000

#set output lists to 1
LFSR1=[1]*(n_clock) #LFSR1
LFSR2=[1]*(n_clock) #LFSR2
out=[1]*(n_clock)

#SN1 Input 1
SN1=[1]*(n_clock)
#SN2 Input 2
SN2=[1]*(n_clock)
#SN3 Output
SN3=[1]*(n_clock)

#Input Probabilities
in_prob1=8 #[1000]
in_prob2=8 #[1000]
#Output Probability
up_counter_val = 0
out_prob=0
#Overflow Flag 
ovr_flg=0

# Run though the simulation to create the idealized LFSR values.
for i in range(n_clock):
	#every 8 bits output and reset counters
	if(n_clock%8 == 0):
		out_prob = up_counter_val
		up_counter_val = 0
		ovr_flg = 0
  #input the feedback
  	PRBSN1[0]=PRBSO1[27]^PRBSO1[30]
  	PRBSN2[0]=PRBSO2[12]^PRBSO2[16]
  #shift the values
  	for j in range(prbs_size-1):
    	count=prbs_size-j-1
    	PRBSN1[count]=PRBSO1[count-1]
    	PRBSN2[count]=PRBSO2[count-1]
  #update the array
  	for j in range(len(PRBSN1)):
    	PRBSO1[j]=PRBSN1[j]    
  	for j in range(len(PRBSN2)):
    	PRBSO2[j]=PRBSN2[j]
  #take the output from the rightmost FF.
  	LFSR1[i]=PRBSN1[prbs_size-1]
  	LFSR2[i]=PRBSN2[prbs_size-1]

#Comparator to generate bipolar SN 
  	if(in_prob1 > int(LFSR1[0:3],2)):
	  	SN1 = 1
	else:
	  	SN1 = 0
  	if(in_prob2 > int(LFSR2[0:3],2)):
	  	SN2 = 1
	else:
		SN2 = 0
#XNOR gate for multiplication of bipolar SN
  	SN3 = !(SN1 ^ SN2)
#Convert back to binary prob with an upcounter that outputs every 8 SN bits
	if(SN3 == 1):
		if (up_counter_val == 7):
			up_counter_val = 0
			ovr_flg = 1
		up_counter_val += 1
	
#Start the test  
@cocotb.test() 
async def test_project(dut):
    dut._log.info("Start")
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    #Start the clock
    cocotb.start_soon(clock.start())

    # Run through reset sequence.  Start low, go high, go back to low. The test begins when the reset goes low.
    dut._log.info("Reset")

    #Set inputs for enable, ui_in and uio_in
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    #Set reset to 0
    dut.rst_n.value = 0

    #wait 5 clock cycle
    await ClockCycles(dut.clk, 5)

    #Set reset to 1
    dut.rst_n.value = 1

    # wait for five clock cycles.
    await ClockCycles(dut.clk, 5)

    #Set reset to 0
    dut.rst_n.value = 0

    #True test begins here.
    dut._log.info("Test project behavior")

    #Set input sample
    #BN Prob 1
    dut.ui_in[0].value = 0
    dut.ui_in[1].value = 0
    dut.ui_in[2].value = 0
    dut.ui_in[3].value = 1
    #BN Prob 2
    dut.ui_in[4].value = 0
    dut.ui_in[5].value = 0
    dut.ui_in[6].value = 0
    dut.ui_in[7].value = 1

    #Compare output to theory for each clock cycle
    ##for i in range(0,n_clock):

    # Wait for one clock cycle to see the output values
    await ClockCycles(dut.clk, 1)

    # The following assertion is just an example of how to check the output values.

    # Test (assert) that we are getting the expected output. 
    assert int(dut.uo_out[2:0].value,2) == out_prob
    assert dut.uo_out[4].value == ovr_flg
      
