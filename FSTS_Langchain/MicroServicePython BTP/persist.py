import os
from hdbcli import dbapi
from cfenv import AppEnv

env = AppEnv()

hana_service = 'hana'
hana = env.get_service(label=hana_service)

# Read from .env
HOST = os.getenv("host")
PORT = int(os.getenv("port"))
USER = os.getenv("user")
PASSWORD = os.getenv("password")
CERT_PATH = os.getenv("certificate")  # Path to your .pem file

try:
    conn = dbapi.connect(
        address=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        encrypt="true",                   # SSL required
        sslValidateCertificate="true",    # Verify server certificate
        sslCryptoProvider="openssl",
        sslTrustStore=CERT_PATH           # Path to cert file
    )

    print("✅ Connected to SAP HANA successfully!")

    # schema_name = "3283c181-f7a3-4c09-abc2-8f6d118c7725"

    with conn.cursor() as cursor:

        # cursor.execute(f'SET SCHEMA "{schema_name}"')

        # # Create table if not exists
        # cursor.execute(f"""
        # CREATE COLUMN TABLE "{schema_name}"."FSTSHeader" (
        #     "id" NVARCHAR(36),
        #     "content" BLOB,
        #     "taskID" INTEGER,
        #     PRIMARY KEY ("id")
        # )
        # """)
        id = "ABCD"
        content = b"Example content"
        taskID = 1
        cursor.execute(f"""
       INSERT INTO "FSTSHeader3" ("id", "content", "taskID") VALUES (?, ?, ?)
        """, (id, content, taskID))

        # cursor.execute(f"""GRANT SELECT, INSERT, UPDATE, DELETE, CREATE ANY, DROP ON SCHEMA {os.getenv("schema")} TO DBADMIN WITH GRANT OPTION;""")

        
        # Check if table exists
        cursor.execute("""SELECT SCHEMA_NAME FROM SYS.SCHEMAS;""")
        result = cursor.fetchone()
        print(result)
        if result:
            print("✅ Table 'FSTSHeader' exists.")
        else:
            print("❌ Table 'FSTSHeader' does NOT exist.")

    conn.close()

except Exception as e:
    print("❌ Connection failed:", e)