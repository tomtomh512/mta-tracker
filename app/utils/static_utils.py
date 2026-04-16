import zipfile, io, csv

def read_csv_from_zip(z: zipfile.ZipFile, filename: str) -> list[dict]:
    with z.open(filename) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
        return list(reader)