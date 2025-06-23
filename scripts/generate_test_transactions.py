import json
import os
import random
import re
import sys
from typing import Any, Dict, List

def sample_from_details(field: Dict[str, Any]) -> Any:
    details = field.get('schema_details')
    if details:
        type_info = details.get('type', {})
        if type_info:
            typ_name, info = next(iter(type_info.items()))
            det = info.get('details', {})
            if det.get('isCodeSet') and 'codeset' in det:
                return det['codeset'][0]['data']
            pattern = det.get('pattern')
            if pattern and pattern.startswith('['):
                m = re.search(r'{(\d+)', pattern)
                length = int(m.group(1)) if m else 1
                return ''.join(str(random.randint(0,9)) for _ in range(length))
            if det.get('type') == 'string':
                return 'sample'
    avro_type = field.get('type')
    if isinstance(avro_type, list):
        avro_type = [t for t in avro_type if t != 'null'][0]
    if isinstance(avro_type, dict) and avro_type.get('type') == 'record':
        return {sub['name']: sample_from_details(sub) for sub in avro_type.get('fields', [])}
    if avro_type in ('string', 'bytes'):
        return 'sample'
    if avro_type in ('int', 'long'):
        return 0
    if avro_type == 'boolean':
        return True
    return None

def generate_sample(schema: Dict[str, Any]) -> Dict[str, Any]:
    return {f['name']: sample_from_details(f) for f in schema.get('fields', [])}


def main(details_path: str, output_dir: str, count: int) -> None:
    with open(details_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    for i in range(1, count + 1):
        sample = generate_sample(schema)
        file_path = os.path.join(output_dir, f"transaction_{i}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)
        print(f"→ Test transaction saved to {file_path}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python generate_test_transactions.py <detailed_schema.json> <output_dir> <count>')
        sys.exit(1)
    try:
        count = int(sys.argv[3])
    except ValueError:
        print('count must be an integer')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], count)
