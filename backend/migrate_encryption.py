import asyncio
import os
import sys
from dotenv import load_dotenv
import asyncpg
from cryptography.fernet import Fernet
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from app.services.security import get_encryption_key, get_blind_index

load_dotenv()
load_dotenv("../.env")

raw_db_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL") or "postgresql://complaintiq:complaintiq@localhost:5432/complaintiq"
DATABASE_URL = raw_db_url.replace("+asyncpg", "")

raw_fernet = Fernet(get_encryption_key())
engine = FernetEngine()
engine._update_key(get_encryption_key())

def fix_encryption(val):
    if not val:
        return val
    if not str(val).startswith("gAAAAA"):
        # Actually plain text! Just encrypt it properly
        return engine.encrypt(str(val))
    
    # It starts with gAAAAA. Was it encrypted with raw_fernet?
    try:
        decrypted = raw_fernet.decrypt(str(val).encode('utf-8')).decode('utf-8')
        # Re-encrypt with correct engine
        return engine.encrypt(decrypted)
    except Exception as e:
        # If decryption fails, maybe it was already encrypted by engine?
        try:
            engine.decrypt(str(val))
            return val # already correctly encrypted
        except Exception:
            return val # Can't decrypt with either, leave it alone

def encrypt_val(val):
    return fix_encryption(val)

async def migrate():
    print(f"Connecting to {DATABASE_URL}...")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Ensure email_hash column exists
        try:
            await conn.execute("ALTER TABLE customers ADD COLUMN IF NOT EXISTS email_hash VARCHAR(100) UNIQUE")
            print("Ensured email_hash column exists.")
        except Exception as e:
            print(f"Note: {e}")

        # 1. Migrate Customers
        print("Migrating customers...")
        customers = await conn.fetch("SELECT id, email, phone FROM customers")
        for row in customers:
            email = row['email']
            phone = row['phone']
            
            enc_email = email
            enc_phone = phone
            update_needed = False
            
            # Determine plaintext email to compute email_hash
            plaintext_email = None
            if email:
                if str(email).startswith("gAAAAA"):
                    try:
                        plaintext_email = raw_fernet.decrypt(str(email).encode('utf-8')).decode('utf-8')
                    except:
                        try:
                            plaintext_email = engine.decrypt(str(email))
                        except:
                            plaintext_email = None
                else:
                    plaintext_email = email
                    
            email_hash = get_blind_index(plaintext_email) if plaintext_email else None
            
            if email:
                new_email = encrypt_val(email)
                if new_email != email:
                    enc_email = new_email
                    update_needed = True
            
            if phone:
                new_phone = encrypt_val(phone)
                if new_phone != phone:
                    enc_phone = new_phone
                    update_needed = True
                
            if update_needed or (email_hash is not None): # we might just need to update hash
                await conn.execute(
                    "UPDATE customers SET email=$1, email_hash=$2, phone=$3 WHERE id=$4",
                    enc_email, email_hash, enc_phone, row['id']
                )
        print(f"Migrated {len(customers)} customers.")

        # 2. Migrate Complaints
        print("Migrating complaints...")
        complaints = await conn.fetch("SELECT id, body FROM complaints")
        for row in complaints:
            body = row['body']
            if body:
                new_body = encrypt_val(body)
                if new_body != body:
                    await conn.execute("UPDATE complaints SET body=$1 WHERE id=$2", new_body, row['id'])
        print(f"Migrated {len(complaints)} complaints.")

        # 3. Migrate Entities
        print("Migrating entities...")
        # Catch errors just in case the entities table doesn't exist or is empty
        try:
            entities = await conn.fetch("SELECT id, entity_value FROM entities")
            for row in entities:
                val = row['entity_value']
                if val:
                    new_val = encrypt_val(val)
                    if new_val != val:
                        await conn.execute("UPDATE entities SET entity_value=$1 WHERE id=$2", new_val, row['id'])
            print(f"Migrated {len(entities)} entities.")
        except asyncpg.exceptions.UndefinedTableError:
            print("Entities table not found, skipping.")

        print("Migration completed successfully!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
