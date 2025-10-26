from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
import cv2
import numpy as np

# 1. Load pretrained SmolVLA model
policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base").eval()

# 2. Connect to the robot using SO101Follower
robot_config = SO101FollowerConfig(port="/dev/ttyUSB0")
robot = SO101Follower(robot_config)

# 3. Initialize camera (e.g., webcam or RealSense)
cam = cv2.VideoCapture(0)

task = "pick up the red cube and place it in the box"

while True:
    # Capture frame
    ret, frame = cam.read()
    if not ret:
        continue

    # Get robot joint states
    obs = robot.get_observation()  # returns joint positions, velocities, etc.

    # Combine with image and task
    input_dict = {
        "observation.image": frame[:, :, ::-1],  # BGR->RGB
        "observation.state": obs,
        "task": task,
    }

    # Predict next action
    action = policy.predict(input_dict)

    # Apply action to robot
    robot.apply_action(action)
