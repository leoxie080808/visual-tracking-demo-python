# visual tracking tool 
Python script to demonstrate the localization algorithm and associated motion algorithms
Features: 
- moveToPoint performance varient: prioritizes quickly turning to target while moving before traversing near max speed
- pure pursuit: path following for multiple waypoints, reducing accel and decel times between each point
- reset: clear field to view new trajectories
- dynamically updating co ordinate system (arbitrary units)

To do: 
- moveToPoint angle enforcement varient: enforces an ending angle by introducing an intermediate point near target position
- model-based predictive control
 
