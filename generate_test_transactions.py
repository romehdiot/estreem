import json
import random
import re
import sys
from typing import Any, Dict, List


def _generate_from_pattern(pattern: str) -> str:
    """Generate a numeric sample matching a simple regex pattern."""
    # Handle patterns like [0-9]{1,25}(\.?[0-9]{0,13})?
    m_range = re.search(r'\{(\d+),(\d+)\}', pattern)
    if m_range:
        min_len, max_len = int(m_range.group(1)), int(m_range.group(2))
    else:
        m_fixed = re.search(r'\{(\d+)\}', pattern)
        if m_fixed:
            min_len = max_len = int(m_fixed.group(1))
        else:
            min_len = max_len = 1

    int_len = random.randint(min_len, max_len)
    result = ''.join(str(random.randint(0, 9)) for _ in range(int_len))
    m_decimal = re.search(r'\\\.\?\[0-9\]\{0,(\d+)\}\)?', pattern)
    if m_decimal:
        dec_len = random.randint(0, int(m_decimal.group(1)))
        if dec_len > 0:
            result += '.' + ''.join(str(random.randint(0, 9)) for _ in range(dec_len))
    return result

def sample_from_details(field: Dict[str, Any]) -> Any:
    details = field.get('schema_details')
    if details:
        type_info = details.get('type', {})
        if type_info:
            typ_name, info = next(iter(type_info.items()))
            det = info.get('details', {})
            if det.get('isCodeSet') and 'codeset' in det:
                return random.choice(det['codeset'])['data']
            pattern = det.get('pattern')
            if pattern:
                return _generate_from_pattern(pattern)
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


def main(details_path: str, output_path: str) -> None:
    with open(details_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    sample = generate_sample(schema)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"→ Test transaction saved to {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python generate_test_transactions.py <detailed_schema.json> <output.json>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
