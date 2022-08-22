import csv
import random

"""Tool which automatically replaces all the old IDs in the tickets.csv file with new IDs 
so that the ticket sorter can be tested
Requires that you have a tickets.csv file in this folder for testing"""

students = {}
with open("people.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        students[row['ID']] = row

tickets = []
id_lookup = {}
keys = list(students.keys())
with open("tickets.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        person_id = row["ID"]
        if person_id not in id_lookup:
            while True:
                new_id = keys[round(random.random() * len(keys))]
                if new_id not in id_lookup.values():
                    id_lookup[person_id] = new_id
                    break
    print(id_lookup)

with open("tickets.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        tickets.append({"ID": id_lookup[row["ID"]],
                        "Chocolate": row["Chocolate"],
                        "Rose": row["Rose"],
                        "Serenade": row["Serenade"]})

with open("tickets.csv", 'w') as file:
    writer = csv.DictWriter(file, fieldnames=["ID", "Chocolate", "Rose", "Serenade"])
    writer.writeheader()
    for row in tickets:
        writer.writerow(row)

