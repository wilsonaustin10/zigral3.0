"""Screen parsing service for visual element detection."""

import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Optional
from pydantic import BaseModel
import torch
from transformers import AutoImageProcessor, AutoModelForObjectDetection
from dataclasses import dataclass
import logging
import io

logger = logging.getLogger(__name__)

@dataclass
class ElementLocation:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    element_type: str

class ScreenParser:
    def __init__(self):
        """Initialize the screen parser with pre-trained models."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load models
        self.processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection")
        self.model = AutoModelForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
        self.model.to(self.device)
        
        # Define element types we can detect
        self.element_types = [
            "button", "input", "link", "text", "image", "checkbox", "radio",
            "dropdown", "table", "list", "heading"
        ]

    async def find_element(self, screenshot: bytes, description: str) -> Optional[ElementLocation]:
        """Find a specific element in the screenshot based on description."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot))
            
            # Process image
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            outputs = self.model(**inputs)
            
            # Convert outputs to normalized coordinates
            results = self.processor.post_process_object_detection(
                outputs,
                threshold=0.5,
                target_sizes=[(image.height, image.width)]
            )[0]
            
            # Find best matching element
            best_match = None
            highest_confidence = 0
            
            for box, score, label in zip(results["boxes"], results["scores"], results["labels"]):
                element_type = self.element_types[label]
                confidence = float(score)
                
                # Simple matching logic - can be enhanced with better NLP
                if description.lower() in element_type.lower() and confidence > highest_confidence:
                    x1, y1, x2, y2 = box.tolist()
                    best_match = ElementLocation(
                        x=int(x1),
                        y=int(y1),
                        width=int(x2 - x1),
                        height=int(y2 - y1),
                        confidence=confidence,
                        element_type=element_type
                    )
                    highest_confidence = confidence
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding element: {str(e)}")
            return None

    async def get_all_elements(self, screenshot: bytes) -> List[ElementLocation]:
        """Get all detectable elements from the screenshot."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot))
            
            # Process image
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            outputs = self.model(**inputs)
            
            # Convert outputs to normalized coordinates
            results = self.processor.post_process_object_detection(
                outputs,
                threshold=0.5,
                target_sizes=[(image.height, image.width)]
            )[0]
            
            # Convert results to ElementLocation objects
            elements = []
            for box, score, label in zip(results["boxes"], results["scores"], results["labels"]):
                x1, y1, x2, y2 = box.tolist()
                elements.append(ElementLocation(
                    x=int(x1),
                    y=int(y1),
                    width=int(x2 - x1),
                    height=int(y2 - y1),
                    confidence=float(score),
                    element_type=self.element_types[label]
                ))
            
            return elements
            
        except Exception as e:
            logger.error(f"Error getting all elements: {str(e)}")
            return []

    async def analyze_layout(self, screenshot: bytes) -> Dict[str, List[ElementLocation]]:
        """Analyze the layout and group elements by type."""
        elements = await self.get_all_elements(screenshot)
        layout = {}
        
        for element in elements:
            if element.element_type not in layout:
                layout[element.element_type] = []
            layout[element.element_type].append(element)
            
        return layout 