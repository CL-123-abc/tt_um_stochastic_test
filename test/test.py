# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT
#imnport the coco functionality
#Testing a bipolar SN multiplier with 4-bit inputs (Probability intervals: 1/16) 
#Outputs every 8-bits, averages after n_clock cycles
#
import matplotlib.pyplot as plt

output_interval = 8 #Determines after how many cycles the output updates, doesnt really affect simulation but does in real circuit
input_bitsize = 4 #Determines number of bits in input, probability interval
graph_interval = 1000 #Determines how many clock cycles will pass per marker on plot
prbs_size = 31 #Size of the LFSR
#Seeds of LFSR
LFSR1_seed = [prbs_size-1]
LFSR2_seed = [prbs_size-2]
#Set number of clock cycles to test
n_clock = 100000

#Input Probabilities in integer val
size = 1
in_prob1=[8]
in_prob2=[8]

#Run through the simulation to create idealized LFSR, SN and output values
for w in range(size):
    #Fill lists with 0's
    #LSFR1
    PRBSN1=[0]*prbs_size
    PRBSO1=[0]*prbs_size

    #LFSR2
    PRBSN2=[0]*prbs_size
    PRBSO2=[0]*prbs_size

    #LFSR will not work if all FFs are set to 0

    #Seed for LFSR1
    for seed1_i in range(len(LFSR1_seed)):
        PRBSO1[LFSR1_seed[seed1_i]]=1
    #Seed for LFSR2
    for seed2_i in range(len(LFSR2_seed)):
        PRBSO2[LFSR2_seed[seed2_i]]=1
        
    #Set output lists
    LFSR1=[0]*(n_clock)
    LFSR2=[0]*(n_clock)
    rand1=0
    rand2=0

    #Set SN lists to 0
    SN1=[0]*(n_clock) #Input1
    SN2=[0]*(n_clock) #Input2
    SN3=[0]*(n_clock) #Output
    
    #Output Probability Values
    up_counter_val=0
    out_prob=[0]*n_clock
    ovr_flg=[0]*(n_clock) #Overflow flag
    avg = 0

    for i in range(n_clock):
        #Every 32 SN output bits, output, avg and reset
        if((i% output_interval) == 0):
            out_prob[i]=up_counter_val
            up_counter_val = 0

        ###LFSR CODE###
        #input the feedback for LFSR, taps are at these regs
        PRBSN1[0]=PRBSO1[27]^PRBSO1[30]
        PRBSN2[0]=PRBSO2[27]^PRBSO2[30]
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
        ###LFSR CODE###
        
        #Convert LFSR to random number
        rand1 = 0
        rand2 = 0
        for tt in range(input_bitsize):
            if (LFSR1[(i-tt)%n_clock] == 1):
                rand1 += pow(2,input_bitsize-1-tt)
            if (LFSR2[(i-tt)%n_clock] == 1):
                rand2 += pow(2,input_bitsize-1-tt)
        #Comparator for bipolar SNG of input
        if(in_prob1[w]>rand1):
            SN1[i] = 1
        else:
            SN1[i] = 0
        if(in_prob2[w]>rand2):
            SN2[i] = 1
        else:
            SN2[i] = 0

        #XNOR gate for bipolar SN multiplication
        SN3[i]= not(SN1[i]^SN2[i])
    
        #Convert back to BN prob with Upcounter
        if(SN3[i] == 1):
            if(up_counter_val == (output_interval-1)):
                up_counter_val = 0
                ovr_flg[i] = 1
            else:
                up_counter_val += 1
            
#Start the test
@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    #Start the clock
    cocotb.start_soon(clock.start())
    
    # Run through the reset sequence. Start low, go high, go back to low. The teset begins when the reset goes low.
    dut._log.info("Reset")
    
    #Set inputs for enable, ui_in and uio_in
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    
    #Set reset to 0
    dut.rst_n.value = 0
    
    #wait 5 clock cycle
    await ClockCycles(dut.clk,5)
    
    #Set reset to 1
    dut.rst_n.value = 1
    
    #wait for five clock cycles.
    await ClockCycles(dut.clk, 5)
    
    #Set reset to 0
    dut.rst_n.value = 0
    
    #True test begins here
    dut._log.info("Test project behavior")
    await ClockCycles(dut.clk,10) 
    test_out_prob = 0
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
    for i in range(0,n_clock):
        
        # Wait for 8 clock cycles to see the output values
        await ClockCycles(dut.clk,8)
    
        #The following assertion is just an example of how to check the output values.
    
        # Test (assert) that we are getting the expected output.
        for i in range(1,4):
            if(dut.uo_out[i] == 1):
                test_out_prob = test_out_prob + pow(2,i)
        
        assert test_out_prob == out_prob[i]
        assert dut.uo_out[4].value == ovr_flg[i]
