import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import os
from PIL import Image
import torch


class ComputerVisionModule:
    def __init__(self, stable_diffusion_model_id: str = "runwayml/stable-diffusion-v1-5"):
        # Configure CUDA settings for GTX 1650
        if torch.cuda.is_available():
            torch.backends.cuda.matmul.allow_tf32 = True  # Enable TF32 for better performance
            torch.backends.cudnn.benchmark = True  # Enable cudnn autotuner
            print(f"CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"VRAM Available: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.2f} GB")

        # Initialize YOLOv8 with GPU support
        try:
            self.yolo_model = YOLO('yolov8n.pt')  # Nano model for efficiency
            self.yolo_model.to('cuda')  # Move to GPU
            print("YOLO initialized on GPU")
        except Exception as e:
            print(f"Error initializing YOLO: {e}")
            self.yolo_model = None

        # Initialize MediaPipe Face Detection
        try:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5
            )
            print("MediaPipe Face Detection initialized")
        except Exception as e:
            print(f"Error initializing MediaPipe: {e}")
            self.face_detection = None

        # Initialize Stable Diffusion with optimizations for GTX 1650
        self.stable_diffusion = None
        try:
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
            from diffusers import StableDiffusionPipeline

            print("Initializing Stable Diffusion with CUDA optimizations...")
            self.stable_diffusion = StableDiffusionPipeline.from_pretrained(
                stable_diffusion_model_id,
                torch_dtype=torch.float16,  # Use half precision
                use_safetensors=True,
                variant="fp16",
                low_memory=True  # Enable low memory optimizations
            ).to("cuda")

            # Enable memory efficient attention
            self.stable_diffusion.enable_attention_slicing(slice_size="auto")
            self.stable_diffusion.enable_vae_slicing()  # Enable VAE slicing
            print("Stable Diffusion initialized on GPU")

        except Exception as e:
            print(f"Error initializing Stable Diffusion: {e}")
            print("Image generation will be unavailable.")

    def detect_objects(self, frame: np.ndarray) -> tuple:
        """
        Detect objects in a frame using YOLOv8.
        Returns: processed frame and list of detections
        """
        if self.yolo_model is None:
            return frame, []

        try:
            # Convert frame to CUDA tensor
            if torch.cuda.is_available():
                frame = torch.from_numpy(frame).cuda()

            results = self.yolo_model(frame)
            annotated_frame = results[0].plot()

            detections = []
            for r in results[0].boxes.data:
                x1, y1, x2, y2, score, class_id = r
                class_name = self.yolo_model.names[int(class_id)]
                detections.append({
                    'class': class_name,
                    'confidence': float(score),
                    'bbox': [float(x1), float(y1), float(x2), float(y2)]
                })

            return annotated_frame, detections
        except Exception as e:
            print(f"Error in object detection: {e}")
            return frame, []

    def detect_faces(self, frame: np.ndarray) -> tuple:
        """
        Detect faces in a frame using MediaPipe.
        Returns: processed frame and list of face detections
        """
        if self.face_detection is None:
            return frame, []

        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(frame_rgb)

            annotated_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            face_detections = []
            if results.detections:
                for detection in results.detections:
                    self.mp_drawing.draw_detection(annotated_frame, detection)

                    bbox = detection.location_data.relative_bounding_box
                    face_detections.append({
                        'confidence': detection.score[0],
                        'bbox': [bbox.xmin, bbox.ymin, bbox.width, bbox.height]
                    })

            return annotated_frame, face_detections
        except Exception as e:
            print(f"Error in face detection: {e}")
            return frame, []

    def generate_image(self, prompt: str, negative_prompt: str = None) -> Image.Image:
        """
        Generate an image using Stable Diffusion based on the text prompt.
        Returns: PIL Image
        """
        if self.stable_diffusion is None:
            raise Exception("Stable Diffusion is not initialized")

        try:
            generation_kwargs = {
                "prompt": prompt,
                "num_inference_steps": 25,  # Reduced for faster generation
                "guidance_scale": 7.5,
                "height": 512,  # Set fixed dimensions for better memory usage
                "width": 512
            }
            if negative_prompt:
                generation_kwargs["negative_prompt"] = negative_prompt

            # Clear CUDA cache before generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            with torch.inference_mode():
                image = self.stable_diffusion(**generation_kwargs).images[0]

            # Clear CUDA cache after generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return image
        except Exception as e:
            print(f"Error generating image: {e}")
            raise

    def start_camera(self):
        """
        Start the camera and perform real-time object and face detection.
        """
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception("Could not open camera")

            print("Camera started. Press 'q' to quit.")

            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Failed to read from camera")
                    break

                # Perform both object and face detection
                frame_with_objects, objects = self.detect_objects(frame)
                frame_with_all, faces = self.detect_faces(frame_with_objects)

                # Display results
                cv2.imshow('Jarvis Vision', frame_with_all)

                # Break loop with 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Error in camera operation: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            # Clear CUDA cache when done
            if torch.cuda.is_available():
                torch.cuda.empty_cache()