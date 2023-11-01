# holmes/spy.py

import csv
import os
import yaml

# Load MIME type mappings from YAML file
with open("bond/config.yml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
        mime_mapping = config.get('mime_mapping', {})
    except yaml.YAMLError as exc:
        print(exc)
        mime_mapping = {}

def get_pretty_mime(mime_type):
    category, detail = mime_type.split('/')
    return mime_mapping.get(category, {}).get(detail, mime_type)

def pretty_size(size):
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"

def get_file_path(service, file_id):
    path_parts = []
    while file_id:
        file = service.files().get(fileId=file_id, fields='id, name, parents').execute()
        path_parts.insert(0, file['name'])
        file_id = file.get('parents', [None])[0]
    return '/'.join(path_parts)

def list_files(service):
    page_num = 0
    running_total = 0
    types_count = {}
    csv_path = os.path.join(os.getcwd(), 'files.csv')

    print(f"Writing to CSV at {csv_path}...")

    try:
        with open(csv_path, mode='w', newline='') as csv_file:
            fieldnames = ['Name', 'ID', 'Path', 'Type', 'MIME Type', 'Last Modified', 'Created', 'Size', 'Shared']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            while True:
                results = service.files().list(
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime, createdTime, size, shared, permissions)"
                ).execute()

                items = results.get('files', [])
                if not items:
                    print('No files found.')
                    break

                print("Writing items to CSV...")
                for item in items:
                    mime_type = item.get('mimeType', 'N/A')
                    pretty_mime = get_pretty_mime(mime_type)

                    writer.writerow({
                        'Name': item['name'],
                        'ID': item['id'],
                        'Path': get_file_path(service, item['id']),
                        'Type': pretty_mime,
                        'MIME Type': mime_type,
                        'Last Modified': item.get('modifiedTime', 'N/A'),
                        'Created': item.get('createdTime', 'N/A'),
                        'Size': pretty_size(int(item.get('size', 0))),
                        'Shared': item.get('shared', False)
                    })

                    # update counts for summary
                    types_count[pretty_mime] = types_count.get(pretty_mime, 0) + 1

                running_total += len(items)
                page_num += 1
                print(f"Page {page_num} complete. {len(items)} items on this page. Running total: {running_total}.")

                # Check for more pages
                if results.get('nextPageToken', None) is None:
                    break

            # Print summary
            print(f"Total files: {running_total}")
            for type_name, count in types_count.items():
                print(f"{type_name}: {count}")

    except Exception as e:
        print(f"An error occurred: {e}")
