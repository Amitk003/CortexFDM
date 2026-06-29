import base64
import os
import cv2
from config.settings import (
    IMAGE_FOLDER,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    JPEG_QUALITY,
)


CAMERA_EXTENSIONS = (".jpg", ".jpeg", ".png")


class MockCameraError(Exception):
    pass


class MockCamera:
    def __init__(self, image_folder=None):
        self.image_folder = image_folder or IMAGE_FOLDER
        self.image_list = []
        self.current_index = 0
        self._scan_images()

    def _scan_images(self):
        if not os.path.isdir(self.image_folder):
            raise MockCameraError(f"Image folder not found: {self.image_folder}")

        all_files = os.listdir(self.image_folder)
        self.image_list = sorted(
            f for f in all_files
            if f.lower().endswith(CAMERA_EXTENSIONS)
        )

        if not self.image_list:
            raise MockCameraError(
                f"No images found in {self.image_folder}. "
                f"Supported formats: {', '.join(CAMERA_EXTENSIONS)}"
            )

    @property
    def total_images(self):
        return len(self.image_list)

    @property
    def current_filename(self):
        if not self.image_list:
            return None
        return self.image_list[self.current_index]

    def get_next_frame(self):
        if not self.image_list:
            raise MockCameraError("No images available")

        filename = self.image_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.image_list)

        filepath = os.path.join(self.image_folder, filename)
        frame = cv2.imread(filepath)
        if frame is None:
            raise MockCameraError(f"Could not read image: {filepath}")

        frame_resized = cv2.resize(frame, (IMAGE_WIDTH, IMAGE_HEIGHT))
        success, buffer = cv2.imencode(".jpg", frame_resized, [
            cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY
        ])
        if not success:
            raise MockCameraError("Failed to encode image as JPEG")

        b64_string = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_string}"

    def reset(self):
        self.current_index = 0

    def list_images(self):
        return list(self.image_list)
