"""
Database initialization script for Pharmacy AI Agent
Creates SQLite database with 10 users and 5 medications
"""

import sqlite3
import json
from datetime import datetime

def create_database():
    """Create the pharmacy database with users and medications tables"""
    
    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        date_of_birth TEXT,
        allergies TEXT,
        current_medications TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create Medications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        medication_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        generic_name TEXT,
        active_ingredients TEXT NOT NULL,
        dosage_forms TEXT,
        common_dosages TEXT,
        description TEXT,
        requires_prescription INTEGER DEFAULT 1,
        stock_quantity INTEGER DEFAULT 0,
        interactions TEXT,
        side_effects TEXT,
        contraindications TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create Prescriptions table (links users to medications)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prescriptions (
        prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        medication_id INTEGER NOT NULL,
        dosage TEXT NOT NULL,
        frequency TEXT NOT NULL,
        prescribed_date TEXT,
        refills_remaining INTEGER DEFAULT 0,
        prescribing_doctor TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (medication_id) REFERENCES medications (medication_id)
    )
    ''')
    
    print("✅ Tables created successfully!")
    
    # Insert 10 fake users (Knicks players)
    users_data = [
        ('Jalen Brunson', 'jalen.brunson@email.com', '212-1234567', '1996-08-31', 'Penicillin', 'None'),
        ('Karl-Anthony Towns', 'kat@email.com', '212-2345678', '1995-11-15', 'None', 'Aspirin'),
        ('Mikal Bridges', 'mikal.bridges@email.com', '212-3456789', '1996-08-30', 'Sulfa drugs', 'Semaglutide'),
        ('Josh Hart', 'josh.hart@email.com', '212-4567890', '1995-03-06', 'None', 'None'),
        ('OG Anunoby', 'og.anunoby@email.com', '212-5678901', '1997-07-17', 'Latex', 'Metformin'),
        ('Deuce McBride', 'deuce.mcbride@email.com', '212-6789012', '2000-09-25', 'Shellfish', 'None'),
        ('Mitchell Robinson', 'mitch.robinson@email.com', '212-7890123', '1998-04-01', 'None', 'Atorvastatin'),
        ('Precious Achiuwa', 'precious.achiuwa@email.com', '212-8901234', '1999-09-19', 'Iodine', 'None'),
        ('Miles McBride', 'miles.mcbride@email.com', '212-9012345', '2000-09-08', 'None', 'Omeprazole'),
        ('Jericho Sims', 'jericho.sims@email.com', '212-0123456', '1998-10-20', 'Peanuts', 'Levothyroxine')
    ]
    
    cursor.executemany('''
    INSERT INTO users (name, email, phone, date_of_birth, allergies, current_medications)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', users_data)
    
    print(f"✅ Inserted {len(users_data)} users!")
    
    # Insert 5 medications with detailed information
    medications_data = [
        (
            'Aspirin',
            'Acetylsalicylic Acid',
            'Acetylsalicylic Acid',
            'Tablet, Chewable Tablet',
            '81mg (low-dose), 325mg, 500mg',
            'Pain reliever and anti-inflammatory medication used to reduce fever, pain, and inflammation. Also used in low doses to prevent heart attacks and strokes.',
            0,  # No prescription required
            150,  # Stock quantity
            'Blood thinners (Warfarin, Heparin), NSAIDs (Ibuprofen), Corticosteroids, Alcohol',
            'Stomach upset, heartburn, nausea, increased bleeding risk, ringing in ears (high doses)',
            'Bleeding disorders, stomach ulcers, severe kidney disease, children with viral infections (Reye syndrome risk), third trimester pregnancy'
        ),
        (
            'Metformin',
            'Metformin Hydrochloride',
            'Metformin Hydrochloride',
            'Tablet, Extended-Release Tablet',
            '500mg, 850mg, 1000mg',
            'Oral diabetes medication that helps control blood sugar levels in people with type 2 diabetes. It decreases glucose production in the liver and improves insulin sensitivity.',
            1,  # Requires prescription
            200,
            'Alcohol (increases risk of lactic acidosis), Iodinated contrast dyes, Carbonic anhydrase inhibitors',
            'Nausea, vomiting, diarrhea, stomach upset, metallic taste, vitamin B12 deficiency (long-term use)',
            'Severe kidney disease, metabolic acidosis, dehydration, heart failure, liver disease, excessive alcohol use'
        ),
        (
            'Semaglutide',
            'Semaglutide',
            'Semaglutide',
            'Injection (subcutaneous), Tablet',
            '0.25mg, 0.5mg, 1mg, 2mg (injection); 3mg, 7mg, 14mg (oral)',
            'GLP-1 receptor agonist used to improve blood sugar control in adults with type 2 diabetes and for chronic weight management. Also reduces risk of cardiovascular events in patients with type 2 diabetes and heart disease.',
            1,  # Requires prescription
            180,
            'Insulin, Sulfonylureas (increased risk of hypoglycemia), Oral medications (delayed gastric emptying may affect absorption)',
            'Nausea, vomiting, diarrhea, abdominal pain, constipation, decreased appetite, injection site reactions',
            'Personal or family history of medullary thyroid carcinoma, Multiple Endocrine Neoplasia syndrome type 2, severe gastrointestinal disease, diabetic retinopathy complications, pregnancy'
        ),
        (
            'Ibuprofen',
            'Ibuprofen',
            'Ibuprofen',
            'Tablet, Capsule, Liquid Gel, Suspension',
            '200mg, 400mg, 600mg, 800mg',
            'Nonsteroidal anti-inflammatory drug (NSAID) used to reduce fever, pain, and inflammation. Common for headaches, dental pain, menstrual cramps, muscle aches, and arthritis.',
            0,  # No prescription required for lower doses
            250,
            'Aspirin, Blood thinners (Warfarin), Other NSAIDs, Corticosteroids, ACE inhibitors, Lithium, Methotrexate',
            'Stomach upset, nausea, heartburn, dizziness, increased blood pressure, increased bleeding risk',
            'Active stomach ulcers, severe heart disease, history of stroke, severe kidney or liver disease, third trimester pregnancy, aspirin allergy'
        ),
        (
            'Amoxicillin',
            'Amoxicillin',
            'Amoxicillin',
            'Capsule, Tablet, Chewable Tablet, Suspension',
            '250mg, 500mg, 875mg',
            'Penicillin-type antibiotic used to treat bacterial infections including respiratory infections, ear infections, urinary tract infections, and skin infections.',
            1,  # Requires prescription
            120,
            'Oral contraceptives (may reduce effectiveness), Allopurinol (increases rash risk), Probenecid, Methotrexate',
            'Nausea, vomiting, diarrhea, rash, yeast infections',
            'Penicillin allergy, severe kidney disease, mononucleosis, history of allergic reactions to cephalosporins'
        )
    ]
    
    cursor.executemany('''
    INSERT INTO medications (name, generic_name, active_ingredients, dosage_forms, 
                           common_dosages, description, requires_prescription, 
                           stock_quantity, interactions, side_effects, contraindications)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', medications_data)
    
    print(f"✅ Inserted {len(medications_data)} medications!")
    
    # Insert some sample prescriptions
    prescriptions_data = [
        (2, 1, '81mg', 'Once daily', '2024-01-15', 3, 'Dr. Cohen'),  # Karl-Anthony Towns - Aspirin
        (3, 3, '1mg', 'Once weekly', '2024-02-20', 2, 'Dr. Levi'),   # Mikal Bridges - Semaglutide
        (5, 2, '1000mg', 'Twice daily', '2024-03-10', 5, 'Dr. Sharon'),  # OG Anunoby - Metformin
        (7, 3, '0.5mg', 'Once weekly', '2023-12-05', 1, 'Dr. Levi'),   # Mitchell Robinson - Semaglutide
        (9, 1, '325mg', 'As needed', '2024-01-25', 2, 'Dr. Cohen'),  # Miles McBride - Aspirin
        (10, 2, '500mg', 'Twice daily', '2024-02-14', 4, 'Dr. Sharon')  # Jericho Sims - Metformin
    ]
    
    cursor.executemany('''
    INSERT INTO prescriptions (user_id, medication_id, dosage, frequency, 
                              prescribed_date, refills_remaining, prescribing_doctor)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', prescriptions_data)
    
    print(f"✅ Inserted {len(prescriptions_data)} prescriptions!")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("\n🎉 Database created successfully!")
    print("📁 Database file: pharmacy.db")
    print("\n📊 Database Summary:")
    print(f"   - {len(users_data)} users")
    print(f"   - {len(medications_data)} medications")
    print(f"   - {len(prescriptions_data)} prescriptions")


def view_database():
    """Display the contents of the database"""
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("USERS IN DATABASE")
    print("="*60)
    cursor.execute('SELECT user_id, name, email, allergies FROM users')
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]} | Name: {user[1]} | Email: {user[2]} | Allergies: {user[3]}")
    
    print("\n" + "="*60)
    print("MEDICATIONS IN DATABASE")
    print("="*60)
    cursor.execute('SELECT medication_id, name, requires_prescription, stock_quantity FROM medications')
    meds = cursor.fetchall()
    for med in meds:
        rx_status = "Prescription Required" if med[2] == 1 else "Over-the-Counter"
        print(f"ID: {med[0]} | Name: {med[1]} | {rx_status} | Stock: {med[3]} units")
    
    print("\n" + "="*60)
    print("PRESCRIPTIONS IN DATABASE")
    print("="*60)
    cursor.execute('''
        SELECT p.prescription_id, u.name, m.name, p.dosage, p.frequency
        FROM prescriptions p
        JOIN users u ON p.user_id = u.user_id
        JOIN medications m ON p.medication_id = m.medication_id
    ''')
    prescriptions = cursor.fetchall()
    for rx in prescriptions:
        print(f"ID: {rx[0]} | Patient: {rx[1]} | Medication: {rx[2]} | Dosage: {rx[3]} | Frequency: {rx[4]}")
    
    conn.close()


if __name__ == "__main__":
    print("🏥 Pharmacy AI Agent - Database Setup")
    print("="*60)
    
    # Create and populate the database
    create_database()
    
    # Display the contents
    view_database()
    
    print("\n✅ Setup complete! You can now use pharmacy.db in your application.")
