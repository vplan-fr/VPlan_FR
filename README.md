# VPlan_FR

## Requirements
- as in [requirements.txt](requirements.txt)
  - ```bash
    python -m pip install -r requirements.txt
    ```
- [creds.json](#credsjson) in repository root directory

### `creds.json`
Example:
```json
{
  "10000000": {
    "school_number": "10000000",
    "school_name": "example_school",
    "display_name": "Example School",
    "username": "",
    "password": "",
    "api_server": "https://stundenplan24.de/"
  }
}
```

# Backend (Plan Crawler)
```bash
python -m backend.load_plans
```

## Importing plan files
⚠️very sketchy⚠️
```bash
python -m backend.import_plans <directory/with/PlanKl/files>
```

