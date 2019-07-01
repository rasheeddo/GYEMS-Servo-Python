from GYEMSClass import *
import time

GY = GYEMS(1)  # create an object with servo ID 1
GY2 = GYEMS(2)  # create an object with servo ID 2

## Uncomment one of these modes for testing
## Reset power ON/OFF when changes mode

# [Multi-turns with maximum speed mode]
#GY.PositionControlMode1(480)			# input: targetAngle in degree  

# [Multi-turns with desired speed mode]		
#GY.PositionControlMode2(150,360)		# input: targetAngle, targetSpeed in degree and degree/seconds 	

# [Single-turn with max. speed and direction mode]										
#GY.PositionControlMode3(40,1)			# input: targetAngle (0~360), direction in degree and 0 for clockwise, 1 for couter-clockwise	

# [Single-turn with desired speed and direction mode]	
GY.PositionControlMode4(0,90,1)		# input: targetAngle (0~360), targetSpeed, direction in degree, degree/seconds and 0 for clockwise, 1 for couter-clockwise
GY2.PositionControlMode4(0,180,1)

while True:

	# read current angle from encoder
	# the angle would be 0~360 degree works well with Mode3 and Mode4, 
	# but in multi-turns mode the encoder cannot cummulate the turns, so the angle would show 0~360
	CurrentDeg1 = GY.GetCurrentDeg()
	CurrentDeg2 = GY2.GetCurrentDeg()
	print('CurrentDeg1',CurrentDeg1)
	print('CurrentDeg2',CurrentDeg2)
	print('--------------')
	time.sleep(0.01)
