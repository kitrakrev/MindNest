"""
FastAPI server for SO-101 Rock-Paper-Scissors Robot Controller

Exposes REST API endpoints to control the robot's rock, paper, and scissors gestures.

Usage:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    GET  /              - API documentation
    GET  /health        - Health check
    POST /rock          - Play rock gesture
    POST /paper         - Play paper gesture
    POST /scissors      - Play scissors gesture
    POST /random        - Play random gesture (rock/paper/scissors)
    POST /shake         - Perform shake animation
    POST /rest          - Return to rest position
    POST /yes           - Nod gesture (up and down)
    POST /no            - Shake head gesture (left to right in center)
    POST /reach_human   - Find nearest human and reach out to them
    GET  /status        - Get robot status
    POST /connect       - Connect to robot
    POST /disconnect    - Disconnect from robot
"""

import random
import logging
import time
import cv2
import numpy as np
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from rps_controller import RPSController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global robot controller instance
robot_controller: Optional[RPSController] = None


# Pydantic models for request/response
class GestureRequest(BaseModel):
    """Request model for gesture actions."""
    duration: float = Field(default=3.0, ge=0.1, le=10.0, description="Duration to hold gesture (seconds)")
    with_shake: bool = Field(default=False, description="Whether to shake before showing gesture")


class ShakeRequest(BaseModel):
    """Request model for shake action."""
    amplitude: int = Field(default=80, ge=20, le=200, description="Shake amplitude")
    shakes: int = Field(default=2, ge=1, le=5, description="Number of shakes")


class ConnectRequest(BaseModel):
    """Request model for robot connection."""
    port: Optional[str] = Field(default=None, description="Serial port (auto-detect if None)")


class YesNoRequest(BaseModel):
    """Request model for yes/no gestures."""
    repetitions: int = Field(default=3, ge=1, le=10, description="Number of times to repeat gesture")
    speed: float = Field(default=1.0, ge=0.5, le=3.0, description="Speed multiplier")


class GestureResponse(BaseModel):
    """Response model for gesture actions."""
    success: bool
    gesture: str
    message: str
    duration: Optional[float] = None


class StatusResponse(BaseModel):
    """Response model for robot status."""
    connected: bool
    current_gesture: Optional[str]
    port: Optional[str]
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Rock-Paper-Scissors API server...")
    global robot_controller
    
    try:
        robot_controller = RPSController()
        logger.info("✓ Robot controller initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize robot controller: {e}")
        robot_controller = None
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API server...")
    if robot_controller:
        try:
            robot_controller.disconnect()
            logger.info("✓ Robot disconnected")
        except Exception as e:
            logger.error(f"❌ Error disconnecting robot: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="SO-101 Rock-Paper-Scissors API",
    description="REST API for controlling SO-101 robot arm to play rock-paper-scissors",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SO-101 Rock-Paper-Scissors API",
        "version": "1.0.0",
        "description": "Control the SO-101 robot arm to play rock-paper-scissors gestures",
        "endpoints": {
            "gestures": [
                "POST /rock - Play rock gesture",
                "POST /paper - Play paper gesture",
                "POST /scissors - Play scissors gesture",
                "POST /random - Play random gesture",
                "POST /yes - Nod gesture (up and down)",
                "POST /no - Shake head gesture (left to right)",
            ],
            "actions": [
                "POST /shake - Perform shake animation",
                "POST /rest - Return to rest position",
                "POST /reach_human - Find nearest human and reach out",
                "POST /follow_human - Continuously track and follow human movement",
            ],
            "system": [
                "GET /health - Health check",
                "GET /status - Get robot status",
                "POST /connect - Connect to robot",
                "POST /disconnect - Disconnect from robot",
            ]
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if robot_controller is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Robot controller not initialized"
            }
        )
    
    connected = robot_controller.check_connectivity()
    
    return {
        "status": "healthy" if connected else "degraded",
        "robot_connected": connected,
        "message": "Robot is connected" if connected else "Robot not connected"
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current robot status."""
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    connected = robot_controller.check_connectivity()
    
    return StatusResponse(
        connected=connected,
        current_gesture=robot_controller.current_gesture if connected else None,
        port=robot_controller.port if robot_controller else None,
        message="Robot is operational" if connected else "Robot not connected"
    )


@app.post("/connect")
async def connect(request: ConnectRequest = ConnectRequest()):
    """Connect to the robot."""
    global robot_controller
    
    try:
        if robot_controller is None:
            robot_controller = RPSController(port=request.port)
        
        if robot_controller.check_connectivity():
            return {
                "success": True,
                "message": f"Connected to robot on port {robot_controller.port}",
                "port": robot_controller.port
            }
        else:
            raise HTTPException(status_code=503, detail="Failed to connect to robot")
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@app.post("/disconnect")
async def disconnect():
    """Disconnect from the robot."""
    global robot_controller
    
    if robot_controller is None:
        return {"success": True, "message": "Robot already disconnected"}
    
    try:
        robot_controller.disconnect()
        return {
            "success": True,
            "message": "Robot disconnected successfully"
        }
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")


def ensure_centered_position():
    """
    Ensure the robot is at a centered, ready position before performing gestures.
    This moves the robot to a neutral centered position for visibility.
    """
    logger.info("📍 Moving to centered position...")
    # Move to rest position first to ensure centered
    success = robot_controller.move_to_gesture("rest", duration=1.0, with_shake=False)
    if not success:
        logger.warning("⚠️ Failed to move to center, continuing anyway...")
    return success


def move_gripper_only(gesture_name: str, duration: float = 3.0):
    """
    Move ONLY the gripper to show rock/paper/scissors gesture.
    All other joints remain at centered position (2048).
    
    Args:
        gesture_name: "rock", "paper", or "scissors"
        duration: How long to hold the gesture
    
    Returns:
        True if successful, False otherwise
    """
    # Centered position for all joints except gripper
    CENTERED_GRIPPER_GESTURES = {
        "rock": {
            "shoulder_pan": 2048,
            "shoulder_lift": 2048,
            "elbow_flex": 2048,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 1200,  # Tight closed fist (gripper fully closed)
        },
        "paper": {
            "shoulder_pan": 2048,
            "shoulder_lift": 2048,
            "elbow_flex": 2048,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 2900,  # Open hand (gripper fully open)
        },
        "scissors": {
            "shoulder_pan": 2048,
            "shoulder_lift": 2048,
            "elbow_flex": 2048,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 2200,  # Partially open (V shape, gripper half open)
        },
    }
    
    if gesture_name not in CENTERED_GRIPPER_GESTURES:
        logger.error(f"Invalid gesture: {gesture_name}")
        return False
    
    positions = CENTERED_GRIPPER_GESTURES[gesture_name]
    
    try:
        # Move to centered position first (if not already there)
        logger.info(f"🤖 Ensuring centered position, then showing {gesture_name} with gripper only")
        
        # Move all joints to center except gripper
        for motor_name, target_pos in positions.items():
            if motor_name in robot_controller.motors:
                robot_controller.smooth_move(motor_name, target_pos, steps=50, total_time=2.0)
        
        # Hold the gesture
        import time
        time.sleep(duration)
        robot_controller.current_gesture = gesture_name
        logger.info(f"✓ Gripper-only gesture '{gesture_name}' completed (held for {duration}s)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in gripper-only gesture '{gesture_name}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@app.post("/rock", response_model=GestureResponse)
async def play_rock(request: GestureRequest = GestureRequest()):
    """
    Play the ROCK gesture using ONLY the gripper.
    
    The robot stays centered and only closes the gripper to form a fist.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"🪨 Executing ROCK gesture (gripper-only, duration={request.duration}s, shake={request.with_shake})")
    
    try:
        # Optional shake before gesture
        if request.with_shake:
            logger.info("🤝 Shaking before gesture...")
            robot_controller.shake_gesture()
        
        # Move gripper only from centered position
        success = move_gripper_only("rock", duration=request.duration)
        
        if success:
            return GestureResponse(
                success=True,
                gesture="rock",
                message="Rock gesture executed (gripper-only from centered position)",
                duration=request.duration
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to execute rock gesture")
            
    except Exception as e:
        logger.error(f"Error executing rock gesture: {e}")
        raise HTTPException(status_code=500, detail=f"Gesture execution failed: {str(e)}")


@app.post("/paper", response_model=GestureResponse)
async def play_paper(request: GestureRequest = GestureRequest()):
    """
    Play the PAPER gesture using ONLY the gripper.
    
    The robot stays centered and only opens the gripper to form an open hand.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"📄 Executing PAPER gesture (gripper-only, duration={request.duration}s, shake={request.with_shake})")
    
    try:
        # Optional shake before gesture
        if request.with_shake:
            logger.info("🤝 Shaking before gesture...")
            robot_controller.shake_gesture()
        
        # Move gripper only from centered position
        success = move_gripper_only("paper", duration=request.duration)
        
        if success:
            return GestureResponse(
                success=True,
                gesture="paper",
                message="Paper gesture executed (gripper-only from centered position)",
                duration=request.duration
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to execute paper gesture")
            
    except Exception as e:
        logger.error(f"Error executing paper gesture: {e}")
        raise HTTPException(status_code=500, detail=f"Gesture execution failed: {str(e)}")


@app.post("/scissors", response_model=GestureResponse)
async def play_scissors(request: GestureRequest = GestureRequest()):
    """
    Play the SCISSORS gesture using ONLY the gripper.
    
    The robot stays centered and only partially opens the gripper to form a V-shape.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"✂️ Executing SCISSORS gesture (gripper-only, duration={request.duration}s, shake={request.with_shake})")
    
    try:
        # Optional shake before gesture
        if request.with_shake:
            logger.info("🤝 Shaking before gesture...")
            robot_controller.shake_gesture()
        
        # Move gripper only from centered position
        success = move_gripper_only("scissors", duration=request.duration)
        
        if success:
            return GestureResponse(
                success=True,
                gesture="scissors",
                message="Scissors gesture executed (gripper-only from centered position)",
                duration=request.duration
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to execute scissors gesture")
            
    except Exception as e:
        logger.error(f"Error executing scissors gesture: {e}")
        raise HTTPException(status_code=500, detail=f"Gesture execution failed: {str(e)}")


@app.post("/random", response_model=GestureResponse)
async def play_random(request: GestureRequest = GestureRequest()):
    """
    Play a RANDOM gesture using ONLY the gripper.
    
    The robot stays centered and randomly chooses rock, paper, or scissors with the gripper.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    # Randomly choose a gesture
    gestures = ["rock", "paper", "scissors"]
    chosen_gesture = random.choice(gestures)
    
    logger.info(f"🎲 Executing RANDOM gesture: {chosen_gesture.upper()} (gripper-only, duration={request.duration}s, shake={request.with_shake})")
    
    try:
        # Optional shake before gesture
        if request.with_shake:
            logger.info("🤝 Shaking before gesture...")
            robot_controller.shake_gesture()
        
        # Move gripper only from centered position
        success = move_gripper_only(chosen_gesture, duration=request.duration)
        
        if success:
            return GestureResponse(
                success=True,
                gesture=chosen_gesture,
                message=f"Random gesture executed (gripper-only): {chosen_gesture}",
                duration=request.duration
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to execute random gesture: {chosen_gesture}")
            
    except Exception as e:
        logger.error(f"Error executing random gesture: {e}")
        raise HTTPException(status_code=500, detail=f"Gesture execution failed: {str(e)}")


@app.post("/shake")
async def shake(request: ShakeRequest = ShakeRequest()):
    """
    Perform a shake animation.
    
    The robot will shake its arm as if preparing to throw in rock-paper-scissors.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"🤝 Executing SHAKE (amplitude={request.amplitude}, shakes={request.shakes})")
    
    try:
        success = robot_controller.shake_gesture(
            amplitude=request.amplitude,
            shakes=request.shakes
        )
        
        if success:
            return {
                "success": True,
                "message": f"Shake animation executed successfully ({request.shakes} shakes)",
                "amplitude": request.amplitude,
                "shakes": request.shakes
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to execute shake animation")
            
    except Exception as e:
        logger.error(f"Error executing shake: {e}")
        raise HTTPException(status_code=500, detail=f"Shake execution failed: {str(e)}")


@app.post("/rest", response_model=GestureResponse)
async def move_to_rest():
    """
    Move robot to rest position.
    
    Returns the robot to its neutral/rest position.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info("🏠 Moving to REST position")
    
    try:
        success = robot_controller.move_to_gesture("rest", duration=2.0, with_shake=False)
        
        if success:
            return GestureResponse(
                success=True,
                gesture="rest",
                message="Moved to rest position successfully",
                duration=2.0
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to move to rest position")
            
    except Exception as e:
        logger.error(f"Error moving to rest: {e}")
        raise HTTPException(status_code=500, detail=f"Rest movement failed: {str(e)}")


@app.post("/yes")
async def gesture_yes(request: YesNoRequest = YesNoRequest()):
    """
    Perform a "yes" gesture - nodding up and down.
    
    The robot will nod vertically in the center position.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"👍 Executing YES gesture (nod up/down, repetitions={request.repetitions}, speed={request.speed})")
    
    try:
        success = perform_yes_gesture(request.repetitions, request.speed)
        
        if success:
            return {
                "success": True,
                "gesture": "yes",
                "message": f"Yes gesture completed ({request.repetitions} nods)",
                "repetitions": request.repetitions
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to execute yes gesture")
            
    except Exception as e:
        logger.error(f"Error executing yes gesture: {e}")
        raise HTTPException(status_code=500, detail=f"Yes gesture failed: {str(e)}")


@app.post("/no")
async def gesture_no(request: YesNoRequest = YesNoRequest()):
    """
    Perform a "no" gesture - shaking left to right in center position.
    
    The robot will shake horizontally while staying centered.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"👎 Executing NO gesture (shake left/right, repetitions={request.repetitions}, speed={request.speed})")
    
    try:
        success = perform_no_gesture(request.repetitions, request.speed)
        
        if success:
            return {
                "success": True,
                "gesture": "no",
                "message": f"No gesture completed ({request.repetitions} shakes)",
                "repetitions": request.repetitions
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to execute no gesture")
            
    except Exception as e:
        logger.error(f"Error executing no gesture: {e}")
        raise HTTPException(status_code=500, detail=f"No gesture failed: {str(e)}")


@app.post("/reach_human")
async def reach_human():
    """
    Find the nearest human using camera 1 and reach out to them.
    
    Uses OpenCV face detection to locate humans and moves the robot arm towards them.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info("👋 Detecting nearest human and reaching out...")
    
    try:
        result = detect_and_reach_human()
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "human_detected": result["detected"],
                "position": result.get("position", None)
            }
        else:
            return {
                "success": False,
                "message": result["message"],
                "human_detected": False
            }
            
    except Exception as e:
        logger.error(f"Error in reach_human: {e}")
        raise HTTPException(status_code=500, detail=f"Reach human failed: {str(e)}")


class FollowRequest(BaseModel):
    """Request model for follow human action."""
    duration: int = Field(default=30, ge=5, le=120, description="How long to follow (seconds)")
    update_rate: float = Field(default=1.0, ge=0.5, le=3.0, description="How often to update position (seconds)")


@app.post("/follow_human")
async def follow_human(request: FollowRequest = FollowRequest()):
    """
    Continuously follow a human by tracking their movement.
    
    The robot will scan for a human, then keep tracking and following their position
    as they move around. Continues for the specified duration.
    """
    if robot_controller is None:
        raise HTTPException(status_code=503, detail="Robot controller not initialized")
    
    if not robot_controller.check_connectivity():
        raise HTTPException(status_code=503, detail="Robot not connected")
    
    logger.info(f"👁️ Starting to follow human for {request.duration} seconds...")
    
    try:
        result = continuous_follow_human(duration=request.duration, update_rate=request.update_rate)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "tracking_info": result.get("tracking_info", {})
            }
        else:
            return {
                "success": False,
                "message": result["message"]
            }
            
    except Exception as e:
        logger.error(f"Error in follow_human: {e}")
        raise HTTPException(status_code=500, detail=f"Follow human failed: {str(e)}")


def perform_yes_gesture(repetitions: int = 3, speed: float = 1.0) -> bool:
    """
    Perform a "yes" nod gesture (up and down movement).
    
    Args:
        repetitions: Number of nods
        speed: Speed multiplier (higher = faster)
    
    Returns:
        True if successful
    """
    if not robot_controller or not robot_controller.bus:
        logger.error("Robot not initialized")
        return False
    
    try:
        # Center position
        base_lift = 2048
        amplitude = 300  # Nod amplitude
        
        # Calculate timing based on speed
        move_time = 0.5 / speed
        
        # Start from center
        robot_controller.smooth_move("shoulder_lift", base_lift, steps=30, total_time=1.0)
        time.sleep(0.3)
        
        # Nod up and down
        for i in range(repetitions):
            # Nod up
            robot_controller.smooth_move("shoulder_lift", base_lift - amplitude, steps=20, total_time=move_time)
            time.sleep(0.1)
            
            # Nod down
            robot_controller.smooth_move("shoulder_lift", base_lift + amplitude, steps=20, total_time=move_time)
            time.sleep(0.1)
        
        # Return to center
        robot_controller.smooth_move("shoulder_lift", base_lift, steps=30, total_time=1.0)
        
        logger.info(f"✓ Yes gesture completed ({repetitions} nods)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in yes gesture: {e}")
        return False


def perform_no_gesture(repetitions: int = 3, speed: float = 1.0) -> bool:
    """
    Perform a "no" shake gesture (left to right in center position).
    
    Args:
        repetitions: Number of shakes
        speed: Speed multiplier (higher = faster)
    
    Returns:
        True if successful
    """
    if not robot_controller or not robot_controller.bus:
        logger.error("Robot not initialized")
        return False
    
    try:
        # Center position
        base_pan = 2048
        base_lift = 2048
        amplitude = 200  # Shake amplitude
        
        # Calculate timing based on speed
        move_time = 0.4 / speed
        
        # Ensure centered position first
        robot_controller.smooth_move("shoulder_pan", base_pan, steps=30, total_time=1.0)
        robot_controller.smooth_move("shoulder_lift", base_lift, steps=30, total_time=1.0)
        time.sleep(0.3)
        
        # Shake left and right
        for i in range(repetitions):
            # Shake left
            robot_controller.smooth_move("shoulder_pan", base_pan - amplitude, steps=20, total_time=move_time)
            time.sleep(0.1)
            
            # Shake right
            robot_controller.smooth_move("shoulder_pan", base_pan + amplitude, steps=20, total_time=move_time)
            time.sleep(0.1)
        
        # Return to center
        robot_controller.smooth_move("shoulder_pan", base_pan, steps=30, total_time=1.0)
        
        logger.info(f"✓ No gesture completed ({repetitions} shakes)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in no gesture: {e}")
        return False


def continuous_follow_human(duration: int = 30, update_rate: float = 1.0) -> Dict:
    """
    Continuously track and follow a human's movement.
    
    Args:
        duration: How long to follow (seconds)
        update_rate: How often to update position (seconds)
    
    Returns:
        Dict with success status and tracking info
    """
    if not robot_controller or not robot_controller.bus:
        return {"success": False, "message": "Robot not initialized"}
    
    try:
        # Open camera
        logger.info("📷 Opening camera for continuous tracking...")
        cap = cv2.VideoCapture(1)
        
        if not cap.isOpened():
            logger.warning("Camera 1 not available, trying camera 0...")
            cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logger.error("No camera available")
            return {"success": False, "message": "No camera available"}
        
        # Load face detection cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Initial scan to find human
        logger.info("🔍 Initial scan to locate human...")
        initial_result = _scan_for_human(cap, face_cascade)
        
        if not initial_result["found"]:
            cap.release()
            return {"success": False, "message": "No human detected in initial scan"}
        
        logger.info(f"✓ Human found! Starting continuous tracking for {duration}s...")
        
        # Tracking statistics
        start_time = time.time()
        update_count = 0
        lost_count = 0
        max_lost_frames = 5
        
        last_position = None
        movement_history = []
        
        # Create display window
        cv2.namedWindow('Robot Vision - Following Human', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Robot Vision - Following Human', 800, 600)
        
        # Continuous tracking loop - rapid updates
        while time.time() - start_time < duration:
            # Capture current frame
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Create a copy for display
            display_frame = frame.copy()
            
            # Detect face in current frame (more aggressive detection)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
            
            if len(faces) > 0:
                # Draw all detected faces
                for (fx, fy, fw, fh) in faces:
                    cv2.rectangle(display_frame, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 2)
                
                # Found face - track the largest one
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                
                # Draw special marker for tracked face
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 255), 3)
                
                # Calculate face center
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                
                # Draw crosshair on face center
                cv2.drawMarker(display_frame, (face_center_x, face_center_y), 
                              (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
                
                frame_width = frame.shape[1]
                frame_height = frame.shape[0]
                
                # Draw center reference
                cv2.line(display_frame, (frame_width // 2, 0), 
                        (frame_width // 2, frame_height), (255, 0, 0), 1)
                cv2.line(display_frame, (0, frame_height // 2), 
                        (frame_width, frame_height // 2), (255, 0, 0), 1)
                
                # Normalize to -1 to 1 range
                normalized_x = (face_center_x / frame_width) * 2 - 1
                normalized_y = (face_center_y / frame_height) * 2 - 1
                
                # Detect movement direction if we have previous position
                direction_text = ""
                if last_position:
                    dx = normalized_x - last_position["x"]
                    dy = normalized_y - last_position["y"]
                    movement_history.append({"dx": dx, "dy": dy, "time": time.time()})
                    
                    # Keep only recent history (last 5 movements)
                    if len(movement_history) > 5:
                        movement_history.pop(0)
                    
                    # Log movement
                    direction = ""
                    if abs(dx) > 0.05:
                        direction += "→" if dx > 0 else "←"
                    if abs(dy) > 0.05:
                        direction += "↓" if dy > 0 else "↑"
                    
                    if direction:
                        direction_text = f"Moving {direction}"
                        logger.info(f"  Human moving {direction} (dx={dx:.2f}, dy={dy:.2f})")
                
                last_position = {"x": normalized_x, "y": normalized_y}
                lost_count = 0  # Reset lost counter
                
                # Calculate target position directly (more responsive - don't read current position)
                # Center at 2048, adjust based on face position
                target_pan = int(2048 - normalized_x * 500)  # More aggressive tracking
                target_lift = int(2048 + normalized_y * 250)  # More aggressive tracking
                
                # Clamp to safe range and never go down (lift stays at or above 2048)
                target_pan = max(1500, min(2600, target_pan))
                target_lift = max(1700, min(2048, target_lift))  # Never go below center
                
                # Move quickly to new position (faster response)
                robot_controller.smooth_move("shoulder_pan", target_pan, steps=10, total_time=0.3)
                robot_controller.smooth_move("shoulder_lift", target_lift, steps=10, total_time=0.3)
                
                update_count += 1
                logger.info(f"  👁️ Tracking #{update_count}: pan={target_pan}, lift={target_lift}, face=({normalized_x:.2f},{normalized_y:.2f})")
                
                # Add tracking info overlay
                elapsed = int(time.time() - start_time)
                cv2.putText(display_frame, f"TRACKING - Update #{update_count}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Time: {elapsed}s / {duration}s", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(display_frame, f"Position: ({normalized_x:.2f}, {normalized_y:.2f})", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                if direction_text:
                    cv2.putText(display_frame, direction_text, 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
            else:
                # Lost track of human
                lost_count += 1
                logger.warning(f"  ⚠️ Lost track of human (count: {lost_count}/{max_lost_frames})")
                
                # Add lost tracking overlay
                cv2.putText(display_frame, f"SEARCHING... ({lost_count}/{max_lost_frames})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                if lost_count >= max_lost_frames:
                    logger.info("  🔍 Re-scanning for human...")
                    cv2.putText(display_frame, "RE-SCANNING...", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    rescan_result = _scan_for_human(cap, face_cascade)
                    
                    if rescan_result["found"]:
                        logger.info("  ✓ Human re-acquired!")
                        lost_count = 0
                    else:
                        logger.warning("  ❌ Human not found in re-scan")
            
            # Show the frame
            cv2.imshow('Robot Vision - Following Human', display_frame)
            
            # Check for 'q' key to quit early
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("User pressed 'q' - stopping tracking early")
                break
            
            # Minimal wait - more responsive tracking
            time.sleep(0.2)  # Update 5 times per second
        
        # Tracking complete
        cap.release()
        cv2.destroyAllWindows()  # Close the display window
        elapsed_time = time.time() - start_time
        
        # Return to center
        logger.info("🏠 Tracking complete, returning to center...")
        robot_controller.smooth_move("shoulder_pan", 2048, steps=30, total_time=1.5)
        robot_controller.smooth_move("shoulder_lift", 2048, steps=30, total_time=1.5)
        
        return {
            "success": True,
            "message": f"Successfully tracked human for {elapsed_time:.1f} seconds",
            "tracking_info": {
                "duration": elapsed_time,
                "updates": update_count,
                "movements_detected": len(movement_history),
                "average_update_rate": elapsed_time / max(update_count, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in continuous tracking: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}"}


def _scan_for_human(cap, face_cascade) -> Dict:
    """
    Helper function to scan for a human across multiple positions.
    Returns dict with 'found' boolean and position info.
    """
    # Define scan positions - same as reach_human but simpler
    scan_positions = [
        (2048, 2048),  # Center
        (2048, 1950),  # Center-up
        (1900, 2048),  # Left
        (2200, 2048),  # Right
        (1750, 2048),  # Far left
        (2350, 2048),  # Far right
    ]
    
    for pan, lift in scan_positions:
        # Move to scan position
        robot_controller.smooth_move("shoulder_pan", pan, steps=15, total_time=0.6)
        robot_controller.smooth_move("shoulder_lift", lift, steps=15, total_time=0.6)
        time.sleep(0.2)
        
        # Capture and detect
        ret, frame = cap.read()
        if not ret:
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) > 0:
            # Found someone!
            return {"found": True, "position": (pan, lift)}
    
    return {"found": False}


def detect_and_reach_human() -> Dict:
    """
    Scan through different positions to find the nearest human face and reach out.
    
    The robot will scan left-to-right and different heights to find a person.
    
    Returns:
        Dict with success status, message, and detection info
    """
    if not robot_controller or not robot_controller.bus:
        return {"success": False, "message": "Robot not initialized", "detected": False}
    
    try:
        # Open camera 1 (index 1, or try 0 if 1 doesn't work)
        logger.info("📷 Opening camera for scanning...")
        cap = cv2.VideoCapture(1)
        
        # If camera 1 doesn't work, try camera 0
        if not cap.isOpened():
            logger.warning("Camera 1 not available, trying camera 0...")
            cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logger.error("No camera available")
            return {"success": False, "message": "No camera available", "detected": False}
        
        # Load face detection cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Define scan positions (pan, lift)
        # START FROM CENTER, then scan UP and SIDEWAYS (never down)
        # Lower lift values = higher position
        scan_positions = [
            # Start at center position
            (2048, 2048),  # 1. Center-center (starting point)
            
            # Look up from center (progressively higher)
            (2048, 1950),  # 2. Center-slightly up
            (2048, 1850),  # 3. Center-up
            (2048, 1750),  # 4. Center-high up
            
            # Look left from center (staying at center height)
            (1900, 2048),  # 5. Slightly left-center
            (1750, 2048),  # 6. Left-center
            (1600, 2048),  # 7. Far left-center
            
            # Look right from center (staying at center height)
            (2200, 2048),  # 8. Slightly right-center
            (2350, 2048),  # 9. Right-center
            (2500, 2048),  # 10. Far right-center
            
            # Look left-up diagonal
            (1750, 1850),  # 11. Left-up
            (1600, 1850),  # 12. Far left-up
            
            # Look right-up diagonal
            (2350, 1850),  # 13. Right-up
            (2500, 1850),  # 14. Far right-up
        ]
        
        logger.info(f"🔍 Scanning {len(scan_positions)} positions for humans...")
        
        best_face = None
        best_position = None
        best_face_size = 0
        
        # Scan through all positions
        for idx, (pan, lift) in enumerate(scan_positions):
            logger.info(f"  Scanning position {idx + 1}/{len(scan_positions)}: pan={pan}, lift={lift}")
            
            # Move to scan position
            robot_controller.smooth_move("shoulder_pan", pan, steps=20, total_time=0.8)
            robot_controller.smooth_move("shoulder_lift", lift, steps=20, total_time=0.8)
            time.sleep(0.3)  # Wait for camera to stabilize
            
            # Capture frame at this position
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"  Failed to capture at position {idx + 1}")
                continue
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) > 0:
                # Find the largest face at this position
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                face_size = w * h
                
                logger.info(f"  ✓ Found face at position {idx + 1}! Size: {face_size}")
                
                # Keep track of the best (largest/nearest) face found
                if face_size > best_face_size:
                    best_face = (x, y, w, h)
                    best_position = (pan, lift, frame.shape[1], frame.shape[0])
                    best_face_size = face_size
                    logger.info(f"  🎯 New best face found! Size: {face_size}")
        
        # Release camera
        cap.release()
        
        # Check if we found any faces
        if best_face is None:
            logger.warning("❌ No human face detected in any position")
            # Return to center
            robot_controller.smooth_move("shoulder_pan", 2048, steps=30, total_time=1.5)
            robot_controller.smooth_move("shoulder_lift", 2048, steps=30, total_time=1.5)
            return {"success": False, "message": "No human detected after full scan", "detected": False}
        
        # Unpack best face and position data
        x, y, w, h = best_face
        best_pan, best_lift, frame_width, frame_height = best_position
        
        # Calculate face center
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        # Normalize to -1 to 1 range
        normalized_x = (face_center_x / frame_width) * 2 - 1
        normalized_y = (face_center_y / frame_height) * 2 - 1
        
        logger.info(f"🎯 Best human detected! Face center: ({normalized_x:.2f}, {normalized_y:.2f})")
        
        # Calculate fine-tuned target position based on where we found the face
        # Start from the scan position where we found them, then adjust
        target_pan = int(best_pan - normalized_x * 200)  # Fine-tune pan
        target_lift = int(best_lift + normalized_y * 150)  # Fine-tune lift
        
        # Clamp values to safe range
        target_pan = max(1500, min(2600, target_pan))
        target_lift = max(1500, min(2600, target_lift))
        
        # Move to precise face position and reach out
        logger.info(f"👋 Reaching out to human at pan={target_pan}, lift={target_lift}")
        
        # Move shoulder to point at human
        robot_controller.smooth_move("shoulder_pan", target_pan, steps=40, total_time=1.5)
        robot_controller.smooth_move("shoulder_lift", target_lift, steps=40, total_time=1.5)
        time.sleep(0.5)
        
        # Extend arm (reach out)
        robot_controller.smooth_move("elbow_flex", 2400, steps=40, total_time=1.5)
        robot_controller.smooth_move("wrist_flex", 2048, steps=30, total_time=1.0)
        
        # Wave gesture
        logger.info("👋 Waving to human...")
        for _ in range(3):
            robot_controller.smooth_move("wrist_roll", 2248, steps=15, total_time=0.4)
            robot_controller.smooth_move("wrist_roll", 1848, steps=15, total_time=0.4)
        robot_controller.smooth_move("wrist_roll", 2048, steps=15, total_time=0.4)
        
        time.sleep(1.0)
        
        # Return to rest
        logger.info("🏠 Returning to rest position...")
        robot_controller.move_to_gesture("rest", duration=2.0, with_shake=False)
        
        return {
            "success": True,
            "message": f"Human detected and greeted after scanning! Face size: {best_face_size}px, Position: ({normalized_x:.2f}, {normalized_y:.2f})",
            "detected": True,
            "position": {"x": normalized_x, "y": normalized_y},
            "scan_info": {
                "positions_scanned": len(scan_positions),
                "face_size": int(best_face_size),
                "found_at_pan": best_pan,
                "found_at_lift": best_lift
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in human detection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}", "detected": False}


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FastAPI server...")
    logger.info("API documentation will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

