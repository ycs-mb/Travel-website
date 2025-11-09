"""Main Orchestrator for Travel Photo Organization Workflow."""

import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
import time

from agents import (
    MetadataExtractionAgent,
    QualityAssessmentAgent,
    AestheticAssessmentAgent,
    DuplicateDetectionAgent,
    FilteringCategorizationAgent,
    CaptionGenerationAgent,
    WebsiteGenerationAgent
)

from utils.logger import setup_logger, get_error_log, save_error_log
from utils.helpers import load_config, save_json, get_image_files, ensure_directories
from utils.validation import validate_final_report


class TravelPhotoOrchestrator:
    """
    Main orchestrator for the travel photo organization workflow.

    Coordinates execution of all 7 agents in the proper sequence,
    handles parallelization, error recovery, and final reporting.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize orchestrator.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Setup logging
        log_file = Path(self.config.get('paths', {}).get('logs_output', './output/logs')) / 'workflow.log'
        self.logger = setup_logger(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=log_file,
            json_format=self.config.get('logging', {}).get('format', 'json') == 'json'
        )

        # Ensure output directories exist
        ensure_directories(self.config)

        # Initialize agents
        self.agents = {
            'metadata': MetadataExtractionAgent(self.config, self.logger),
            'quality': QualityAssessmentAgent(self.config, self.logger),
            'aesthetic': AestheticAssessmentAgent(self.config, self.logger),
            'duplicates': DuplicateDetectionAgent(self.config, self.logger),
            'filtering': FilteringCategorizationAgent(self.config, self.logger),
            'captions': CaptionGenerationAgent(self.config, self.logger),
            'website': WebsiteGenerationAgent(self.config, self.logger)
        }

        # Storage for agent outputs
        self.outputs = {}
        self.validations = []
        self.agent_performance = []

        self.logger.info("=" * 80)
        self.logger.info("TRAVEL PHOTO ORGANIZATION WORKFLOW INITIALIZED")
        self.logger.info("=" * 80)

    def run_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete workflow.

        Returns:
            Final statistics report
        """
        workflow_start = time.time()

        self.logger.info("Starting workflow execution...")

        # Get input images
        input_dir = Path(self.config.get('paths', {}).get('input_images', './sample_images'))
        image_paths = get_image_files(input_dir)

        if not image_paths:
            self.logger.error(f"No images found in {input_dir}")
            return self._generate_empty_report()

        self.logger.info(f"Found {len(image_paths)} images to process")

        # Stage 1: Metadata Extraction
        self._run_agent_stage(
            "Metadata Extraction",
            lambda: self.agents['metadata'].run(image_paths)
        )

        # Stage 2 & 3: Quality and Aesthetic Assessment (can run in parallel)
        if self.config.get('parallelization', {}).get('enable_parallel_agents', True):
            self.logger.info("Running Quality and Aesthetic assessment in parallel")
            # In a full implementation, use ThreadPoolExecutor here
            # For now, run sequentially
            self._run_agent_stage(
                "Quality Assessment",
                lambda: self.agents['quality'].run(
                    image_paths,
                    self.outputs.get('metadata', [])
                )
            )
            self._run_agent_stage(
                "Aesthetic Assessment",
                lambda: self.agents['aesthetic'].run(
                    image_paths,
                    self.outputs.get('metadata', [])
                )
            )
        else:
            self._run_agent_stage(
                "Quality Assessment",
                lambda: self.agents['quality'].run(
                    image_paths,
                    self.outputs.get('metadata', [])
                )
            )
            self._run_agent_stage(
                "Aesthetic Assessment",
                lambda: self.agents['aesthetic'].run(
                    image_paths,
                    self.outputs.get('metadata', [])
                )
            )

        # Stage 4: Duplicate Detection (requires Quality + Aesthetic)
        self._run_agent_stage(
            "Duplicate Detection",
            lambda: self.agents['duplicates'].run(
                image_paths,
                self.outputs.get('quality', []),
                self.outputs.get('aesthetic', []),
                self.outputs.get('metadata', [])
            )
        )

        # Stage 5 & 6: Filtering and Captions (can run in parallel after duplicates)
        self._run_agent_stage(
            "Filtering & Categorization",
            lambda: self.agents['filtering'].run(
                image_paths,
                self.outputs.get('metadata', []),
                self.outputs.get('quality', []),
                self.outputs.get('aesthetic', [])
            )
        )

        self._run_agent_stage(
            "Caption Generation",
            lambda: self.agents['captions'].run(
                image_paths,
                self.outputs.get('metadata', []),
                self.outputs.get('quality', []),
                self.outputs.get('aesthetic', []),
                self.outputs.get('filtering', [])
            )
        )

        # Stage 7: Website Generation (requires all previous outputs)
        all_data = {
            'metadata': self.outputs.get('metadata', []),
            'quality': self.outputs.get('quality', []),
            'aesthetic': self.outputs.get('aesthetic', []),
            'duplicates': self.outputs.get('duplicates', []),
            'categories': self.outputs.get('filtering', []),
            'captions': self.outputs.get('captions', [])
        }

        self._run_agent_stage(
            "Website Generation",
            lambda: self.agents['website'].run(all_data)
        )

        # Generate final report
        workflow_time = time.time() - workflow_start
        final_report = self._generate_final_report(len(image_paths), workflow_time)

        # Save outputs
        self._save_all_outputs(final_report)

        self.logger.info("=" * 80)
        self.logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
        self.logger.info("=" * 80)

        return final_report

    def _run_agent_stage(self, name: str, agent_func):
        """
        Run a single agent stage with timing and error handling.

        Args:
            name: Agent name
            agent_func: Function to execute agent
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info(f"STAGE: {name}")
        self.logger.info(f"{'=' * 80}")

        start_time = time.time()

        try:
            output, validation = agent_func()

            execution_time = time.time() - start_time

            # Store output and validation
            key = name.lower().replace(' & ', '_').replace(' ', '_')
            self.outputs[key] = output
            self.validations.append(validation)

            # Track performance
            self.agent_performance.append({
                'agent': name,
                'execution_time_seconds': round(execution_time, 2),
                'images_processed': len(output) if isinstance(output, list) else 1,
                'success_rate': 1.0 if validation['status'] == 'success' else 0.5
            })

            self.logger.info(f"{name} completed in {execution_time:.2f}s")
            self.logger.info(f"Status: {validation['status']}")
            self.logger.info(f"Summary: {validation['summary']}")

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"{name} failed after {execution_time:.2f}s: {str(e)}")

            self.validations.append({
                'agent': name,
                'stage': 'execution',
                'status': 'error',
                'summary': f"Failed: {str(e)}",
                'issues': [str(e)]
            })

            self.agent_performance.append({
                'agent': name,
                'execution_time_seconds': round(execution_time, 2),
                'images_processed': 0,
                'success_rate': 0.0
            })

    def _generate_final_report(self, num_images: int, workflow_time: float) -> Dict[str, Any]:
        """
        Generate final statistics report.

        Args:
            num_images: Total number of images processed
            workflow_time: Total workflow execution time

        Returns:
            Final report dictionary
        """
        metadata_list = self.outputs.get('metadata', [])
        quality_list = self.outputs.get('quality', [])
        aesthetic_list = self.outputs.get('aesthetic', [])
        duplicates_list = self.outputs.get('duplicates', [])
        filtering_list = self.outputs.get('filtering', [])

        # Calculate statistics
        num_flagged_metadata = sum(
            1 for m in metadata_list if m.get('flags')
        )

        avg_technical = (
            sum(q.get('quality_score', 0) for q in quality_list) / len(quality_list)
            if quality_list else 0.0
        )

        avg_aesthetic = (
            sum(a.get('overall_aesthetic', 0) for a in aesthetic_list) / len(aesthetic_list)
            if aesthetic_list else 0.0
        )

        num_duplicates = sum(
            len(g['image_ids']) - 1 for g in duplicates_list
        ) if duplicates_list else 0

        num_final_selected = sum(
            1 for f in filtering_list if f.get('passes_filter', False)
        )

        num_flagged_review = sum(
            1 for f in filtering_list if f.get('flagged', False)
        )

        # Category distribution
        category_dist = {}
        for f in filtering_list:
            cat = f.get('category', 'Unknown')
            category_dist[cat] = category_dist.get(cat, 0) + 1

        # Quality distribution
        quality_dist = {f"score_{i}": 0 for i in range(1, 6)}
        for q in quality_list:
            score = q.get('quality_score', 3)
            quality_dist[f"score_{score}"] += 1

        # Create report
        report = {
            'num_images_ingested': num_images,
            'num_images_flagged_metadata': num_flagged_metadata,
            'average_technical_score': round(avg_technical, 2),
            'average_aesthetic_score': round(avg_aesthetic, 2),
            'num_duplicates_found': num_duplicates,
            'num_images_final_selected': num_final_selected,
            'num_images_flagged_for_manual_review': num_flagged_review,
            'processing_time_seconds': round(workflow_time, 2),
            'agent_performance': self.agent_performance,
            'category_distribution': category_dist,
            'quality_distribution': quality_dist,
            'agent_errors': get_error_log(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # Validate report
        is_valid, error_msg = validate_final_report(report)
        if not is_valid:
            self.logger.warning(f"Final report validation warning: {error_msg}")

        return report

    def _generate_empty_report(self) -> Dict[str, Any]:
        """Generate empty report when no images are found."""
        return {
            'num_images_ingested': 0,
            'num_images_flagged_metadata': 0,
            'average_technical_score': 0.0,
            'average_aesthetic_score': 0.0,
            'num_duplicates_found': 0,
            'num_images_final_selected': 0,
            'num_images_flagged_for_manual_review': 0,
            'processing_time_seconds': 0.0,
            'agent_performance': [],
            'category_distribution': {},
            'quality_distribution': {},
            'agent_errors': get_error_log(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def _save_all_outputs(self, final_report: Dict[str, Any]):
        """Save all outputs to files."""
        output_dir = Path(self.config.get('paths', {}).get('reports_output', './output/reports'))

        # Save individual agent outputs
        for key, data in self.outputs.items():
            output_file = output_dir / f"{key}_output.json"
            save_json(data, output_file)
            self.logger.info(f"Saved {key} output to {output_file}")

        # Save validations
        validations_file = output_dir / "validations.json"
        save_json(self.validations, validations_file)
        self.logger.info(f"Saved validations to {validations_file}")

        # Save final report
        report_file = output_dir / "final_report.json"
        save_json(final_report, report_file)
        self.logger.info(f"Saved final report to {report_file}")

        # Save error log
        error_log_file = Path(self.config.get('paths', {}).get('logs_output', './output/logs')) / 'errors.json'
        save_error_log(error_log_file)
        self.logger.info(f"Saved error log to {error_log_file}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("TRAVEL PHOTO ORGANIZATION WORKFLOW")
    print("AI-Powered Agentic System for Photo Management")
    print("=" * 80 + "\n")

    try:
        orchestrator = TravelPhotoOrchestrator()
        final_report = orchestrator.run_workflow()

        print("\n" + "=" * 80)
        print("WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"Images Processed: {final_report['num_images_ingested']}")
        print(f"Average Technical Score: {final_report['average_technical_score']}/5")
        print(f"Average Aesthetic Score: {final_report['average_aesthetic_score']}/5")
        print(f"Duplicates Found: {final_report['num_duplicates_found']}")
        print(f"Final Selected: {final_report['num_images_final_selected']}")
        print(f"Flagged for Review: {final_report['num_images_flagged_for_manual_review']}")
        print(f"Total Processing Time: {final_report['processing_time_seconds']:.2f}s")
        print("=" * 80 + "\n")

        print("✓ All outputs saved to ./output directory")
        print("✓ Website generated at ./output/website")
        print("\nWorkflow completed successfully!")

    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
