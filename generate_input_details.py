import json
import re
import sys
from typing import Any, Dict, List


def _canon(parts: List[str]) -> str:
    """Return a normalized key used for matching fields."""
    joined = "".join(parts)
    return re.sub(r"[^a-z0-9]", "", joined.lower())

def load_clean_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    txt = re.sub(r"root@[^\n]*#", "", txt)
    txt = txt.strip()
    return json.loads(txt)

def build_field_map(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a mapping of canonical field path to details."""
    mapping: Dict[str, Any] = {}
    for obj in normalized_data.get('Objects', []):
        obj_name = obj.get('object', '')
        for f in obj.get('fields', []):
            key_field = _canon([f['field']])
            mapping[key_field] = f
            key_with_obj = _canon([obj_name, f['field']])
            mapping.setdefault(key_with_obj, f)
    return mapping

def enrich_fields(fields: List[Dict[str, Any]], field_map: Dict[str, Any], path: List[str]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for field in fields:
        base: Dict[str, Any] = {k: v for k, v in field.items() if k != 'type'}
        avro_type = field['type']
        sub_path = path + [field['name']]
        if isinstance(avro_type, dict) and avro_type.get('type') == 'record':
            sub_fields = enrich_fields(avro_type.get('fields', []), field_map, path + [avro_type.get('name', '')])
            new_type = dict(avro_type)
            new_type['fields'] = sub_fields
            base['type'] = new_type
        elif isinstance(avro_type, list):
            new_types: List[Any] = []
            for t in avro_type:
                if isinstance(t, dict) and t.get('type') == 'record':
                    sub_fields = enrich_fields(t.get('fields', []), field_map, path + [t.get('name', '')])
                    t_new = dict(t)
                    t_new['fields'] = sub_fields
                    new_types.append(t_new)
                else:
                    new_types.append(t)
            base['type'] = new_types
        else:
            base['type'] = avro_type

        key_path = _canon(path + [field['name']])
        key_field = _canon([field['name']])
        details = field_map.get(key_path) or field_map.get(key_field)
        if details:
            base['schema_details'] = {k: v for k, v in details.items() if k != 'field'}
        enriched.append(base)
    return enriched

def generate_details(normalized_path: str, avro_path: str, output_path: str) -> None:
    normalized = load_clean_json(normalized_path)
    avro_schema = load_clean_json(avro_path)
    field_map = build_field_map(normalized)
    enriched_fields = enrich_fields(avro_schema.get('fields', []), field_map, [])
    detailed_schema = {
        'name': avro_schema.get('name'),
        'type': avro_schema.get('type'),
        'namespace': avro_schema.get('namespace'),
        'fields': enriched_fields,
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_schema, f, ensure_ascii=False, indent=2)
    print(f"→ Detailed schema saved to {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python generate_input_details.py <normalized_schema.json> <avro_input.json> <output.json>')
        sys.exit(1)
    generate_details(sys.argv[1], sys.argv[2], sys.argv[3])
