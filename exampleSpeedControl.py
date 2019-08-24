from GYEMSClass import *
import time

GY = GYEMS()	# create an object

## Reset power ON/OFF if changed mode from any PositionControl

# [Speed Control for wheels robot]
GY.SpeedControl(1,360.5)			# input: targetSpeed in degree/seconds


while True:
	# This is the function for estimating the speed of the servo
	# So the value may be swing up/down a bit due to the differentiate of the angle and average
	AVESpeed = GY.GetAverageSpeed(1)
	print(AVESpeed)
	print('--------------')
	# No delay needs because there is a delay for estimating the speed