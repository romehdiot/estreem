import pandas as pd
import json
import re

def load_types(types_path):
    with open(types_path, 'r', encoding='utf-8') as f:
        types_data = json.load(f)
    object_to_type = {}
    for type_entry in types_data["Types"]:
        for type_name, type_info in type_entry.items():
            # On parcourt tous les objets du type
            for obj in type_info.get("objects", []):
                object_key = obj["Object"].lower().strip()
                # On extrait toutes les propriétés sauf 'objects'
                details = {k: v for k, v in type_info.items() if k != "objects"}
                # Ajoute codeset uniquement si isCodeSet True et codeset présent
                if type_info.get("isCodeSet") and "codeset" in type_info:
                    details["codeset"] = type_info["codeset"]
                object_to_type[object_key] = {
                    "type_name": type_name,
                    "details": details
                }
    return object_to_type

def respects_pattern(s):
    """True si s est du style xx.yy ou xx.yy.zz, false sinon"""
    s = s.strip()
    return bool(re.match(r"^[A-Za-z0-9]+\.[A-Za-z0-9]+(\.[A-Za-z0-9]+)?$", s))

def enrich_field(field_dict, object_to_type):
    iso_map = field_dict.get("iso20022_mapping", "")
    raw_iso_map = iso_map.strip()
    # Peut contenir plusieurs mappings séparés par virgule ou retour à la ligne
    candidates = [part.strip().lower() for part in raw_iso_map.replace('\n', ',').split(',') if part.strip() not in ["", "not applicable", "_"]]
    found = False

    for candidate in candidates:
        if candidate in object_to_type and respects_pattern(candidate):
            type_info = object_to_type[candidate]
            field_dict["type"] = {
                type_info["type_name"]: {
                    "details": type_info["details"]
                }
            }
            found = True
            break

    if not found:
        # On vérifie aussi le pattern sur le 1er candidat (si plusieurs, c’est rare)
        pattern_ok = respects_pattern(candidates[0]) if candidates else False
        found_in_types = candidates and candidates[0] in object_to_type
        field_dict["not_found_in_types"] = not (pattern_ok and found_in_types)
    else:
        field_dict["not_found_in_types"] = False

    return field_dict

def main():
    # 1) Fichiers
    excel_file = "(Mapping Estreem 1205) P2S NORMALIZED SCHEMA.xlsx"
    sheet_name = "P2S Normalized Model"
    types_path = "dico_schema.json"

    # 2) Lecture Types <obj_name>: type
    object_to_type = load_types(types_path)

    # 3) Lecture Excel
    df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name,
        engine='openpyxl',
        dtype=str
    )
    df.columns = df.columns.str.replace('\r', ' ', regex=False).str.replace('\n', ' ', regex=False).str.strip()

    # 4) Colonnes dynamiques et extraction
    mand_col = next(col for col in df.columns if 'Mandatory' in col)
    resp_col = next(col for col in df.columns if 'Responsibility' in col)
    comment_col = next((col for col in df.columns if "Comments SCO" in col), "Comments SCO")

    cols_to_extract = [
        'Object',
        'Field',
        mand_col,
        resp_col,
        'ESTREEM ISO 20022 Mapping',
        comment_col
    ]
    df_sel = df[cols_to_extract].dropna(how='all')
    df_sel.columns = [
        'object',
        'field',
        'mandatory_optional',
        'responsibility',
        'iso20022_mapping',
        'Commentaire'
    ]
    df_sel['iso20022_mapping'] = (
        df_sel['iso20022_mapping']
            .replace('N/A', pd.NA)
            .fillna('Not Applicable')
    )
    df_sel['field'] = (
        df_sel['field']
            .replace('', pd.NA)
            .fillna('Empty')
    )
    df_sel['Commentaire'] = df_sel['Commentaire'].fillna("")

    # 5) Group by object
    objects = []
    for obj_name, group in df_sel.groupby('object', sort=False):
        fields = []
        for _, row in group.iterrows():
            base_field = {
                "field": row["field"],
                "mandatory_optional": row["mandatory_optional"],
                "responsibility": row["responsibility"],
                "iso20022_mapping": row["iso20022_mapping"],
                "Commentaire": row["Commentaire"]
            }
            enriched_field = enrich_field(base_field, object_to_type)
            fields.append(enriched_field)
        objects.append({
            "object": obj_name,
            "fields": fields
        })

    # 6) Output JSON
    output = {"Objects": objects}
    with open('normalized_schema.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"→ {len(objects)} objets exportés dans normalized_schema.json")

if __name__ == "__main__":
    main()