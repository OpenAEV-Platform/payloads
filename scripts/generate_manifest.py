from pathlib import Path

import json_api_doc
import orjson

ORJSON_OPTION = orjson.OPT_INDENT_2 | orjson.OPT_NAIVE_UTC | orjson.OPT_OMIT_MICROSECONDS | orjson.OPT_SORT_KEYS

def is_valid_json_api(json_data):
    """check if the JSON data is in the JSON:API format"""
    return "data" in json_data.keys()

def is_valid_json_flat(json_data):
    """check if the JSON data is in the legacy flat JSON payload format"""
    return "payload_information" in json_data.keys()

def process_json_api(data, file_path, root_path):
    flat_data = json_api_doc.deserialize(data)

    # extracting tags, cleaning them for future use and simplifying them in the flat_data
    payload_tags = flat_data.get("payload_tags", [])
    for idx in range(len(payload_tags)):
        if "id" in payload_tags[idx]:
            del payload_tags[idx]["id"]
        if "type" in payload_tags[idx]:
            del payload_tags[idx]["type"]
    flat_data["payload_tags"] = [tag["tag_id"] for tag in payload_tags]

    # extracting domains and simplifying them in the flat_data
    payload_domains = flat_data.get("payload_domains", [])
    flat_data["payload_domains"] = [
        {"domain_name": domain["domain_name"], "domain_color": domain["domain_color"]}
        for domain in payload_domains
    ]

    # extracting attack_patterns, cleaning them for future use and rewriting them in flat_data
    payload_attack_patterns = flat_data.get("payload_attack_patterns", [])
    for idx in range(len(payload_attack_patterns)):
        if "id" in payload_attack_patterns[idx]:
            del payload_attack_patterns[idx]["id"]
        if "type" in payload_attack_patterns[idx]:
            del payload_attack_patterns[idx]["type"]
    flat_data["payload_attack_patterns"] = payload_attack_patterns

    # looking for relevant document(s) and formatting them to the previous format
    payload_document = {}
    file_lookup = [
        key for key
        in flat_data
        if isinstance(flat_data[key], dict) and flat_data[key].get("type") == "documents"
    ]
    if len(file_lookup)>1:
        print("Warning, more than one file detected as attachment, fallback to first found")
    if file_lookup:
        file_key = file_lookup[0]
        payload_document = flat_data.pop(file_key)
        flat_data[file_key] = payload_document.get("document_id")
        if "id" in payload_document:
            del payload_document["id"]
        if "type" in payload_document:
            del payload_document["type"]
        payload_document["document_tags"] = [
            tag["tag_id"] for tag
            in payload_document.get("document_tags", [])
        ]

        attachment_path = file_path.parent / "attachments.zip"
        if attachment_path.is_file():
            # Compute relative path from root_path and make URL-compatible
            relative_path = attachment_path.relative_to(root_path)
            relative_path = relative_path.as_posix()
            if payload_document.get("document_path") != relative_path:
                payload_document["document_path"] = relative_path
    flat_data["payload_document"] = payload_document

    if "payload_external_id" not in flat_data or flat_data["payload_external_id"] is None:
        flat_data["payload_external_id"] = flat_data["payload_id"]
    if flat_data.get("payload_source") != "FILIGRAN":
        flat_data["payload_source"] = "FILIGRAN"
    if flat_data.get("payload_status") != "VERIFIED":
        flat_data["payload_status"] = "VERIFIED"

    for key in ["id", "type", "payload_id", "payload_collector", "payload_collector_type"]:
        if key in flat_data:
            del flat_data[key]

    final_data = {
        "payload_information": flat_data,
        "payload_tags": payload_tags,
        "payload_document": payload_document,
        "payload_attack_patterns": payload_attack_patterns,
    }

    bindata = orjson.dumps(final_data, default=str, option=ORJSON_OPTION)
    file_path.write_bytes(bindata)

    return final_data

def process_json_flat(data, file_path, root_path):
    changed = False

    payload_information = data.get("payload_information", {})
    if payload_information and isinstance(payload_information, dict):
        # Set required values
        if payload_information.get("payload_source") != "FILIGRAN":
            payload_information["payload_source"] = "FILIGRAN"
            changed = True
        if payload_information.get("payload_status") != "VERIFIED":
            payload_information["payload_status"] = "VERIFIED"
            changed = True

        # Handle payload_external_id and payload_id
        if "payload_external_id" not in payload_information or payload_information["payload_external_id"] is None:
            payload_information["payload_external_id"] = payload_information["payload_id"]
            changed = True

        # Remove unwanted keys
        for key in ["payload_collector_type", "payload_collector", "payload_id"]:
            if key in payload_information:
                del payload_information[key]
                changed = True
    data["payload_information"] = payload_information

    # Handle document_path in payload_document if attachments.zip exists
    payload_document = data.get("payload_document")
    if payload_document is not None and isinstance(payload_document, dict):
        attachment_path = file_path.parent / "attachments.zip"
        if attachment_path.is_file():
            # Compute relative path from root_path and make URL-compatible
            relative_path = attachment_path.relative_to(root_path)
            relative_path = relative_path.as_posix()
            if payload_document.get("document_path") != relative_path:
                payload_document["document_path"] = relative_path
                changed = True
    data["payload_document"] = payload_document

    if changed:
        bindata = orjson.dumps(data, default=str, option=ORJSON_OPTION)
        file_path.write_bytes(bindata)

    return data

def fix_and_load_json(file_path, root_path, raise_on_unknown=False):
    """route the file data in the proper processing function according to format"""
    print(f"Processing {file_path}")
    try:
        data = orjson.loads(file_path.read_bytes())

        if is_valid_json_api(data):
            print("File detected as matching the JSON:API format")
            data = process_json_api(data, file_path, root_path)
        elif is_valid_json_flat(data):
            print("File detected as matching the legacy JSON flat format")
            data = process_json_flat(data, file_path, root_path)
        else:
            if raise_on_unknown:
                print("File is neither JSON:API nor legacy JSON flat format")
                raise ValueError()
        return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def find_json_files(root_path, ignore_path):
    """recursively check for JSON files under root_path"""
    return [
        file for file
        in root_path.glob("**/*.json")
        if file != ignore_path
    ]

def merge_json_files(json_files, parent_dir):
    merged = []
    for file in json_files:
        data = fix_and_load_json(file, parent_dir)
        if data is None:
            continue
        if isinstance(data, list):
            merged.extend(data)
        else:
            merged.append(data)
    return merged


if __name__ == "__main__":
    root_path = Path(__file__).resolve().parent
    output_path = root_path / "manifest.json"

    json_files = find_json_files(root_path, output_path)
    print(f"Found {len(json_files)} JSON files.")

    merged_data = merge_json_files(json_files, root_path)
    bindata = orjson.dumps(merged_data, default=str, option=ORJSON_OPTION)
    output_path.write_bytes(bindata)
    print(f"Merged JSON saved to {output_path}")
