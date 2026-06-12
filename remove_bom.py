import os

def remove_bom_from_files(directory="."):
    bom = b'\xef\xbb\xbf'
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                
                if content.startswith(bom):
                    with open(path, 'wb') as f:
                        f.write(content[3:])
                    print(f"Usunięto BOM z: {path}")
            except IOError:
                pass

if __name__ == "__main__":
    remove_bom_from_files()