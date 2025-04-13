import csv
import os

CSV_FILE = 'process_log.csv'

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["processed", "skipped"])
            writer.writerow([0, 0])
            
def update_csv(processed_increment, skipped_increment):
    processed, skipped = read_stats()
    
    processed = processed_increment
    skipped = skipped_increment
    
    # Rewrite file with new totals
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["processed", "skipped"])
        writer.writerow([processed, skipped])
        
def read_stats():
    # Read current values
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        current = rows[0] if rows else {"processed": 0, "skipped": 0}
    # Update values
    return current["processed"], current["skipped"]
    
if __name__ == "__main__":
    while True:
        print("\nMenu:")
        print("1. Initialize CSV")
        print("2. Read Stats")
        print("3. Exit\n")
        
        choice = input("Enter your choice: ")
        print()
        match choice:
            case "1":
                init_csv()
                print("CSV initialized.")
            case "2":
                stats = read_stats()
                if stats:
                    print("Logged Stats:")
                    print(f"Processed: {stats[0]}, Skipped: {stats[1]}")
                else:
                    print("No stats available.")
            case "3":
                print("Exiting program.")
                break
            case _:
                print("Invalid choice. Please try again.")