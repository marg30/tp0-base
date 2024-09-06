import csv

def calculate_size_stats(file_paths):
    total_bytes = {
        "nombre": 0,
        "apellido": 0,
        "documento": 0,
        "nacimiento": 0,
        "numero": 0,
    }
    max_bytes = {
        "nombre": 0,
        "apellido": 0,
        "documento": 0,
        "nacimiento": 0,
        "numero": 0,
    }
    min_bytes = {
        "nombre": float('inf'),
        "apellido": float('inf'),
        "documento": float('inf'),
        "nacimiento": float('inf'),
        "numero": float('inf'),
    }
    count = 0

    for file_path in file_paths:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                for field in total_bytes:
                    byte_size = len(row[field].encode('utf-8'))
                    total_bytes[field] += byte_size

                    # Update max and min
                    if byte_size > max_bytes[field]:
                        max_bytes[field] = byte_size
                    if byte_size < min_bytes[field]:
                        min_bytes[field] = byte_size

                count += 1

    average_bytes = {key: total_bytes[key] / count for key in total_bytes}

    return average_bytes, max_bytes, min_bytes

# List of CSV files
csv_files = [
    "agency-1.csv",
    "agency-2.csv",
    "agency-3.csv",
    "agency-4.csv",
    "agency-5.csv",
]

average_sizes, max_sizes, min_sizes = calculate_size_stats(csv_files)

print("Average size in bytes for each field:")
for field, avg_size in average_sizes.items():
    print(f"{field}: {avg_size:.2f} bytes")

print("\nMaximum size in bytes for each field:")
for field, max_size in max_sizes.items():
    print(f"{field}: {max_size} bytes")

print("\nMinimum size in bytes for each field:")
for field, min_size in min_sizes.items():
    print(f"{field}: {min_size} bytes")
