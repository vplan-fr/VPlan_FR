# VPlan_FR

## Requirements
- as in [requirements.txt](requirements.txt)
  - ```bash
    python -m pip install -r requirements.txt
    ```
- MongoDB
- [creds.json](#credsjson) in repository root directory
- Installing npm packages
  - `cd client`
  - `npm install --force`

### `creds.json`
Example:
```json
{
  "example_school": {
    "school_number": "10000000",
    "hosting": {
      "creds": {},
      "endpoints": "https://www.stundenplan24.de/10000000/"
    }
  }
}
```

# Backend (Plan Crawler)
```bash
python -m backend.load_plans
```

# Server
## Environment variables
- `MONGO_URL`

```bash
python server.py
```

## Importing plan files
⚠️very sketchy⚠️
```bash
python -m backend.import_plans <directory/with/PlanKl/files>
```

