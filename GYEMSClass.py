#***************************************************************
#
# A python class to control GYEMS RMD-L series servo motor 
# by Rasheed Kittinanthapanya
# a simple RS485 communication between GYEMS servo and Jetson Nano
#
#***************************************************************

import serial
import time
import serial.rs485
import sys

class GYEMS:

	def __init__(self):

		self.ver = sys.version_info[0]

		# Using serial.rs485 library
		self.ser = serial.rs485.RS485("/dev/ttyUSB0", baudrate=115200)		# baudrate must be same as in "RMD-L config V1.1" software
		self.ser.rs485_mode = serial.rs485.RS485Settings(rts_level_for_tx=True, rts_level_for_rx=False, loopback=False, delay_before_tx=None, delay_before_rx=None)

		self.Header = 0x3E

		# Initial value for estimating speed
		self.t1 = 0.0
		self.theta1 = 0.0
		self.MAXDPS = 10000.0
		self.LastDPS = 0.0


	def map(self, val, in_min, in_max, out_min, out_max):

		return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

	def SplitTo4Byte(self,Int):
		# equivalent to Int32toByteData of arduino lib
		StoreByte = [None]*4

		StoreByte[0] = (Int & 0xFF000000) >> 24             #High byte, most right of HEX
		StoreByte[1] = (Int & 0x00FF0000) >> 16
		StoreByte[2] = (Int & 0x0000FF00) >> 8
		StoreByte[3] = (Int & 0x000000FF)					#Low byte, most left of HEX

		return StoreByte

	def SplitTo8Byte(self,Int):
		# equivalent to Int64toByteData of arduino lib
		StoreByte = [None]*8

		StoreByte[0] = (Int & 0xFF00000000000000) >> 56       #High byte, most right of HEX
		StoreByte[1] = (Int & 0x00FF000000000000) >> 48
		StoreByte[2] = (Int & 0x0000FF0000000000) >> 40
		StoreByte[3] = (Int & 0x000000FF00000000) >> 32    
		StoreByte[4] = (Int & 0x00000000FF000000) >> 24    
		StoreByte[5] = (Int & 0x0000000000FF0000) >> 16
		StoreByte[6] = (Int & 0x000000000000FF00) >> 8
		StoreByte[7] = (Int & 0x00000000000000FF)             #Low byte, most left of HEX

		return StoreByte

	def Combine2Byte(self, loByte,hiByte):

		return (loByte & 0xFF) | ( (hiByte & 0xFF) << 8)

	def WriteData(self,CommandString):

		# Set an RTS line to transmit data
		rts_level_for_tx = True
		rts_level_for_rx = False
		self.ser.write(CommandString) # write a string byte out to USB port
		self.ser.flush()				 # wait until finish writing
		# Set an RTS line to receive data
		rts_level_for_tx = False
		rts_level_for_rx = True

		readEncoder = [None]*8
		readEncoder = self.ser.read(8)

	def GetCurrentDeg(self,ID):

		# Constant value
		EncoderCom = 0x90
		EncoderComDataLength = 0x00
		_ID = ID
		FrameCheckSum = self.Header + EncoderCom + EncoderComDataLength + _ID

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			EncoderComString = str(bytearray([chr(self.Header),chr(EncoderCom),chr(_ID),chr(EncoderComDataLength),chr(FrameCheckSum)]))
		else:
			EncoderComString = bytearray([self.Header,EncoderCom,_ID,EncoderComDataLength,FrameCheckSum])

		# Write data out to usb port
		#self.WriteData(EncoderComString)
		rts_level_for_tx = True
		rts_level_for_rx = False
		self.ser.write(EncoderComString) # write a string byte out to USB port
		self.ser.flush()				 # wait until finish writing
		# Set an RTS line to receive data
		rts_level_for_tx = False
		rts_level_for_rx = True

		# Read a reply from servo
		readEncoder = [None]*8
		readEncoder = self.ser.read(8)

		# Combine byte data 5 and 6 into a single word (16bit encoder data)
		if self.ver == 2:
			RawAngle = self.Combine2Byte(ord(readEncoder[5]),ord(readEncoder[6]))
		else:
			RawAngle = self.Combine2Byte(readEncoder[5],readEncoder[6])
		# map 16 bit data to degree value
		Degree = self.map(RawAngle,0,16383,0.0,360.0); 

		return Degree

	def EstimateDPS(self,ID):

		# get instantenuous angle and time
		theta2 = self.GetCurrentDeg(ID)
		t2 = time.time()

		# find the different of time and angle
		period = t2 - self.t1
		deltaPos = (theta2 - self.theta1)
		# speed from differentiate of angle and time
		CurrentDPS = deltaPos/period

		# try to eliminate a spike due to differentiate
		if abs(CurrentDPS) > self.MAXDPS:
			CurrentDPS = self.LastDPS

		# Update previou value to new value
		self.t1 = t2
		self.theta1 = theta2
		self.LastDPS = CurrentDPS

		return CurrentDPS

	def GetAverageSpeed(self,ID):

		# a sample is total number for doing average
		sampler = 100
		# doing an average
		for i in range(0,sampler):
			Speed = self.EstimateDPS(ID)

			if i == 0:
				AccumSpeed = Speed
			else:
				AccumSpeed = AccumSpeed + Speed

			#time.sleep(0.001)

		aveDPS = AccumSpeed/sampler


		return aveDPS

	def MotorOff(self,ID):

		# Constant value
		OffCom = 0x80
		OffComDataLength = 0x00
		_ID = ID
		DataCheckByte = self.Header + OffCom + _ID + OffComDataLength

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			OffComString = str(bytearray([chr(self.Header),chr(OffCom),chr(_ID),chr(OffComDataLength),chr(DataCheckByte)]))
		else:
			OffComString = bytearray([self.Header,OffCom,_ID,OffComDataLength,DataCheckByte])

		# Write data out to usb port
		self.WriteData(OffComString)

	def MotorStop(self,ID):

		# Constant value
		StopCom = 0x81
		StopComDataLength = 0x00
		_ID = ID
		DataCheckByte = self.Header + StopCom + _ID + StopComDataLength

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			StopComString = str(bytearray([chr(self.Header),chr(StopCom),chr(_ID),chr(StopComDataLength),chr(DataCheckByte)]))
		else:
			StopComString = bytearray([self.Header,StopCom,_ID,StopComDataLength,DataCheckByte])

		# Write data out to usb port
		self.WriteData(StopComString)

	def MotorRun(self,ID):

		# Constant value
		RunCom = 0x88
		RunComDataLength = 0x00
		_ID = ID
		DataCheckByte = self.Header + RunCom + _ID + RunComDataLength

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			RunComString = str(bytearray([chr(self.Header),chr(RunCom),chr(_ID),chr(RunComDataLength),chr(DataCheckByte)]))
		else:
			RunComString = bytearray([self.Header,RunCom,_ID,RunComDataLength,DataCheckByte])

		# Write data out to usb port
		self.WriteData(RunComString)


	def SpeedControl(self,ID,DPS):

		# Constant value
		SpeedLSB = int(DPS*100.0)
		SpeedCom = 0xA2			# Convert hex to ascii
		SpeedComDataLength = 0x04
		_ID = ID
		FrameCheckSum = self.Header + SpeedCom + SpeedComDataLength + _ID

		SpeedByte = self.SplitTo4Byte(SpeedLSB)
		DataCheckByte = SpeedByte[3] + SpeedByte[2] + SpeedByte[1] + SpeedByte[0]
		DataCheckByte = DataCheckByte & 0x00FF   # eliminate the second byte, only need 1 byte 

		# For python2, str(bytearray([chr(data2),chr(data2),...]))
		# For python3, bytearray([data1,data2,data3,...])

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			SpeedComString = str(bytearray([chr(self.Header),chr(SpeedCom),chr(_ID),chr(SpeedComDataLength),chr(FrameCheckSum),
							chr(SpeedByte[3]),chr(SpeedByte[2]),chr(SpeedByte[1]),chr(SpeedByte[0]),chr(DataCheckByte)]))
		else:
			SpeedComString = bytearray([self.Header,SpeedCom,_ID,SpeedComDataLength,FrameCheckSum,
							SpeedByte[3],SpeedByte[2],SpeedByte[1],SpeedByte[0],DataCheckByte])
		

		# Write data out to usb port
		self.WriteData(SpeedComString)
		
	def PositionControlMode1(self,ID,Deg):

		# Constant value
		DegLSB = int(Deg*100.0)
		Position1Com = 0xA3
		Position1DataLength = 0x08
		_ID = ID
		FrameCheckSum = self.Header + Position1Com + Position1DataLength + _ID

		Position1Byte = self.SplitTo8Byte(DegLSB)
		DataCheckByte = Position1Byte[7] + Position1Byte[6] + Position1Byte[5] + Position1Byte[4] + Position1Byte[3] + Position1Byte[2] + Position1Byte[1] + Position1Byte[0]

		DataCheckByte = DataCheckByte & 0x00FF   # eliminate the second byte, only need 1 byte 

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			PosCom1String = str(bytearray([chr(self.Header),chr(Position1Com),chr(_ID),chr(Position1DataLength),chr(FrameCheckSum),
						chr(Position1Byte[7]),chr(Position1Byte[6]),chr(Position1Byte[5]),chr(Position1Byte[4]),
						chr(Position1Byte[3]),chr(Position1Byte[2]),chr(Position1Byte[1]),chr(Position1Byte[0]),chr(DataCheckByte)]))
		else:
			PosCom1String = bytearray([self.Header,Position1Com,_ID,Position1DataLength,FrameCheckSum,Position1Byte[7],Position1Byte[6],
				Position1Byte[5],Position1Byte[4],Position1Byte[3],Position1Byte[2],Position1Byte[1],Position1Byte[0],DataCheckByte])

		# Write data out to usb port
		self.WriteData(PosCom1String)

	def PositionControlMode2(self,ID,Deg,DPS):

		# Constant value
		DegLSB = int(Deg*100.0)
		SpeedLSB = int(DPS*100.0)

		Position2Com = 0xA4
		Position2DataLength = 0x0C
		_ID = ID
		FrameCheckSum = self.Header + Position2Com + Position2DataLength + _ID

		Position2Byte = self.SplitTo8Byte(DegLSB)
		Speed2Byte = self.SplitTo4Byte(SpeedLSB)
		DataCheckByte = Position2Byte[7] + Position2Byte[6] + Position2Byte[5] + Position2Byte[4] + Position2Byte[3] + Position2Byte[2] + Position2Byte[1] + Position2Byte[0] + Speed2Byte[3] + Speed2Byte[2] + Speed2Byte[1] + Speed2Byte[0]

		DataCheckByte = DataCheckByte & 0x000000FF   # eliminate the second byte, only need 1 byte 

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			PosCom2String = str(bytearray([chr(self.Header),chr(Position2Com),chr(_ID),chr(Position2DataLength),chr(FrameCheckSum),
						chr(Position2Byte[7]),chr(Position2Byte[6]),chr(Position2Byte[5]),chr(Position2Byte[4]),
						chr(Position2Byte[3]),chr(Position2Byte[2]),chr(Position2Byte[1]),chr(Position2Byte[0]),
						chr(Speed2Byte[3]),chr(Speed2Byte[2]),chr(Speed2Byte[1]),chr(Speed2Byte[0]),chr(DataCheckByte)]))
		else:
			PosCom2String = bytearray([self.Header,Position2Com,_ID,Position2DataLength,FrameCheckSum,Position2Byte[7],Position2Byte[6],
				Position2Byte[5],Position2Byte[4],Position2Byte[3],Position2Byte[2],Position2Byte[1],Position2Byte[0], Speed2Byte[3],
				Speed2Byte[2],Speed2Byte[1],Speed2Byte[0],DataCheckByte])


		# Write data out to usb port
		self.WriteData(PosCom2String)

	def PositionControlMode3(self,ID,Deg,Direction):

		# Constant value
		DegLSB = int(Deg*100.0)
		Position3Com = 0xA5
		Position3DataLength = 0x04
		_ID = ID
		FrameCheckSum = self.Header + Position3Com + Position3DataLength + _ID

		Position3Byte = self.SplitTo4Byte(DegLSB)
		DataCheckByte = Direction + Position3Byte[3] + Position3Byte[2] + Position3Byte[1]

		DataCheckByte = DataCheckByte & 0x00FF   # eliminate the second byte, only need 1 byte 

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			PosCom3String = str(bytearray([chr(self.Header),chr(Position3Com),chr(_ID),chr(Position3DataLength),chr(FrameCheckSum),
							chr(Direction),chr(Position3Byte[3]),chr(Position3Byte[2]),chr(Position3Byte[1]),chr(DataCheckByte)]))
		else:
			PosCom3String = bytearray([self.Header,Position3Com,_ID,Position3DataLength,FrameCheckSum,Direction,
							Position3Byte[3],Position3Byte[2],Position3Byte[1],DataCheckByte])

		# Write data out to usb port
		self.WriteData(PosCom3String)

	def PositionControlMode4(self,ID,Deg,DPS,Direction):

		# Constant value
		DegLSB = int(Deg*100.0)
		SpeedLSB = int(DPS*100.0)

		Position4Com = 0xA6
		Position4DataLength = 0x08
		_ID = ID
		FrameCheckSum = self.Header + Position4Com + Position4DataLength + _ID

		Position4Byte = self.SplitTo4Byte(DegLSB)
		Speed4Byte = self.SplitTo4Byte(SpeedLSB)
		DataCheckByte = Direction + Position4Byte[3] + Position4Byte[2] + Position4Byte[1] + Position4Byte[0] + Speed4Byte[3] + Speed4Byte[2] + Speed4Byte[1] + Speed4Byte[0]

		DataCheckByte = DataCheckByte & 0x000000FF   # eliminate the second byte, only need 1 byte 

		# Construct each hexadecimal byte into single string list
		if self.ver == 2:
			PosCom4String = str(bytearray([chr(self.Header),chr(Position4Com),chr(_ID),chr(Position4DataLength),chr(FrameCheckSum),
							chr(Direction),chr(Position4Byte[3]),chr(Position4Byte[2]),chr(Position4Byte[1]),
							chr(Speed4Byte[3]),chr(Speed4Byte[2]),chr(Speed4Byte[1]),chr(Speed4Byte[0]),chr(DataCheckByte)]))
		else:
			PosCom4String = bytearray([self.Header,Position4Com,_ID,Position4DataLength,FrameCheckSum,Direction,Position4Byte[3],
							Position4Byte[2],Position4Byte[1],Speed4Byte[3],Speed4Byte[2],Speed4Byte[1],Speed4Byte[0],DataCheckByte])

		# Write data out to usb port
		self.WriteData(PosCom4String)
