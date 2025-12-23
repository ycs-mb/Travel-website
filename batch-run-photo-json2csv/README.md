# Batch Photo Analysis to CSV

This tool iterates through a folder of images, sends them to the Photo Analysis API, and saves the results to a CSV file.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    Or if using `uv`:
    ```bash
    uv pip install -r requirements.txt
    ```

## Usage

**Basic Usage**:
```bash
python main.py /path/to/images output_results.csv --api-key YOUR_API_KEY
```

**Using Environment Variable for API Key**:
```bash
export API_KEY=your_key_here
python main.py /path/to/images output_results.csv
```

**Recursive Search**:
To look for images in subdirectories as well:
```bash
python main.py /path/to/images output_results.csv --recursive
```

**Custom API URL**:
If your API is running on a different port or host:
```bash
python main.py /path/to/images output_results.csv --api-url http://localhost:5000
```

## Output

The script generates:
1.  **[output_filename].csv**: Contains the successful analysis results.
2.  **[output_filename]_errors.csv**: (If errors occur) Contains a list of files that failed to process and the error message.
