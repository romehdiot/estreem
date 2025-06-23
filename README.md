# Estreem Schema Tools

This repository contains scripts and data used to generate JSON schemas and sample
transactions for the Estreem project. All Python utilities are located in the
`scripts/` directory. Input spreadsheets and example schemas are kept at the root
of the repository.

## Requirements

The scripts require Python 3 with `pandas` and `openpyxl` installed. Install them
with:

```bash
pip install pandas openpyxl
```

## Available Scripts

- `scripts/dico_to_json.py` – converts the Excel DICO file into a simplified
  JSON description (`dico_schema.json`).
- `scripts/generate_normalized_json.py` – creates `normalized_schema.json` from
the normalized Excel file using `dico_schema.json`.
- `scripts/generate_input_details.py` – enriches an Avro schema with details
  from `normalized_schema.json`.
- `scripts/generate_test_transactions.py` – generates sample transaction files
  from a detailed schema.

Run each script from the repository root so that relative file paths resolve
correctly.

## Example Workflow

1. **Generate `dico_schema.json`**

   ```bash
   python scripts/dico_to_json.py
   ```

2. **Generate `normalized_schema.json`**

   ```bash
   python scripts/generate_normalized_json.py
   ```

3. **Build a detailed input schema**

   ```bash
   python scripts/generate_input_details.py normalized_schema.json \
       estreem-input.json detailed_schema.json
   ```

4. **Create test transactions**

   ```bash
   # Generate 5 transactions inside the `transactions/` folder
   python scripts/generate_test_transactions.py detailed_schema.json transactions 5
   ```

Each transaction is saved as `transaction_1.json`, `transaction_2.json`, etc. in
the specified folder.

