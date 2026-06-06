import os

def find_bom_files(directory="."):
    bom = b'\xef\xbb\xbf'
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    if f.read(3) == bom:
                        print(f"Znaleziono BOM: {path}")
            except IOError:
                pass

if __name__ == "__main__":
    find_bom_files()