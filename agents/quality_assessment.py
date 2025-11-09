"""Agent 2: Quality Assessment - Evaluate technical image quality."""

import logging
from pathlib import Path
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from PIL import Image
import cv2

from utils.logger import log_error, log_info
from utils.validation import validate_agent_output, create_validation_summary


class QualityAssessmentAgent:
    """
    Agent 2: Image Quality Analyst

    System Prompt:
    You are an elite image quality analyst with expertise in computational photography.
    Evaluate each photograph using state-of-the-art quality metrics.

    Assess: Sharpness/Focus, Exposure, Noise Level, Resolution, Overall Technical Score.
    Detect: Overexposed, Underexposed, Motion blur, High noise, Low resolution.
    """

    SYSTEM_PROMPT = """
    You are an elite image quality analyst with expertise in computational photography.
    Evaluate each photograph using state-of-the-art quality metrics.

    Assess the following technical dimensions:
    1. Sharpness/Focus Quality (1-5): Measure edge acuity and blur
    2. Exposure (1-5): Evaluate histogram distribution, clipping, dynamic range
    3. Noise Level (1-5): Detect ISO noise, compression artifacts
    4. Resolution Adequacy (1-5): Assess if resolution meets modern standards
    5. Overall Technical Score (1-5): Weighted composite of above metrics

    Detection criteria:
    - Overexposed: >5% pixels at 255 in any channel
    - Underexposed: >10% pixels at 0
    - Motion blur: Edge analysis variance below threshold
    - High noise: Grain/artifact detection in smooth areas
    - Low resolution: <2MP or <1920px on long edge

    Provide structured output with scores and detected issues.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Quality Assessment Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('quality_assessment', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        self.thresholds = config.get('thresholds', {})

    def assess_sharpness(self, image: np.ndarray) -> tuple[int, float]:
        """
        Assess image sharpness using Laplacian variance.

        Args:
            image: Image as numpy array

        Returns:
            Tuple of (score 1-5, variance value)
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()

            # Score based on variance thresholds
            if variance > 500:
                score = 5
            elif variance > 300:
                score = 4
            elif variance > 150:
                score = 3
            elif variance > 75:
                score = 2
            else:
                score = 1

            return score, variance

        except Exception as e:
            self.logger.warning(f"Error assessing sharpness: {e}")
            return 3, 0.0

    def assess_exposure(self, image: np.ndarray) -> tuple[int, float, List[str]]:
        """
        Assess image exposure using histogram analysis.

        Args:
            image: Image as numpy array

        Returns:
            Tuple of (score 1-5, clipping percentage, issues list)
        """
        issues = []

        try:
            # Calculate histogram for each channel
            if len(image.shape) == 3:
                channels = cv2.split(image)
            else:
                channels = [image]

            total_pixels = image.shape[0] * image.shape[1]
            clipped_high = 0
            clipped_low = 0

            for channel in channels:
                # Count overexposed pixels (at 255)
                clipped_high += np.sum(channel >= 255)
                # Count underexposed pixels (at 0)
                clipped_low += np.sum(channel <= 0)

            # Calculate percentages
            high_percent = (clipped_high / (total_pixels * len(channels))) * 100
            low_percent = (clipped_low / (total_pixels * len(channels))) * 100

            # Check for exposure issues
            if high_percent > 5:
                issues.append("overexposed")
            if low_percent > 10:
                issues.append("underexposed")

            # Score based on clipping
            total_clipping = high_percent + low_percent

            if total_clipping < 1:
                score = 5
            elif total_clipping < 3:
                score = 4
            elif total_clipping < 8:
                score = 3
            elif total_clipping < 15:
                score = 2
            else:
                score = 1

            return score, total_clipping, issues

        except Exception as e:
            self.logger.warning(f"Error assessing exposure: {e}")
            return 3, 0.0, []

    def assess_noise(self, image: np.ndarray) -> tuple[int, float]:
        """
        Assess image noise using standard deviation in smooth areas.

        Args:
            image: Image as numpy array

        Returns:
            Tuple of (score 1-5, noise estimate)
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            # Estimate noise using median filtering
            median = cv2.medianBlur(gray, 5)
            noise = np.std(gray.astype(float) - median.astype(float))

            # Score based on noise level
            if noise < 5:
                score = 5
            elif noise < 10:
                score = 4
            elif noise < 15:
                score = 3
            elif noise < 25:
                score = 2
            else:
                score = 1

            return score, noise

        except Exception as e:
            self.logger.warning(f"Error assessing noise: {e}")
            return 3, 0.0

    def assess_resolution(self, width: int, height: int) -> tuple[int, List[str]]:
        """
        Assess image resolution adequacy.

        Args:
            width: Image width
            height: Image height

        Returns:
            Tuple of (score 1-5, issues list)
        """
        issues = []
        total_pixels = width * height
        min_pixels = self.thresholds.get('min_resolution_pixels', 2000000)

        if total_pixels < min_pixels:
            issues.append("low_resolution")

        # Score based on resolution
        if total_pixels >= 24000000:  # 24MP+
            score = 5
        elif total_pixels >= 12000000:  # 12MP+
            score = 4
        elif total_pixels >= 8000000:  # 8MP+
            score = 3
        elif total_pixels >= min_pixels:  # 2MP+
            score = 2
        else:
            score = 1

        return score, issues

    def process_image(self, image_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess quality of a single image.

        Args:
            image_path: Path to image file
            metadata: Image metadata from Agent 1

        Returns:
            Quality assessment dictionary
        """
        issues = []

        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Get dimensions
            height, width = image.shape[:2]

            # Assess different quality aspects
            sharpness_score, blur_variance = self.assess_sharpness(image)
            exposure_score, clipping_percent, exposure_issues = self.assess_exposure(image)
            noise_score, snr = self.assess_noise(image)
            resolution_score, resolution_issues = self.assess_resolution(width, height)

            # Combine issues
            issues.extend(exposure_issues)
            issues.extend(resolution_issues)

            if sharpness_score <= 2:
                issues.append("motion_blur")
            if noise_score <= 2:
                issues.append("high_noise")

            # Calculate overall quality score (weighted average)
            quality_score = int(round(
                (sharpness_score * 0.35 +
                 exposure_score * 0.30 +
                 noise_score * 0.20 +
                 resolution_score * 0.15)
            ))

            # Create assessment object
            assessment = {
                "image_id": metadata['image_id'],
                "quality_score": quality_score,
                "sharpness": sharpness_score,
                "exposure": exposure_score,
                "noise": noise_score,
                "resolution": resolution_score,
                "issues": issues,
                "metrics": {
                    "blur_variance": float(blur_variance),
                    "histogram_clipping_percent": float(clipping_percent),
                    "snr_db": float(snr)
                }
            }

            # Validate output
            is_valid, error_msg = validate_agent_output("quality_assessment", assessment)
            if not is_valid:
                log_error(
                    self.logger,
                    "Technical Assessment",
                    "ValidationError",
                    f"Validation failed for {image_path.name}: {error_msg}",
                    "error"
                )

            return assessment

        except Exception as e:
            log_error(
                self.logger,
                "Technical Assessment",
                "ProcessingError",
                f"Failed to assess {image_path.name}: {str(e)}",
                "error"
            )
            return {
                "image_id": metadata.get('image_id', image_path.stem),
                "quality_score": 3,
                "sharpness": 3,
                "exposure": 3,
                "noise": 3,
                "resolution": 3,
                "issues": ["processing_error"],
                "metrics": {
                    "blur_variance": 0.0,
                    "histogram_clipping_percent": 0.0,
                    "snr_db": 0.0
                }
            }

    def run(self, image_paths: List[Path], metadata_list: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run quality assessment on all images.

        Args:
            image_paths: List of image file paths
            metadata_list: List of metadata from Agent 1

        Returns:
            Tuple of (assessment_list, validation_summary)
        """
        log_info(self.logger, f"Starting quality assessment for {len(image_paths)} images", "Technical Assessment")

        # Create lookup for metadata
        metadata_map = {m['image_id']: m for m in metadata_list}

        assessment_list = []
        issues = []

        # Process images in parallel
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for path in image_paths:
                image_id = path.stem
                metadata = metadata_map.get(image_id, {'image_id': image_id})
                futures.append(executor.submit(self.process_image, path, metadata))

            for future in as_completed(futures):
                try:
                    assessment = future.result()
                    assessment_list.append(assessment)

                    if assessment.get('issues'):
                        issues.append(f"{assessment['image_id']}: {', '.join(assessment['issues'])}")

                except Exception as e:
                    error_msg = f"Failed to assess image: {str(e)}"
                    issues.append(error_msg)
                    log_error(
                        self.logger,
                        "Technical Assessment",
                        "ExecutionError",
                        error_msg,
                        "error"
                    )

        # Calculate statistics
        if assessment_list:
            avg_quality = sum(a['quality_score'] for a in assessment_list) / len(assessment_list)
            summary = f"Assessed {len(assessment_list)} images, average quality: {avg_quality:.2f}/5"
        else:
            summary = "No images were successfully assessed"

        # Create validation summary
        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")

        validation = create_validation_summary(
            agent="Technical Assessment",
            stage="scoring",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        log_info(self.logger, f"Quality assessment completed: {summary}", "Technical Assessment")

        return assessment_list, validation
