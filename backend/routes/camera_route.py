import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from camera import camera, vision_thresholds, DEFAULT_VISION_THRESHOLDS

router = APIRouter(prefix="/api")


@router.get("/camera/analysis")
def get_camera_analysis():
    # returns latest opencv analysis results for the camera view
    return camera.get_analysis()


@router.get("/camera/stream")
def camera_stream():
    # streams mjpeg frames for the live camera feed in the dashboard
    def generate():
        while True:
            frame = camera.get_frame()
            if frame:
                # mjpeg multipart format expected by <img> tags with src pointing here
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
            # match the capture rate so this loop doesn't spin the cpu resending the same frame
            time.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/camera/thresholds")
def get_vision_thresholds():
    # current opencv thresholds for the settings view
    return vision_thresholds


@router.post("/camera/thresholds")
def update_vision_thresholds(clear_brightness: float, turbid_brightness: float, debris_min_area: float):
    # update the opencv thresholds at runtime without restarting the server
    if turbid_brightness >= clear_brightness:
        raise HTTPException(status_code=400, detail="turbid_brightness must be below clear_brightness")
    vision_thresholds["clear_brightness"] = clear_brightness
    vision_thresholds["turbid_brightness"] = turbid_brightness
    vision_thresholds["debris_min_area"] = debris_min_area
    return vision_thresholds


@router.post("/camera/thresholds/reset")
def reset_vision_thresholds():
    # reset the opencv thresholds back to default values
    vision_thresholds.update(DEFAULT_VISION_THRESHOLDS)
    return vision_thresholds