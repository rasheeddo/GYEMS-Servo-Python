from GYEMSClass import *
import time

GY = GYEMS()  # create an object


## Uncomment one of these modes for testing
## Reset power ON/OFF when changes mode

#GY.SpeedControl(1,360)
#GY.SpeedControl(2,360)

# [Multi-turns with maximum speed mode]
#GY.PositionControlMode1(1,90)			# input: targetAngle in degree 
#GY.PositionControlMode1(2,180) 

# [Multi-turns with desired speed mode]		
#GY.PositionControlMode2(1,150,360)		# input: targetAngle, targetSpeed in degree and degree/seconds 	

# [Single-turn with max. speed and direction mode]										
#GY.PositionControlMode3(1,40,1)			# input: targetAngle (0~360), direction in degree and 0 for clockwise, 1 for couter-clockwise	

# [Single-turn with desired speed and direction mode]	
GY.PositionControlMode4(1,91.5,90,1)		# input: targetAngle (0~360), targetSpeed, direction in degree, degree/seconds and 0 for clockwise, 1 for couter-clockwise
GY.PositionControlMode4(2,120.7,180,1)

while True:

	# read current angle from encoder
	# the angle would be 0~360 degree works well with Mode3 and Mode4, 
	# but in multi-turns mode the encoder cannot cummulate the turns, so the angle would show 0~360
	CurrentDeg1 = GY.GetCurrentDeg(1)
	CurrentDeg2 = GY.GetCurrentDeg(2)
	print('CurrentDeg1',CurrentDeg1)
	print('CurrentDeg2',CurrentDeg2)
	print('--------------')
	time.sleep(0.01)
