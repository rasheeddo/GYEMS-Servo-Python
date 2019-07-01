from GYEMSClass import *
import time

GY = GYEMS(1)	# create an object with servo ID

## Reset power ON/OFF if changed mode from any PositionControl

# [Speed Control for wheels robot]
GY.SpeedControl(360)			# input: targetSpeed in degree/seconds


while True:
	# This is to show the motor can stop and continue running by using these two functions
	GY.MotorStop()
	print("Motor Stop")
	time.sleep(2)
	GY.MotorRun()
	print("Motor Run")
	time.sleep(2)

