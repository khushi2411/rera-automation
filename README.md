# Automating the process of scraping and uploading RERA data.

## Dependencies

### Python

- scrapy
- playwright
- webdriver-manager

Before installing these dependencies, it is recommended to create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Then, install the dependencies using pip:

```bash
pip install -r requirements.txt
```

### JavaScript

- firebase-admin

Install this dependency using npm:

```bash
npm install
```

### Service Account Key

- rera-serviceAccountKey.json

This file is required to authenticate with Firebase. Ensure you have downloaded the service account key from the Firebase console and placed it in the root directory of the project.

## Scripts

To run the project, execute the following script:

```bash
./run-scripts.sh
```

This script will:

1.  Scrape action IDs.
2.  Convert action IDs to CSV.
3.  Run residential shell scripts.
4.  Run plotted shell scripts.
5.  Upload plotted data.
6.  Upload residential data.
7.  Delete final merged files after upload.
