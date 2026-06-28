# Image Requirements for Mock Camera

We need sample images of 3D printing states for the mock camera. The system reads these images in sequence as if they were coming from a live camera feed.

## Required Images

### Perfect Print (2 images)
- Show a clean, successful 3D print
- Smooth layers, no visible defects
- File names: perfect_01.jpg, perfect_02.jpg

### Under-extrusion (2 images)
- Show visible gaps in the printed layers
- Missing or thin walls
- Porous or incomplete infill
- File names: under_extrusion_01.jpg, under_extrusion_02.jpg

### Spaghetti / Total Failure (2 images)
- Show tangled plastic loops printing in the air
- Print detached from the bed
- Messy, disorganized filament
- File names: spaghetti_01.jpg, spaghetti_02.jpg

## Image Specifications

- Format: JPEG
- Resolution: 512 x 512 pixels (we will resize if needed)
- Aspect ratio: 1:1 (square)
- The print should be clearly visible against the background
- Good lighting so details are visible
- Angle: Top-down or slight angle view of the print bed

## Where to Get These Images

You can either:
1. Take photos with a phone camera if you have a 3D printer
2. Search for images online of 3D printing failures
3. I can help find public domain images

Place all images in the `sample_images/` folder before running the system.
