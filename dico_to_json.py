#!/usr/bin/env python3
import pandas as pd
import json

def safe_str(x):
    if pd.isna(x):
        return "vide"
    try:
        s = str(x).strip()
        return s if s else "vide"
    except Exception:
        return "vide"

def main():
    excel_file = "DICO_ESTREEM_v2513.xlsx"
    sheet_dico = "DICO_Complet"
    sheet_struct = "TypesStructures"
    sheet_simples = "TypesSimples"
    sheet_codeset = "Codeset"

    df_dico = pd.read_excel(excel_file, sheet_name=sheet_dico, header=1, dtype=str)
    df_struct = pd.read_excel(excel_file, sheet_name=sheet_struct, dtype=str)
    df_simple = pd.read_excel(excel_file, sheet_name=sheet_simples, dtype=str)
    df_code = pd.read_excel(excel_file, sheet_name=sheet_codeset, header=2, dtype=str)

    for df in (df_dico, df_struct, df_simple, df_code):
        df.columns = (
            df.columns
              .str.replace('\r',' ',regex=False)
              .str.replace('\n',' ',regex=False)
              .str.strip()
        )

    cols_dico = df_dico.columns.tolist()
    col_object = next(c for c in cols_dico if "object" in c.lower())
    col_attribute = next(c for c in cols_dico if "attribute" in c.lower())
    col_type = next(c for c in cols_dico if c.lower() == "type")

    df_struct = df_struct.rename(columns={
        next(c for c in df_struct.columns if "structure" in c.lower()): "Structure",
        next(c for c in df_struct.columns if "attributes" in c.lower()): "Attributes",
        next(c for c in df_struct.columns if "typologie" in c.lower()): "Typologie"
    })

    cols_simple = df_simple.columns.tolist()
    col_ts_label = next(c for c in cols_simple if 'libell' in c.lower())
    col_ts_def = next(c for c in cols_simple if 'défin' in c.lower())
    col_ts_type = next(c for c in cols_simple if 'type' in c.lower() and 'typologie' not in c.lower() and 'pattern' not in c.lower())
    col_ts_pattern = next(c for c in cols_simple if 'pattern' in c.lower())
    df_simple = (
        df_simple
        .rename(columns={
            col_ts_label: 'typologie',
            col_ts_def: 'definition',
            col_ts_type: 'simple_type',
            col_ts_pattern: 'pattern'
        })
        [['typologie','definition','simple_type','pattern']]
        .drop_duplicates('typologie', keep='first')
    )
    mapping_simple = df_simple.set_index('typologie').to_dict(orient='index')

    cols_code = df_code.columns.tolist()
    col_cs_codeset = cols_code[0]
    col_cs_format = cols_code[1]
    col_cs_data = cols_code[2]

    grouped = {}

    for idx, row in df_dico.iterrows():
        xx = safe_str(row.get(col_object, "vide"))
        yy = safe_str(row.get(col_attribute, "vide"))
        zz_base = safe_str(row.get(col_type, "vide"))

        matches = df_struct[df_struct['Structure'].apply(safe_str).str.lower() == zz_base.lower()]
        if matches.empty:
            type_value = zz_base
            obj = {"Object": f"{xx}.{yy}"}
            grouped.setdefault(type_value, []).append(obj)
        else:
            for _, st_row in matches.iterrows():
                zz_multi = safe_str(st_row['Attributes'])
                struct_typologie = safe_str(st_row['Typologie'])
                type_value = struct_typologie
                obj = {"Object": f"{xx}.{yy}.{zz_multi}"}
                grouped.setdefault(type_value, []).append(obj)

    types_list = []
    for type_value, items in grouped.items():
        is_code_set = not df_code[df_code[col_cs_codeset].apply(safe_str) == type_value].empty
        dico_type = {
            "isCodeSet": is_code_set
        }
        if is_code_set:
            codeset_rows = df_code[df_code[col_cs_codeset].apply(safe_str) == type_value]
            dico_type["codeset"] = [
                {
                    "data": safe_str(r[col_cs_data]),
                    "format": safe_str(r[col_cs_format])
                }
                for _, r in codeset_rows.iterrows()
            ]
        else:
            info = mapping_simple.get(type_value)
            dico_type["definition"] = safe_str(info['definition']) if info else ""
            dico_type["type"] = safe_str(info['simple_type']) if info else ""
            pat = info['pattern'] if info else ""
            dico_type["pattern"] = safe_str(pat) if safe_str(pat) != "vide" else "---"
        dico_type["objects"] = items
        types_list.append({type_value: dico_type})

    final_json = {"Types": types_list}

    output_path = "dico_schema.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)

    print(f"\nFichier sauvegardé sous : {output_path}")

if __name__ == "__main__":
    main()