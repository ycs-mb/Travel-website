#!/usr/bin/env python3
"""Run multiple agents on image directory for testing and development."""

from pathlib import Path
from utils.helpers import load_config, get_image_files, save_json
from utils.logger import setup_logger
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.filtering_categorization import FilteringCategorizationAgent
from agents.caption_generation import CaptionGenerationAgent


def main():
    """Run agents on images in sample_images directory."""
    config = load_config("config.yaml")
    logger = setup_logger()

    # Get images
    input_dir = Path(config['paths']['input_images'])
    image_paths = get_image_files(input_dir)

    if not image_paths:
        print(f"No images found in {input_dir}")
        return

    print("=" * 80)
    print(f"Processing {len(image_paths)} images")
    print("=" * 80)

    # Agent 1: Metadata Extraction
    print("\n→ Agent 1: Extracting metadata...")
    metadata_agent = MetadataExtractionAgent(config, logger)
    metadata_list, val1 = metadata_agent.run(image_paths)
    print(f"  ✓ {val1['summary']}")
    if val1.get('issues'):
        for issue in val1['issues'][:3]:  # Show first 3 issues
            print(f"    ⚠ {issue}")

    # Agent 2: Quality Assessment
    print("\n→ Agent 2: Assessing technical quality...")
    quality_agent = QualityAssessmentAgent(config, logger)
    quality_list, val2 = quality_agent.run(image_paths, metadata_list)
    print(f"  ✓ {val2['summary']}")
    if val2.get('issues'):
        for issue in val2['issues'][:3]:
            print(f"    ⚠ {issue}")

    # Agent 3: Aesthetic Assessment
    print("\n→ Agent 3: Assessing aesthetic quality...")
    aesthetic_agent = AestheticAssessmentAgent(config, logger)
    aesthetic_list, val3 = aesthetic_agent.run(image_paths, metadata_list)
    print(f"  ✓ {val3['summary']}")
    if val3.get('issues'):
        for issue in val3['issues'][:3]:
            print(f"    ⚠ {issue}")

    # Agent 5: Filtering & Categorization
    print("\n→ Agent 5: Categorizing images...")
    filtering_agent = FilteringCategorizationAgent(config, logger)
    categories, val5 = filtering_agent.run(image_paths, metadata_list, quality_list, aesthetic_list)
    print(f"  ✓ {val5['summary']}")
    if val5.get('issues'):
        for issue in val5['issues'][:3]:
            print(f"    ⚠ {issue}")

    # Agent 6: Caption Generation
    print("\n→ Agent 6: Generating captions...")
    caption_agent = CaptionGenerationAgent(config, logger)
    captions, val6 = caption_agent.run(image_paths, metadata_list, quality_list, aesthetic_list, categories)
    print(f"  ✓ {val6['summary']}")
    if val6.get('issues'):
        for issue in val6['issues'][:3]:
            print(f"    ⚠ {issue}")

    # Save results
    output_dir = Path("agent_outputs")
    output_dir.mkdir(exist_ok=True)
    save_json(metadata_list, output_dir / "metadata.json")
    save_json(quality_list, output_dir / "quality.json")
    save_json(aesthetic_list, output_dir / "aesthetic.json")
    save_json(categories, output_dir / "categories.json")
    save_json(captions, output_dir / "captions.json")

    # Print sample results
    print("\n" + "=" * 80)
    print("SAMPLE RESULTS")
    print("=" * 80)

    if metadata_list:
        m = metadata_list[0]
        print(f"\n📸 {m['filename']}")
        print(f"   GPS: {m['gps'].get('location', 'Not found')} ({m['gps']['latitude']}, {m['gps']['longitude']})")
        print(f"   DateTime: {m['capture_datetime']}")
        print(f"   Camera: {m['camera_settings'].get('camera_model', 'Unknown')}")

    if quality_list:
        q = quality_list[0]
        print(f"\n⭐ Quality Score: {q.get('quality_score', 'N/A')}/5 (Sharpness: {q.get('sharpness', 'N/A')})")

    if aesthetic_list:
        a = aesthetic_list[0]
        print(f"\n🎨 Aesthetic Score: {a.get('overall_aesthetic', 'N/A')}/5")
        print(f"   Composition: {a.get('composition', 'N/A')}/5 | Lighting: {a.get('lighting', 'N/A')}/5")

    if categories:
        c = categories[0]
        print(f"\n📂 Category: {c.get('category', 'Unknown')} | Time: {c.get('time_category', 'Unknown')}")

    if captions:
        cap = captions[0]
        print(f"\n📝 Concise: {cap['captions'].get('concise', 'N/A')}")

    print("\n" + "=" * 80)
    print(f"✓ All results saved to {output_dir}")
    print(f"  - metadata.json: EXIF data and GPS locations")
    print(f"  - quality.json: Technical quality scores")
    print(f"  - aesthetic.json: Artistic quality assessment")
    print(f"  - categories.json: Image categorization and filtering")
    print(f"  - captions.json: Generated captions and keywords")
    print("=" * 80)


if __name__ == "__main__":
    main()
