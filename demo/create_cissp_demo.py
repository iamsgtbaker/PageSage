#!/usr/bin/env python3
"""Create a CISSP demo database with ~150 entries"""

import sqlite3
import os
from pathlib import Path

# Delete existing demo database
demo_path = Path(__file__).parent / "demo_index.db"
if demo_path.exists():
    os.remove(demo_path)

conn = sqlite3.connect(str(demo_path))
cursor = conn.cursor()

# Create tables
cursor.executescript('''
    CREATE TABLE terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term TEXT NOT NULL UNIQUE COLLATE NOCASE,
        notes TEXT DEFAULT '',
        ai_description TEXT,
        is_tool INTEGER,
        ai_enriched_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE page_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term_id INTEGER NOT NULL,
        book_number INTEGER NOT NULL,
        page_start INTEGER NOT NULL,
        page_end INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (term_id) REFERENCES terms(id),
        UNIQUE(term_id, book_number, page_start, page_end)
    );

    CREATE INDEX idx_term_lookup ON terms(term COLLATE NOCASE);

    CREATE TABLE settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_number TEXT NOT NULL UNIQUE,
        book_name TEXT NOT NULL,
        page_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE gap_exclusions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_number TEXT NOT NULL,
        page_start INTEGER NOT NULL,
        page_end INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(book_number, page_start, page_end)
    );

    CREATE TABLE custom_properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_name TEXT NOT NULL,
        property_value TEXT NOT NULL,
        display_order INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

# Add settings
cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('index_name', 'CISSP Study Guide'))
cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('color_scheme', '#4a90d9'))

# Add books (CISSP 8 Domains)
books = [
    ('1', 'Security and Risk Management', 180),
    ('2', 'Asset Security', 95),
    ('3', 'Security Architecture and Engineering', 210),
    ('4', 'Communication and Network Security', 165),
    ('5', 'Identity and Access Management', 120),
    ('6', 'Security Assessment and Testing', 85),
    ('7', 'Security Operations', 195),
    ('8', 'Software Development Security', 110),
]

for book_num, book_name, page_count in books:
    cursor.execute("INSERT INTO books (book_number, book_name, page_count) VALUES (?, ?, ?)",
                   (book_num, book_name, page_count))

# CISSP Terms organized by domain
terms_data = [
    # Domain 1: Security and Risk Management
    ("Risk Assessment", [(1, 12, 18)], "Process of identifying, analyzing, and evaluating risks to organizational assets"),
    ("Risk Mitigation", [(1, 19, 25)], "Strategies to reduce risk to acceptable levels"),
    ("Risk Acceptance", [(1, 26, 28)], ""),
    ("Risk Avoidance", [(1, 29, 31)], ""),
    ("Risk Transfer", [(1, 32, 35)], "Shifting risk to third party, often through insurance"),
    ("Quantitative Risk Analysis", [(1, 40, 48)], "Uses numerical values: ALE = SLE x ARO"),
    ("Qualitative Risk Analysis", [(1, 49, 55)], "Uses descriptive categories: High, Medium, Low"),
    ("Annual Loss Expectancy (ALE)", [(1, 42, 44)], "ALE = SLE x ARO; Expected yearly loss from a threat"),
    ("Single Loss Expectancy (SLE)", [(1, 45, 46)], "SLE = Asset Value x Exposure Factor"),
    ("Annual Rate of Occurrence (ARO)", [(1, 47, 48)], ""),
    ("Business Impact Analysis (BIA)", [(1, 60, 72)], "Identifies critical business functions and their dependencies"),
    ("Maximum Tolerable Downtime (MTD)", [(1, 65, 67)], ""),
    ("Recovery Time Objective (RTO)", [(1, 68, 70)], "Target time to restore systems after disaster"),
    ("Recovery Point Objective (RPO)", [(1, 71, 72)], "Maximum acceptable data loss measured in time"),
    ("Due Care", [(1, 80, 82)], "Reasonable steps taken to protect assets"),
    ("Due Diligence", [(1, 83, 85)], "Research and analysis before making decisions"),
    ("Security Policy", [(1, 90, 98)], "High-level statement of management intent"),
    ("Security Standards", [(1, 99, 102)], ""),
    ("Security Procedures", [(1, 103, 108)], ""),
    ("Security Guidelines", [(1, 109, 112)], ""),
    ("Security Baselines", [(1, 113, 115)], ""),
    ("Separation of Duties", [(1, 120, 124)], "No single person controls all aspects of critical function"),
    ("Least Privilege", [(1, 125, 128)], "Users get minimum access needed for job"),
    ("Need to Know", [(1, 129, 131)], ""),
    ("Job Rotation", [(1, 132, 135)], ""),
    ("Mandatory Vacation", [(1, 136, 138)], "Helps detect fraud by requiring time away"),
    ("Non-Disclosure Agreement (NDA)", [(1, 145, 148)], ""),
    ("Service Level Agreement (SLA)", [(1, 149, 152)], ""),
    ("Intellectual Property", [(1, 155, 165)], ""),
    ("Copyright", [(1, 156, 158)], ""),
    ("Trademark", [(1, 159, 161)], ""),
    ("Patent", [(1, 162, 164)], ""),
    ("Trade Secret", [(1, 165, 167)], ""),
    ("GDPR", [(1, 170, 175)], "EU data protection regulation"),
    ("HIPAA", [(1, 176, 180)], "US healthcare data protection"),

    # Domain 2: Asset Security
    ("Data Classification", [(2, 8, 18)], "Categorizing data based on sensitivity and value"),
    ("Data Handling", [(2, 19, 25)], ""),
    ("Data Retention", [(2, 26, 32)], "How long to keep data before destruction"),
    ("Data Remanence", [(2, 33, 38)], "Residual data remaining after deletion"),
    ("Data Destruction", [(2, 39, 45)], ""),
    ("Degaussing", [(2, 40, 42)], "Using magnetic field to erase magnetic media"),
    ("Cryptographic Erasure", [(2, 43, 45)], ""),
    ("Data Owner", [(2, 50, 53)], "Executive responsible for data classification"),
    ("Data Custodian", [(2, 54, 57)], "IT staff responsible for implementing controls"),
    ("Data Steward", [(2, 58, 60)], ""),
    ("System Owner", [(2, 61, 63)], ""),
    ("Data States", [(2, 70, 78)], "Data at rest, in transit, and in use"),
    ("Data at Rest", [(2, 71, 73)], ""),
    ("Data in Transit", [(2, 74, 76)], ""),
    ("Data in Use", [(2, 77, 78)], ""),
    ("Scoping", [(2, 82, 85)], ""),
    ("Tailoring", [(2, 86, 90)], ""),

    # Domain 3: Security Architecture and Engineering
    ("Security Models", [(3, 10, 45)], ""),
    ("Bell-LaPadula Model", [(3, 12, 20)], "Confidentiality model: No read up, no write down"),
    ("Biba Model", [(3, 21, 28)], "Integrity model: No write up, no read down"),
    ("Clark-Wilson Model", [(3, 29, 35)], "Integrity through well-formed transactions"),
    ("Brewer-Nash Model", [(3, 36, 40)], "Chinese Wall model for conflict of interest"),
    ("Defense in Depth", [(3, 50, 58)], "Multiple layers of security controls"),
    ("Zero Trust", [(3, 59, 68)], "Never trust, always verify"),
    ("Trusted Computing Base (TCB)", [(3, 72, 78)], ""),
    ("Security Kernel", [(3, 79, 82)], ""),
    ("Reference Monitor", [(3, 83, 86)], ""),
    ("Common Criteria", [(3, 90, 102)], "International standard for security evaluation"),
    ("Evaluation Assurance Level (EAL)", [(3, 95, 102)], "EAL1 through EAL7"),
    ("Cryptography", [(3, 110, 160)], ""),
    ("Symmetric Encryption", [(3, 112, 125)], "Same key for encryption and decryption"),
    ("AES", [(3, 118, 122)], "Advanced Encryption Standard, 128/192/256-bit keys"),
    ("DES", [(3, 115, 117)], "Legacy 56-bit encryption, now deprecated"),
    ("3DES", [(3, 123, 125)], ""),
    ("Asymmetric Encryption", [(3, 126, 142)], "Public/private key pairs"),
    ("RSA", [(3, 130, 135)], "Based on factoring large prime numbers"),
    ("Diffie-Hellman", [(3, 136, 140)], "Key exchange algorithm"),
    ("Elliptic Curve Cryptography (ECC)", [(3, 141, 145)], ""),
    ("Hash Functions", [(3, 146, 158)], "One-way functions producing fixed-length output"),
    ("SHA-256", [(3, 150, 152)], ""),
    ("MD5", [(3, 148, 149)], "Deprecated, collision vulnerabilities"),
    ("Digital Signatures", [(3, 159, 165)], "Provides authentication, integrity, non-repudiation"),
    ("PKI", [(3, 168, 180)], "Public Key Infrastructure"),
    ("Certificate Authority (CA)", [(3, 170, 175)], ""),
    ("Certificate Revocation List (CRL)", [(3, 176, 178)], ""),
    ("OCSP", [(3, 179, 180)], "Online Certificate Status Protocol"),
    ("Side-Channel Attacks", [(3, 185, 190)], ""),
    ("Physical Security", [(3, 195, 210)], ""),
    ("Mantrap", [(3, 198, 200)], ""),
    ("Bollards", [(3, 201, 203)], ""),
    ("CPTED", [(3, 204, 208)], "Crime Prevention Through Environmental Design"),

    # Domain 4: Communication and Network Security
    ("OSI Model", [(4, 8, 22)], "7 layers: Physical, Data Link, Network, Transport, Session, Presentation, Application"),
    ("TCP/IP Model", [(4, 23, 30)], ""),
    ("Firewall", [(4, 35, 52)], ""),
    ("Stateful Firewall", [(4, 40, 45)], "Tracks connection state"),
    ("Stateless Firewall", [(4, 38, 39)], ""),
    ("Next-Generation Firewall (NGFW)", [(4, 46, 52)], ""),
    ("Intrusion Detection System (IDS)", [(4, 55, 68)], "Monitors and alerts on suspicious activity"),
    ("Intrusion Prevention System (IPS)", [(4, 69, 78)], "Monitors and blocks suspicious activity"),
    ("Network IDS (NIDS)", [(4, 58, 62)], ""),
    ("Host IDS (HIDS)", [(4, 63, 67)], ""),
    ("VPN", [(4, 82, 98)], "Virtual Private Network"),
    ("IPSec", [(4, 85, 92)], ""),
    ("SSL/TLS VPN", [(4, 93, 98)], ""),
    ("Network Segmentation", [(4, 102, 112)], ""),
    ("VLAN", [(4, 105, 110)], "Virtual LAN"),
    ("DMZ", [(4, 115, 122)], "Demilitarized zone between trusted and untrusted networks"),
    ("NAC", [(4, 125, 132)], "Network Access Control"),
    ("802.1X", [(4, 128, 132)], "Port-based network access control"),
    ("DNS Security", [(4, 138, 145)], ""),
    ("DNSSEC", [(4, 140, 145)], ""),
    ("Wireless Security", [(4, 148, 162)], ""),
    ("WPA3", [(4, 155, 160)], "Latest wireless security protocol"),
    ("WPA2", [(4, 152, 154)], ""),

    # Domain 5: Identity and Access Management
    ("Authentication", [(5, 8, 32)], "Verifying identity"),
    ("Authorization", [(5, 33, 42)], "Granting access based on identity"),
    ("Accounting", [(5, 43, 48)], "Logging and tracking access"),
    ("Multi-Factor Authentication (MFA)", [(5, 15, 25)], "Something you know, have, are"),
    ("Single Sign-On (SSO)", [(5, 52, 62)], "One authentication for multiple systems"),
    ("Kerberos", [(5, 55, 60)], "Ticket-based authentication protocol"),
    ("SAML", [(5, 65, 72)], "Security Assertion Markup Language"),
    ("OAuth", [(5, 73, 78)], "Authorization framework"),
    ("OpenID Connect", [(5, 79, 82)], ""),
    ("LDAP", [(5, 85, 90)], "Lightweight Directory Access Protocol"),
    ("Active Directory", [(5, 91, 98)], "Microsoft directory service"),
    ("Access Control Models", [(5, 100, 118)], ""),
    ("DAC", [(5, 102, 106)], "Discretionary Access Control"),
    ("MAC", [(5, 107, 111)], "Mandatory Access Control"),
    ("RBAC", [(5, 112, 116)], "Role-Based Access Control"),
    ("ABAC", [(5, 117, 120)], "Attribute-Based Access Control"),
    ("Privileged Access Management (PAM)", [(5, 105, 108)], ""),

    # Domain 6: Security Assessment and Testing
    ("Vulnerability Assessment", [(6, 8, 22)], "Identifying security weaknesses"),
    ("Penetration Testing", [(6, 23, 42)], "Authorized simulated attack"),
    ("White Box Testing", [(6, 28, 32)], "Full knowledge of target"),
    ("Black Box Testing", [(6, 33, 37)], "No knowledge of target"),
    ("Gray Box Testing", [(6, 38, 42)], "Partial knowledge"),
    ("SAST", [(6, 48, 54)], "Static Application Security Testing"),
    ("DAST", [(6, 55, 60)], "Dynamic Application Security Testing"),
    ("Fuzzing", [(6, 62, 68)], "Sending malformed input to find vulnerabilities"),
    ("Code Review", [(6, 70, 76)], ""),
    ("Log Analysis", [(6, 78, 85)], ""),

    # Domain 7: Security Operations
    ("Incident Response", [(7, 10, 45)], ""),
    ("Incident Response Phases", [(7, 12, 30)], "Preparation, Detection, Containment, Eradication, Recovery, Lessons Learned"),
    ("SOAR", [(7, 35, 42)], "Security Orchestration, Automation, and Response"),
    ("SIEM", [(7, 48, 62)], "Security Information and Event Management"),
    ("Disaster Recovery", [(7, 68, 95)], ""),
    ("Hot Site", [(7, 75, 78)], "Fully operational backup site"),
    ("Warm Site", [(7, 79, 82)], "Partially equipped backup site"),
    ("Cold Site", [(7, 83, 86)], "Empty facility, longest recovery time"),
    ("Business Continuity Plan (BCP)", [(7, 88, 95)], ""),
    ("Backup Strategies", [(7, 100, 115)], ""),
    ("Full Backup", [(7, 102, 105)], ""),
    ("Incremental Backup", [(7, 106, 110)], "Only data changed since last backup"),
    ("Differential Backup", [(7, 111, 115)], "Data changed since last full backup"),
    ("Chain of Custody", [(7, 120, 128)], "Documentation of evidence handling"),
    ("Digital Forensics", [(7, 130, 150)], ""),
    ("Evidence Collection", [(7, 135, 142)], ""),
    ("Volatility Order", [(7, 143, 148)], "CPU registers, cache, RAM, disk"),
    ("Change Management", [(7, 155, 168)], ""),
    ("Configuration Management", [(7, 170, 180)], ""),
    ("Patch Management", [(7, 182, 192)], ""),

    # Domain 8: Software Development Security
    ("SDLC", [(8, 8, 25)], "Software Development Life Cycle"),
    ("Secure SDLC", [(8, 15, 25)], "Integrating security into each phase"),
    ("Agile Security", [(8, 28, 35)], ""),
    ("DevSecOps", [(8, 36, 45)], "Security integrated into DevOps"),
    ("OWASP Top 10", [(8, 50, 72)], "Top web application security risks"),
    ("SQL Injection", [(8, 52, 58)], "Injecting malicious SQL commands"),
    ("Cross-Site Scripting (XSS)", [(8, 59, 65)], "Injecting malicious scripts into web pages"),
    ("CSRF", [(8, 66, 70)], "Cross-Site Request Forgery"),
    ("Input Validation", [(8, 75, 82)], ""),
    ("Output Encoding", [(8, 83, 88)], ""),
    ("Secure Coding Practices", [(8, 90, 105)], ""),
    ("Buffer Overflow", [(8, 92, 98)], "Writing beyond allocated memory"),
    ("Memory Safety", [(8, 99, 105)], ""),
]

# Insert terms and references
for term, refs, notes in terms_data:
    cursor.execute("INSERT INTO terms (term, notes) VALUES (?, ?)", (term, notes))
    term_id = cursor.lastrowid

    for ref in refs:
        book_num, page_start, page_end = ref
        if page_start == page_end:
            page_end = None
        cursor.execute(
            "INSERT INTO page_references (term_id, book_number, page_start, page_end) VALUES (?, ?, ?, ?)",
            (term_id, book_num, page_start, page_end)
        )

conn.commit()

# Verify counts
cursor.execute("SELECT COUNT(*) FROM terms")
term_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM page_references")
ref_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM terms WHERE notes != ''")
notes_count = cursor.fetchone()[0]

print(f"Created CISSP demo database:")
print(f"  Terms: {term_count}")
print(f"  References: {ref_count}")
print(f"  Terms with notes: {notes_count}")
print(f"  Saved to: {demo_path}")

conn.close()
