from pymongo import MongoClient, ASCENDING, DESCENDING

# =======================
# CONFIG
# =======================
MONGO_URI = "mongodb:27017"
DB_NAME = "wf_prov"
COLL_NAME = "do_vers"

BATCH_SIZE = 5000   # batch update
DRY_RUN = True      # True = test, False = effettivo

# =======================
# INIT
# =======================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLL_NAME]

cursor = coll.find(
    {},
    sort=[("dc_identifier", ASCENDING),
          ("dc_hasVersion", ASCENDING),
          ("schema_startDate", DESCENDING)],
    no_cursor_timeout=True,
    batch_size=BATCH_SIZE
)

prev_key = None
first_in_group = True
update_batch = []
total_processed = 0
total_soft_deleted = 0

try:
    for doc in cursor:
        total_processed += 1
        key = (doc.get("dc_identifier"), doc.get("dc_hasVersion"))

        if key != prev_key:
            prev_key = key
            first_in_group = True
        else:
            first_in_group = False

        if not first_in_group:
            # DUPLICATO → soft delete
            update_batch.append(doc["_id"])

        # Esegui batch update
        if len(update_batch) >= BATCH_SIZE:
            if not DRY_RUN:
                coll.update_many(
                    {"_id": {"$in": update_batch}},
                    {"$set": {"enabled": 0}}
                )
            total_soft_deleted += len(update_batch)
            update_batch.clear()

finally:
    cursor.close()

# flush finale
if update_batch and not DRY_RUN:
    coll.update_many(
        {"_id": {"$in": update_batch}},
        {"$set": {"enabled": 0}}
    )
    total_soft_deleted += len(update_batch)

print("DONE")
print(f"Total processed: {total_processed}")
print(f"Total soft deleted: {total_soft_deleted}")
print(f"DRY_RUN: {DRY_RUN}")