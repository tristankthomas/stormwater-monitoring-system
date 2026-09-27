from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from camera import camera

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

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
