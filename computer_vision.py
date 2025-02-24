import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import os
from PIL import Image
import torch
from typing import Optional, Tuple, List, Dict, Union


class ComputerVisionModule:
    def __init__(self, stable_diffusion_model_id: str = "runwayml/stable-diffusion-v1-5"):
        """Initialize the Computer Vision Module with enhanced error handling."""
        self.vram_available = 0.0
        self._init_cuda()
        self._init_yolo()
        self._init_mediapipe()
        self._init_stable_diffusion(stable_diffusion_model_id)

    def _init_cuda(self) -> None:
        """Initialize CUDA settings with proper error checking."""
        try:
            if not torch.cuda.is_available():
                print("CUDA is not available. Some features will be disabled.")
                return

            # Configure CUDA settings
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.benchmark = True

            # Get device information
            device_name = torch.cuda.get_device_name(0)
            self.vram_available = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3

            print(f"CUDA initialized successfully:")
            print(f"- Device: {device_name}")
            print(f"- VRAM Available: {self.vram_available:.2f} GB")

        except Exception as e:
            print(f"Error initializing CUDA: {str(e)}")
            print("Some GPU-accelerated features may be unavailable.")

    def _init_yolo(self) -> None:
        """Initialize YOLO with enhanced error handling."""
        self.yolo_model = None
        try:
            if not torch.cuda.is_available():
                print("CUDA not available. YOLO will run on CPU.")
                self.yolo_model = YOLO('yolov8n.pt')
                return

            # Initialize YOLO with GPU support
            self.yolo_model = YOLO('yolov8n.pt')
            self.yolo_model.to('cuda')
            print("YOLO initialized successfully on GPU")

        except Exception as e:
            print(f"Error initializing YOLO: {str(e)}")
            print("Object detection will be unavailable.")

    def _init_mediapipe(self) -> None:
        """Initialize MediaPipe with enhanced error handling."""
        try:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5
            )
            print("MediaPipe Face Detection initialized successfully")

        except Exception as e:
            print(f"Error initializing MediaPipe: {str(e)}")
            self.face_detection = None
            print("Face detection will be unavailable.")

    def _init_stable_diffusion(self, model_id: str) -> None:
        """Initialize Stable Diffusion with enhanced error handling and memory checks."""
        self.stable_diffusion = None

        try:
            # Check VRAM requirements
            if self.vram_available < 4.0:
                print(f"Warning: Available VRAM ({self.vram_available:.2f} GB) is less than recommended 4GB")
                print("Image generation may be unstable or fail")

            from diffusers import StableDiffusionPipeline
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

            print("Initializing Stable Diffusion with optimizations...")
            self.stable_diffusion = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16",
                low_memory=True
            )

            if torch.cuda.is_available():
                self.stable_diffusion = self.stable_diffusion.to("cuda")
                self.stable_diffusion.enable_attention_slicing(slice_size="auto")
                self.stable_diffusion.enable_vae_slicing()
                print("Stable Diffusion initialized successfully on GPU")
            else:
                print("Warning: Stable Diffusion running on CPU")

        except ImportError as e:
            print("Error: Required packages not installed.")
            print("Please install with: pip install diffusers transformers")
            print(f"Specific error: {str(e)}")
        except Exception as e:
            print(f"Error initializing Stable Diffusion: {str(e)}")
            print("Image generation will be unavailable.")

    def generate_image(self, prompt: str, negative_prompt: str = None) -> Image.Image:
        """Generate an image with enhanced error handling and memory management."""
        if self.stable_diffusion is None:
            raise Exception("Stable Diffusion is not initialized")

        try:
            print(f"Generating image with prompt: {prompt}")

            # Memory management
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

                # Check available memory
                available_memory = torch.cuda.mem_get_info()[0] / 1024 ** 3
                if available_memory < 2.0:  # If less than 2GB available
                    print(f"Warning: Low VRAM available ({available_memory:.2f} GB)")

            # Generation parameters
            generation_kwargs = {
                "prompt": prompt,
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
                "height": 384,
                "width": 384
            }
            if negative_prompt:
                generation_kwargs["negative_prompt"] = negative_prompt

            # Generate image with proper error handling
            with torch.inference_mode(), torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                print("Starting image generation...")
                result = self.stable_diffusion(**generation_kwargs)

                if not result.images:
                    raise Exception("No image was generated")

                image = result.images[0]
                if not isinstance(image, Image.Image):
                    raise TypeError("Generated result is not a PIL Image")

                print("Image generation completed successfully")
                return image

        except RuntimeError as e:
            if "out of memory" in str(e):
                torch.cuda.empty_cache()
                print("CUDA out of memory. Attempting recovery...")
                raise Exception("Insufficient GPU memory. Try reducing image size.")
            raise
        except Exception as e:
            print(f"Error in image generation: {str(e)}")
            raise

    def detect_objects(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Union[str, float, List[float]]]]]:
        """Detect objects with enhanced error handling."""
        if self.yolo_model is None:
            return frame, []

        try:
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
            print(f"Error in object detection: {str(e)}")
            return frame, []

    def detect_faces(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Union[float, List[float]]]]]:
        """Detect faces with enhanced error handling."""
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
            print(f"Error in face detection: {str(e)}")
            return frame, []

    def start_camera(self) -> None:
        """Start camera with enhanced error handling."""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception(
                    "Could not open camera. Please check if camera is connected and not in use by another application.")

            print("Camera started. Press 'q' to quit.")

            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Failed to read from camera")
                    break

                # Reduce processing load
                frame = cv2.resize(frame, (640, 480))

                frame_with_objects, objects = self.detect_objects(frame)
                frame_with_all, faces = self.detect_faces(frame_with_objects)

                cv2.imshow('Grim Vision', frame_with_all)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Error in camera operation: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()