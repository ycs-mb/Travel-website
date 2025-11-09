"""Agent 4: Duplicate Detection - Find and group similar/duplicate images."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
from collections import defaultdict
import imagehash
from PIL import Image

from utils.logger import log_error, log_info
from utils.validation import create_validation_summary


class DuplicateDetectionAgent:
    """
    Agent 4: Visual Comparator

    System Prompt:
    You are an expert in visual similarity analysis using cutting-edge computer
    vision algorithms.

    Detect duplicates and visually similar images using:
    - Perceptual hashing (pHash, dHash, aHash)
    - Feature embedding similarity (CLIP, ResNet)
    - SSIM (Structural Similarity Index)

    For each similarity group, select the best image using combined scoring.
    """

    SYSTEM_PROMPT = """
    You are an expert in visual similarity analysis using cutting-edge computer
    vision algorithms.

    Detect duplicates and visually similar images using:
    1. Perceptual hashing (pHash, dHash, aHash)
    2. Feature embedding similarity (CLIP, ResNet, VGG)
    3. SSIM (Structural Similarity Index)

    Thresholds:
    - Duplicate: Hamming distance ≤ 5 OR embedding cosine similarity ≥ 0.98
    - Near-duplicate: Hamming distance ≤ 10 OR embedding cosine similarity ≥ 0.95
    - Similar: Hamming distance ≤ 15 OR embedding cosine similarity ≥ 0.90

    For each similarity group:
    1. Select the best image using: technical_score * 0.4 + aesthetic_score * 0.6
    2. If tied, prefer higher resolution
    3. Mark others for removal/deduplication

    Handle edge cases: burst shots, bracketed exposures, panorama sequences.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Duplicate Detection Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('duplicate_detection', {})
        self.hash_threshold = self.agent_config.get('hash_threshold', 10)
        self.embedding_threshold = self.agent_config.get('embedding_threshold', 0.90)

    def compute_hash(self, image_path: Path) -> Tuple[str, str, str]:
        """
        Compute multiple perceptual hashes for an image.

        Args:
            image_path: Path to image

        Returns:
            Tuple of (phash, dhash, ahash) as hex strings
        """
        try:
            with Image.open(image_path) as img:
                # Resize for faster processing
                img.thumbnail((512, 512))

                # Compute multiple hash types
                phash = str(imagehash.phash(img))
                dhash = str(imagehash.dhash(img))
                ahash = str(imagehash.average_hash(img))

                return phash, dhash, ahash

        except Exception as e:
            log_error(
                self.logger,
                "Duplicate Detection",
                "HashError",
                f"Failed to compute hash for {image_path.name}: {str(e)}",
                "warning"
            )
            return "", "", ""

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hex hash strings.

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            Hamming distance
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 999  # Invalid comparison

        distance = 0
        for c1, c2 in zip(hash1, hash2):
            # XOR and count bits
            xor = int(c1, 16) ^ int(c2, 16)
            distance += bin(xor).count('1')

        return distance

    def find_similar_groups(
        self,
        image_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group similar images based on perceptual hashing.

        Args:
            image_data: List of image data with hashes and scores

        Returns:
            List of similarity groups
        """
        # Track which images have been grouped
        grouped = set()
        similarity_groups = []
        group_counter = 0

        for i, img1 in enumerate(image_data):
            if img1['image_id'] in grouped:
                continue

            # Start a new group
            group = {
                'group_id': f"group_{group_counter}",
                'image_ids': [img1['image_id']],
                'similarity_type': 'duplicate',
                'similarity_metric': 0.0
            }

            # Find similar images
            for j, img2 in enumerate(image_data[i + 1:], start=i + 1):
                if img2['image_id'] in grouped:
                    continue

                # Calculate hash distances
                phash_dist = self.hamming_distance(img1['phash'], img2['phash'])
                dhash_dist = self.hamming_distance(img1['dhash'], img2['dhash'])
                ahash_dist = self.hamming_distance(img1['ahash'], img2['ahash'])

                # Use minimum distance
                min_distance = min(phash_dist, dhash_dist, ahash_dist)

                # Classify similarity
                if min_distance <= 5:
                    similarity_type = 'duplicate'
                elif min_distance <= self.hash_threshold:
                    similarity_type = 'near-duplicate'
                elif min_distance <= 15:
                    similarity_type = 'similar'
                else:
                    continue

                # Add to group
                group['image_ids'].append(img2['image_id'])
                group['similarity_type'] = similarity_type
                group['similarity_metric'] = float(min_distance)
                grouped.add(img2['image_id'])

            # Only save groups with multiple images
            if len(group['image_ids']) > 1:
                # Select best image in group
                best_image = self.select_best_image(group['image_ids'], image_data)
                group['selected_best'] = best_image
                similarity_groups.append(group)
                grouped.add(img1['image_id'])
                group_counter += 1

        return similarity_groups

    def select_best_image(
        self,
        image_ids: List[str],
        image_data: List[Dict[str, Any]]
    ) -> str:
        """
        Select the best image from a similarity group.

        Args:
            image_ids: List of image IDs in group
            image_data: Full image data list

        Returns:
            ID of best image
        """
        # Create lookup
        data_map = {img['image_id']: img for img in image_data}

        # Calculate combined scores
        scored_images = []
        for img_id in image_ids:
            if img_id not in data_map:
                continue

            img = data_map[img_id]
            technical = img.get('technical_score', 3)
            aesthetic = img.get('aesthetic_score', 3)
            resolution = img.get('resolution', 0)

            # Combined score: 40% technical, 60% aesthetic
            combined_score = (technical * 0.4 + aesthetic * 0.6)

            scored_images.append({
                'image_id': img_id,
                'score': combined_score,
                'resolution': resolution
            })

        # Sort by score (descending), then resolution (descending)
        scored_images.sort(key=lambda x: (x['score'], x['resolution']), reverse=True)

        return scored_images[0]['image_id'] if scored_images else image_ids[0]

    def run(
        self,
        image_paths: List[Path],
        quality_assessments: List[Dict[str, Any]],
        aesthetic_assessments: List[Dict[str, Any]],
        metadata_list: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run duplicate detection on all images.

        Args:
            image_paths: List of image file paths
            quality_assessments: Quality scores from Agent 2
            aesthetic_assessments: Aesthetic scores from Agent 3
            metadata_list: Metadata from Agent 1

        Returns:
            Tuple of (similarity_groups, validation_summary)
        """
        log_info(self.logger, f"Starting duplicate detection for {len(image_paths)} images", "Duplicate Detection")

        # Create lookups
        quality_map = {q['image_id']: q for q in quality_assessments}
        aesthetic_map = {a['image_id']: a for a in aesthetic_assessments}
        metadata_map = {m['image_id']: m for m in metadata_list}

        # Compute hashes and prepare data
        image_data = []
        issues = []

        for path in image_paths:
            image_id = path.stem

            try:
                # Compute hashes
                phash, dhash, ahash = self.compute_hash(path)

                # Get scores
                quality = quality_map.get(image_id, {})
                aesthetic = aesthetic_map.get(image_id, {})
                metadata = metadata_map.get(image_id, {})

                dimensions = metadata.get('dimensions', {})
                resolution = dimensions.get('width', 0) * dimensions.get('height', 0)

                image_data.append({
                    'image_id': image_id,
                    'path': path,
                    'phash': phash,
                    'dhash': dhash,
                    'ahash': ahash,
                    'technical_score': quality.get('quality_score', 3),
                    'aesthetic_score': aesthetic.get('overall_aesthetic', 3),
                    'resolution': resolution
                })

            except Exception as e:
                error_msg = f"Failed to process {path.name}: {str(e)}"
                issues.append(error_msg)
                log_error(
                    self.logger,
                    "Duplicate Detection",
                    "ProcessingError",
                    error_msg,
                    "error"
                )

        # Find similarity groups
        similarity_groups = self.find_similar_groups(image_data)

        # Calculate statistics
        num_duplicates = sum(len(g['image_ids']) - 1 for g in similarity_groups)
        summary = f"Found {len(similarity_groups)} similarity groups with {num_duplicates} duplicates"

        # Create validation summary
        status = "success" if not issues else "warning"

        validation = create_validation_summary(
            agent="Duplicate Detection",
            stage="grouping",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        log_info(self.logger, f"Duplicate detection completed: {summary}", "Duplicate Detection")

        return similarity_groups, validation
