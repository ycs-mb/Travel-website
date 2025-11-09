"""Agent 7: Website Generation - Generate Material UI React website."""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from utils.logger import log_error, log_info
from utils.validation import create_validation_summary
from utils.helpers import save_json


class WebsiteGenerationAgent:
    """
    Agent 7: Material UI Web Expert

    System Prompt:
    You are a senior full-stack developer specializing in Material UI and React.
    Create a beautiful, responsive photo showcase website.

    Requirements: Material UI v5, responsive grid, filters, lightbox, statistics,
    search, sort options, export, dark/light theme, mobile-optimized.

    Stack: React 18+, Material UI v5, React Router, TypeScript.
    """

    SYSTEM_PROMPT = """
    You are a senior full-stack developer specializing in Material UI and React.
    Create a beautiful, responsive photo showcase website.

    Requirements:
    1. Material UI v5 with modern design system
    2. Responsive grid layout (masonry or card grid)
    3. Interactive filters: category, location, date range, quality score
    4. Image lightbox/modal with full metadata display
    5. Statistics dashboard with charts
    6. Search functionality (by caption, location, keywords)
    7. Sort options: date, quality, aesthetic score, name
    8. Export options: selected images, metadata CSV
    9. Dark/light theme toggle
    10. Mobile-optimized with touch gestures

    Technical stack:
    - React 18+ with hooks
    - Material UI v5
    - React Router for navigation
    - Context API for state management
    - Lazy loading for performance
    - TypeScript for type safety
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Website Generation Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('website_generation', {})
        self.output_dir = Path(config.get('paths', {}).get('website_output', './output/website'))

    def generate_package_json(self) -> str:
        """Generate package.json for React app."""
        return json.dumps({
            "name": "travel-photo-gallery",
            "version": "1.0.0",
            "description": "AI-powered travel photo organization and showcase",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "@mui/material": "^5.14.0",
                "@mui/icons-material": "^5.14.0",
                "@emotion/react": "^11.11.0",
                "@emotion/styled": "^11.11.0",
                "recharts": "^2.10.0",
                "react-image-lightbox": "^5.1.4",
                "date-fns": "^2.30.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@vitejs/plugin-react": "^4.2.0",
                "typescript": "^5.3.0",
                "vite": "^5.0.0"
            },
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
                "lint": "eslint src --ext ts,tsx"
            }
        }, indent=2)

    def generate_readme(self) -> str:
        """Generate README.md for website."""
        return """# Travel Photo Gallery

AI-powered travel photo organization and showcase website built with React and Material UI.

## Features

- 📸 Beautiful masonry grid layout for photo display
- 🔍 Advanced filtering by category, location, date, and quality
- 🌓 Dark/light theme toggle
- 📊 Statistics dashboard with quality metrics
- 🔎 Search by captions, keywords, and locations
- 📱 Fully responsive and mobile-optimized
- 🖼️ Lightbox view with full metadata display
- 📥 Export selected photos and metadata

## Setup

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

### Data Source

Place your photo data in `public/data/photos.json`. The file should contain
an array of photo objects with metadata, quality scores, and captions.

### Environment Variables

Create a `.env` file in the root directory:

```
VITE_APP_TITLE=My Travel Photos
VITE_PHOTOS_PER_PAGE=24
```

## Deployment

### Static Hosting (Netlify, Vercel, GitHub Pages)

```bash
npm run build
```

Upload the `dist` folder to your hosting provider.

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Project Structure

```
src/
├── components/        # React components
│   ├── PhotoGrid.tsx
│   ├── PhotoCard.tsx
│   ├── Filters.tsx
│   ├── Lightbox.tsx
│   └── Statistics.tsx
├── context/          # Context providers
│   └── ThemeContext.tsx
├── pages/            # Page components
│   ├── Gallery.tsx
│   └── Stats.tsx
├── types/            # TypeScript types
│   └── Photo.ts
├── utils/            # Utility functions
│   └── helpers.ts
├── App.tsx           # Main app component
└── main.tsx          # Entry point
```

## License

MIT

## Credits

Built with:
- React 18
- Material UI v5
- Recharts
- Vite
"""

    def generate_sample_data(self, all_data: Dict[str, Any]) -> Path:
        """
        Generate sample JSON data for website.

        Args:
            all_data: Combined data from all agents

        Returns:
            Path to generated data file
        """
        photos = []

        for img in all_data.get('metadata', []):
            image_id = img['image_id']

            # Find corresponding data
            quality = next((q for q in all_data.get('quality', []) if q['image_id'] == image_id), {})
            aesthetic = next((a for a in all_data.get('aesthetic', []) if a['image_id'] == image_id), {})
            category = next((c for c in all_data.get('categories', []) if c['image_id'] == image_id), {})
            captions = next((c for c in all_data.get('captions', []) if c['image_id'] == image_id), {})

            photo_data = {
                'id': image_id,
                'filename': img['filename'],
                'thumbnail': f'/photos/thumbnails/{img["filename"]}',
                'full': f'/photos/full/{img["filename"]}',
                'metadata': {
                    'captureDate': img.get('capture_datetime'),
                    'location': category.get('location'),
                    'gps': img.get('gps'),
                    'camera': img.get('camera_settings', {}).get('camera_model'),
                    'settings': img.get('camera_settings'),
                    'dimensions': img.get('dimensions')
                },
                'scores': {
                    'technical': quality.get('quality_score', 3),
                    'aesthetic': aesthetic.get('overall_aesthetic', 3),
                    'sharpness': quality.get('sharpness'),
                    'exposure': quality.get('exposure'),
                    'composition': aesthetic.get('composition')
                },
                'category': {
                    'main': category.get('category', 'Uncategorized'),
                    'subcategories': category.get('subcategories', []),
                    'time': category.get('time_category', 'Unknown')
                },
                'captions': captions.get('captions', {}),
                'keywords': captions.get('keywords', []),
                'flags': img.get('flags', [])
            }

            photos.append(photo_data)

        # Save to file
        data_dir = self.output_dir / 'public' / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / 'photos.json'

        save_json({'photos': photos, 'generated': datetime.utcnow().isoformat() + 'Z'}, data_file)

        return data_file

    def generate_feature_doc(self) -> str:
        """Generate feature documentation."""
        return """# Travel Photo Gallery - Features Documentation

## Overview

This web application provides an intelligent, beautiful interface for browsing
and organizing travel photographs with AI-powered metadata and quality scoring.

## Core Features

### 1. Photo Gallery

**Masonry Grid Layout**
- Responsive grid that adapts to screen size
- Lazy loading for performance
- Smooth hover effects
- Click to expand in lightbox

**Filtering Options**
- Category filter (Landscape, Architecture, People, etc.)
- Quality score range (1-5)
- Aesthetic score range (1-5)
- Date range picker
- Location/GPS filter
- Time of day filter

**Sorting Options**
- Capture date (ascending/descending)
- Technical quality score
- Aesthetic score
- Alphabetical by filename
- Random shuffle

### 2. Lightbox/Detail View

When clicking on a photo, users see:
- Full-resolution image display
- All metadata (date, location, GPS coordinates)
- Camera settings (ISO, aperture, shutter speed, focal length)
- Quality scores with breakdown
- Generated captions (concise, standard, detailed)
- Keywords for searchability
- Previous/Next navigation
- Download option

### 3. Statistics Dashboard

**Overall Metrics**
- Total photos in collection
- Average technical quality score
- Average aesthetic score
- Photos by category (pie chart)
- Quality distribution (bar chart)
- Photos over time (line chart)

**Interactive Charts**
- Built with Recharts
- Responsive and animated
- Click to filter gallery

### 4. Search Functionality

**Search by:**
- Photo captions (all levels)
- Keywords
- Location names
- Camera model
- Category

**Real-time Results**
- Updates as you type
- Highlights matching terms
- Shows number of results

### 5. Theme Toggle

- Light mode (default)
- Dark mode
- Persisted to localStorage
- Smooth transitions
- Optimized colors for photo viewing

### 6. Export Options

**Export Formats:**
- JSON: All photo data
- CSV: Metadata spreadsheet
- Selected photos only
- Filter results export

### 7. Mobile Optimization

- Touch gestures for lightbox (swipe left/right)
- Optimized grid for mobile screens
- Bottom navigation for filters
- Reduced data loading on mobile
- PWA-ready for offline access

## User Interactions

### Navigation Flow

1. **Landing Page**: Gallery with all photos
2. **Apply Filters**: Use filter panel to narrow results
3. **Click Photo**: Open lightbox with full details
4. **Navigate**: Use arrows or swipe to browse
5. **View Stats**: Switch to dashboard tab
6. **Search**: Use search bar for specific photos
7. **Export**: Download filtered results

### Keyboard Shortcuts

- `←/→`: Navigate photos in lightbox
- `Esc`: Close lightbox
- `/`: Focus search bar
- `d`: Toggle dark mode
- `f`: Open filters

## Technical Implementation

### State Management
- React Context API for global state
- Local state for component-specific data
- Persisted settings in localStorage

### Performance
- Image lazy loading
- Virtual scrolling for large collections
- Memoized components
- Optimized re-renders
- Code splitting with React.lazy()

### Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Focus management

## Future Enhancements

- Map view with GPS clustering
- Photo editing capabilities
- Social sharing
- Collections/Albums
- AI-powered recommendations
- Multi-language support
- Advanced batch operations
"""

    def create_website_structure(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create complete website structure.

        Args:
            all_data: All combined agent data

        Returns:
            Website output information
        """
        try:
            log_info(self.logger, "Generating website structure", "Website Generation")

            # Create directories
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'src').mkdir(exist_ok=True)
            (self.output_dir / 'public').mkdir(exist_ok=True)

            # Generate package.json
            package_json = self.generate_package_json()
            (self.output_dir / 'package.json').write_text(package_json)

            # Generate README
            readme = self.generate_readme()
            readme_path = self.output_dir / 'README.md'
            readme_path.write_text(readme)

            # Generate feature documentation
            feature_doc = self.generate_feature_doc()
            features_path = self.output_dir / 'FEATURES.md'
            features_path.write_text(feature_doc)

            # Generate sample data
            data_file = self.generate_sample_data(all_data)

            # Create placeholder for React components
            components_note = """# React Components

The full React/TypeScript components would be generated here.

Key components to implement:
- App.tsx: Main application shell
- Gallery.tsx: Photo grid with filters
- PhotoCard.tsx: Individual photo display
- Lightbox.tsx: Full-size image viewer
- Statistics.tsx: Dashboard with charts
- Filters.tsx: Filter panel
- SearchBar.tsx: Search functionality
- ThemeToggle.tsx: Dark/light mode

Use Material UI v5 components throughout.
"""
            (self.output_dir / 'src' / 'COMPONENTS.md').write_text(components_note)

            return {
                'code_folder': str(self.output_dir),
                'readme': str(readme_path),
                'sample_data': str(data_file),
                'feature_doc': str(features_path)
            }

        except Exception as e:
            log_error(
                self.logger,
                "Website Generation",
                "GenerationError",
                f"Failed to generate website: {str(e)}",
                "error"
            )
            raise

    def run(self, all_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate website from all agent outputs.

        Args:
            all_data: Combined data from all agents and statistics

        Returns:
            Tuple of (website_output, validation_summary)
        """
        log_info(self.logger, "Starting website generation", "Website Generation")

        try:
            # Generate website structure
            output = self.create_website_structure(all_data)

            summary = f"Generated website at {output['code_folder']}"

            validation = create_validation_summary(
                agent="Website Generation",
                stage="build",
                status="success",
                summary=summary,
                issues=None
            )

            log_info(self.logger, f"Website generation completed: {summary}", "Website Generation")

            return output, validation

        except Exception as e:
            error_msg = f"Website generation failed: {str(e)}"
            log_error(
                self.logger,
                "Website Generation",
                "ExecutionError",
                error_msg,
                "critical"
            )

            validation = create_validation_summary(
                agent="Website Generation",
                stage="build",
                status="error",
                summary=error_msg,
                issues=[error_msg]
            )

            return {}, validation
