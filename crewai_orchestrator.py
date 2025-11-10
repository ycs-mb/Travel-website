"""CrewAI Orchestrator for Travel Photo Organization Workflow."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
import time
import yaml

from crewai import Agent, Task, Crew, Process

# Import custom tools
from travel_photo_tools import (
    MetadataExtractionTool,
    QualityAssessmentTool,
    AestheticAssessmentTool,
    FilteringCategorizationTool,
    CaptionGenerationTool
)

from utils.helpers import load_config, save_json, get_image_files, ensure_directories
from utils.logger import setup_logger


class CrewAITravelPhotoOrchestrator:
    """
    CrewAI-based orchestrator for travel photo organization workflow.

    Coordinates 5 agents using CrewAI framework with custom tools for
    metadata extraction, quality assessment, aesthetic evaluation,
    filtering/categorization, and caption generation.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize CrewAI orchestrator.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_output = Path(self.config.get('paths', {}).get('output_dir', './output'))
        self.timestamped_output = base_output / timestamp

        # Update config with timestamped paths
        self.config['paths']['output_dir'] = str(self.timestamped_output)
        self.config['paths']['reports_output'] = str(self.timestamped_output / 'reports')
        self.config['paths']['logs_output'] = str(self.timestamped_output / 'logs')
        self.config['paths']['metadata_output'] = str(self.timestamped_output / 'metadata')

        # Setup logging
        log_file = Path(self.config.get('paths', {}).get('logs_output', './output/logs')) / 'workflow.log'
        self.logger = setup_logger(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=log_file,
            json_format=self.config.get('logging', {}).get('format', 'json') == 'json'
        )

        # Ensure output directories exist
        ensure_directories(self.config)

        # Get input images
        input_dir = Path(self.config.get('paths', {}).get('input_images', './sample_images'))
        self.image_paths = get_image_files(input_dir)
        self.image_path_strings = [str(p) for p in self.image_paths]

        # Load CrewAI configurations
        self.agents_config = self._load_yaml_config('crewai_config_agents.yaml')
        self.tasks_config = self._load_yaml_config('crewai_config_tasks.yaml')

        # Initialize tools
        self.tools = {
            'metadata': MetadataExtractionTool(),
            'quality': QualityAssessmentTool(),
            'aesthetic': AestheticAssessmentTool(),
            'filtering': FilteringCategorizationTool(),
            'captions': CaptionGenerationTool()
        }

        # Create agents and tasks
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()

        # Create crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            process=Process.sequential,  # Sequential process for dependency management
            verbose=True
        )

        self.logger.info("=" * 80)
        self.logger.info("CREWAI TRAVEL PHOTO ORGANIZATION WORKFLOW INITIALIZED")
        self.logger.info(f"Output directory: {self.timestamped_output}")
        self.logger.info(f"Found {len(self.image_paths)} images to process")
        self.logger.info("=" * 80)

    def _load_yaml_config(self, config_file: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def _create_agents(self) -> Dict[str, Agent]:
        """Create CrewAI agents from configuration."""
        agents = {}

        # Configure LLM for agents (use OpenAI or Gemini)
        llm_config = None
        if os.getenv('OPENAI_API_KEY'):
            llm_config = "gpt-4"  # or "gpt-4-turbo-preview"
        elif os.getenv('GOOGLE_API_KEY'):
            llm_config = "gemini-pro"

        # Metadata Expert
        agents['metadata'] = Agent(
            role=self.agents_config['metadata_expert']['role'],
            goal=self.agents_config['metadata_expert']['goal'],
            backstory=self.agents_config['metadata_expert']['backstory'],
            tools=[self.tools['metadata']],
            verbose=self.agents_config['metadata_expert'].get('verbose', True),
            allow_delegation=self.agents_config['metadata_expert'].get('allow_delegation', False),
            llm=llm_config
        )

        # Quality Analyst
        agents['quality'] = Agent(
            role=self.agents_config['quality_analyst']['role'],
            goal=self.agents_config['quality_analyst']['goal'],
            backstory=self.agents_config['quality_analyst']['backstory'],
            tools=[self.tools['quality']],
            verbose=self.agents_config['quality_analyst'].get('verbose', True),
            allow_delegation=self.agents_config['quality_analyst'].get('allow_delegation', False),
            llm=llm_config
        )

        # Aesthetic Critic
        agents['aesthetic'] = Agent(
            role=self.agents_config['aesthetic_critic']['role'],
            goal=self.agents_config['aesthetic_critic']['goal'],
            backstory=self.agents_config['aesthetic_critic']['backstory'],
            tools=[self.tools['aesthetic']],
            verbose=self.agents_config['aesthetic_critic'].get('verbose', True),
            allow_delegation=self.agents_config['aesthetic_critic'].get('allow_delegation', False),
            llm=llm_config
        )

        # Content Curator
        agents['curator'] = Agent(
            role=self.agents_config['content_curator']['role'],
            goal=self.agents_config['content_curator']['goal'],
            backstory=self.agents_config['content_curator']['backstory'],
            tools=[self.tools['filtering']],
            verbose=self.agents_config['content_curator'].get('verbose', True),
            allow_delegation=self.agents_config['content_curator'].get('allow_delegation', False),
            llm=llm_config
        )

        # Caption Writer
        agents['captions'] = Agent(
            role=self.agents_config['caption_writer']['role'],
            goal=self.agents_config['caption_writer']['goal'],
            backstory=self.agents_config['caption_writer']['backstory'],
            tools=[self.tools['captions']],
            verbose=self.agents_config['caption_writer'].get('verbose', True),
            allow_delegation=self.agents_config['caption_writer'].get('allow_delegation', False),
            llm=llm_config
        )

        return agents

    def _create_tasks(self) -> Dict[str, Task]:
        """Create CrewAI tasks from configuration."""
        tasks = {}

        # Metadata Extraction Task
        tasks['metadata'] = Task(
            description=self.tasks_config['extract_metadata']['description'].format(
                image_paths=self.image_path_strings,
                config=self.config
            ),
            expected_output=self.tasks_config['extract_metadata']['expected_output'],
            agent=self.agents['metadata']
        )

        # Quality Assessment Task
        tasks['quality'] = Task(
            description=self.tasks_config['assess_quality']['description'],
            expected_output=self.tasks_config['assess_quality']['expected_output'],
            agent=self.agents['quality'],
            context=[tasks['metadata']]
        )

        # Aesthetic Assessment Task
        tasks['aesthetic'] = Task(
            description=self.tasks_config['assess_aesthetics']['description'],
            expected_output=self.tasks_config['assess_aesthetics']['expected_output'],
            agent=self.agents['aesthetic'],
            context=[tasks['metadata']]
        )

        # Filtering and Categorization Task
        tasks['filtering'] = Task(
            description=self.tasks_config['filter_and_categorize']['description'],
            expected_output=self.tasks_config['filter_and_categorize']['expected_output'],
            agent=self.agents['curator'],
            context=[tasks['metadata'], tasks['quality'], tasks['aesthetic']]
        )

        # Caption Generation Task
        tasks['captions'] = Task(
            description=self.tasks_config['generate_captions']['description'],
            expected_output=self.tasks_config['generate_captions']['expected_output'],
            agent=self.agents['captions'],
            context=[tasks['metadata'], tasks['quality'], tasks['aesthetic'], tasks['filtering']]
        )

        return tasks

    def run_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete CrewAI workflow.

        Returns:
            Final statistics report
        """
        workflow_start = time.time()

        self.logger.info("Starting CrewAI workflow execution...")

        if not self.image_paths:
            self.logger.error("No images found to process")
            return self._generate_empty_report()

        try:
            # Kick off the crew
            result = self.crew.kickoff(inputs={
                'image_paths': self.image_path_strings,
                'config': self.config
            })

            # Generate final report
            workflow_time = time.time() - workflow_start
            final_report = self._generate_final_report(len(self.image_paths), workflow_time, result)

            # Save outputs
            self._save_all_outputs(final_report, result)

            self.logger.info("=" * 80)
            self.logger.info("CREWAI WORKFLOW COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 80)

            return final_report

        except Exception as e:
            self.logger.error(f"CrewAI workflow failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._generate_empty_report()

    def _generate_final_report(self, num_images: int, workflow_time: float, crew_result: Any) -> Dict[str, Any]:
        """Generate final statistics report."""
        report = {
            'num_images_ingested': num_images,
            'processing_time_seconds': round(workflow_time, 2),
            'workflow_type': 'CrewAI',
            'crew_result': str(crew_result)[:500],  # Truncate for brevity
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        return report

    def _generate_empty_report(self) -> Dict[str, Any]:
        """Generate empty report when no images are found."""
        return {
            'num_images_ingested': 0,
            'processing_time_seconds': 0.0,
            'workflow_type': 'CrewAI',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def _save_all_outputs(self, final_report: Dict[str, Any], crew_result: Any):
        """Save all outputs to files."""
        output_dir = Path(self.config.get('paths', {}).get('reports_output', './output/reports'))

        # Save crew result
        crew_output_file = output_dir / "crew_result.txt"
        with open(crew_output_file, 'w') as f:
            f.write(str(crew_result))
        self.logger.info(f"Saved crew result to {crew_output_file}")

        # Save final report
        report_file = output_dir / "final_report.json"
        save_json(final_report, report_file)
        self.logger.info(f"Saved final report to {report_file}")


def main():
    """Main entry point for CrewAI workflow."""
    print("\n" + "=" * 80)
    print("TRAVEL PHOTO ORGANIZATION WORKFLOW - CrewAI Edition")
    print("AI-Powered Agentic System for Photo Management")
    print("=" * 80 + "\n")

    try:
        orchestrator = CrewAITravelPhotoOrchestrator()
        final_report = orchestrator.run_workflow()

        print("\n" + "=" * 80)
        print("WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"Images Processed: {final_report['num_images_ingested']}")
        print(f"Total Processing Time: {final_report['processing_time_seconds']:.2f}s")
        print(f"Workflow Type: {final_report['workflow_type']}")
        print("=" * 80 + "\n")

        print(f"✓ All outputs saved to {orchestrator.timestamped_output}")
        print(f"✓ Reports saved at {orchestrator.timestamped_output / 'reports'}")
        print("\nWorkflow completed successfully!")

    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
