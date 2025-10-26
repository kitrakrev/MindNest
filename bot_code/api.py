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
    GET  /status        - Get robot status
    POST /connect       - Connect to robot
    POST /disconnect    - Disconnect from robot
"""

import random
import logging
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
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
            ],
            "actions": [
                "POST /shake - Perform shake animation",
                "POST /rest - Return to rest position",
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


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FastAPI server...")
    logger.info("API documentation will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

