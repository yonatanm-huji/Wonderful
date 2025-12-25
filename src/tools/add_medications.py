"""
Add 3 additional medications to the database that have known interactions
with our existing medications (Aspirin, Metformin, Semaglutide, Ibuprofen, Amoxicillin)
"""

import sqlite3

def add_interacting_medications():
    """Add 3 medications that interact with our existing ones"""
    
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()
    
    # New medications with interactions
    new_medications = [
        (
            'Warfarin',
            'Warfarin Sodium',
            'Warfarin Sodium',
            'Tablet',
            '1mg, 2mg, 2.5mg, 3mg, 4mg, 5mg, 6mg, 7.5mg, 10mg',
            'Anticoagulant (blood thinner) used to prevent blood clots, reduce risk of stroke, and treat conditions like deep vein thrombosis and pulmonary embolism.',
            1,  # Requires prescription
            95,  # Stock quantity
            'Aspirin (increased bleeding risk), Ibuprofen (increased bleeding risk), NSAIDs, Antibiotics (especially Amoxicillin), Vitamin K-rich foods',
            'Easy bruising, bleeding gums, nosebleeds, blood in urine or stool, unusual bleeding, purple skin discoloration',
            'Active bleeding, severe liver disease, pregnancy, recent surgery, uncontrolled high blood pressure, bleeding disorders'
        ),
        (
            'Glyburide',
            'Glyburide',
            'Glyburide',
            'Tablet',
            '1.25mg, 2.5mg, 5mg',
            'Sulfonylurea medication used to treat type 2 diabetes by stimulating the pancreas to release insulin. Often used in combination with Metformin.',
            1,  # Requires prescription
            110,
            'Metformin (enhanced blood sugar lowering effect), Aspirin (may enhance effects), Alcohol (increases risk of low blood sugar), Beta-blockers',
            'Low blood sugar (hypoglycemia), dizziness, nausea, weight gain, upset stomach, skin rash',
            'Type 1 diabetes, diabetic ketoacidosis, severe kidney disease, severe liver disease, G6PD deficiency, sulfa drug allergy'
        ),
        (
            'Probenecid',
            'Probenecid',
            'Probenecid',
            'Tablet',
            '500mg',
            'Used to treat gout and gouty arthritis by helping the kidneys remove uric acid from the body. Also used to increase blood levels of certain antibiotics like Amoxicillin.',
            1,  # Requires prescription
            75,
            'Amoxicillin (increases Amoxicillin blood levels - this is sometimes intentional), Aspirin (reduces effectiveness), Metformin, NSAIDs',
            'Headache, loss of appetite, nausea, vomiting, sore gums, frequent urination',
            'Kidney stones, blood disorders, acute gout attack (during active flare), children under 2 years, severe kidney disease'
        )
    ]
    
    # Insert the new medications
    cursor.executemany('''
    INSERT INTO medications (name, generic_name, active_ingredients, dosage_forms, 
                           common_dosages, description, requires_prescription, 
                           stock_quantity, interactions, side_effects, contraindications)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', new_medications)
    
    print(f"✅ Added {len(new_medications)} new medications!")
    
    # Add some prescriptions for these new medications
    new_prescriptions = [
        (1, 6, '5mg', 'Once daily', '2024-01-10', 2, 'Dr. Cohen'),  # Jalen Brunson - Warfarin
        (4, 7, '2.5mg', 'Once daily', '2024-02-15', 3, 'Dr. Sharon'),  # Josh Hart - Glyburide
        (8, 8, '500mg', 'Twice daily', '2024-03-01', 4, 'Dr. Levi')  # Precious Achiuwa - Probenecid
    ]
    
    cursor.executemany('''
    INSERT INTO prescriptions (user_id, medication_id, dosage, frequency, 
                              prescribed_date, refills_remaining, prescribing_doctor)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', new_prescriptions)
    
    print(f"✅ Added {len(new_prescriptions)} new prescriptions!")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*80)
    print("NEW MEDICATIONS AND KEY INTERACTIONS:")
    print("="*80)
    print("\n1. WARFARIN (Blood Thinner)")
    print("   ⚠️  MAJOR INTERACTION with Aspirin → Increased bleeding risk")
    print("   ⚠️  MAJOR INTERACTION with Ibuprofen → Increased bleeding risk")
    print("   ⚠️  INTERACTION with Amoxicillin → May increase anticoagulant effect")
    print("   Patient: Jalen Brunson (has Penicillin allergy - careful with Amoxicillin!)")
    
    print("\n2. GLYBURIDE (Diabetes medication)")
    print("   ⚠️  INTERACTION with Metformin → Enhanced blood sugar lowering")
    print("   ⚠️  INTERACTION with Aspirin → May enhance hypoglycemic effects")
    print("   Patient: Josh Hart")
    
    print("\n3. PROBENECID (Gout medication)")
    print("   ⚠️  INTERACTION with Amoxicillin → Increases Amoxicillin blood levels")
    print("   ⚠️  INTERACTION with Aspirin → Reduces Probenecid effectiveness")
    print("   ⚠️  INTERACTION with Metformin → May affect Metformin clearance")
    print("   Patient: Precious Achiuwa")
    
    print("\n" + "="*80)
    print("TESTING SCENARIOS NOW AVAILABLE:")
    print("="*80)
    print("✓ 'I'm on Warfarin, can I take Aspirin?' → Should warn about bleeding risk")
    print("✓ 'Jalen Brunson needs Amoxicillin' → Should warn about Penicillin allergy!")
    print("✓ 'Can Josh Hart take Metformin with Glyburide?' → Should mention interaction")
    print("✓ 'Does Probenecid interact with my antibiotics?' → Should explain the interaction")


def view_all_medications():
    """Display all medications now in database"""
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("ALL MEDICATIONS IN DATABASE (8 total)")
    print("="*80)
    
    cursor.execute('''
        SELECT medication_id, name, requires_prescription, stock_quantity, 
               active_ingredients
        FROM medications
        ORDER BY medication_id
    ''')
    
    meds = cursor.fetchall()
    for med in meds:
        rx_status = "Rx Required" if med[2] == 1 else "OTC"
        print(f"\n{med[0]}. {med[1]}")
        print(f"   Status: {rx_status} | Stock: {med[3]} units")
        print(f"   Active: {med[4]}")
    
    conn.close()


def view_interaction_matrix():
    """Show which medications interact with each other"""
    print("\n" + "="*80)
    print("INTERACTION MATRIX")
    print("="*80)
    print("""
    Original 5 Medications:
    1. Aspirin
    2. Metformin  
    3. Semaglutide
    4. Ibuprofen
    5. Amoxicillin
    
    New 3 Medications (with interactions):
    6. Warfarin      → Interacts with: Aspirin ⚠️, Ibuprofen ⚠️, Amoxicillin
    7. Glyburide     → Interacts with: Metformin ⚠️, Aspirin
    8. Probenecid    → Interacts with: Amoxicillin ⚠️, Aspirin, Metformin
    
    ⚠️ = Major/clinically significant interaction
    """)


if __name__ == "__main__":
    print("🏥 Adding Interacting Medications to Pharmacy Database")
    print("="*80)
    
    add_interacting_medications()
    view_all_medications()
    view_interaction_matrix()
    
    print("\n✅ Database updated! Now you have realistic interaction scenarios to test.")
    print("\n💡 Test the tools with:")
    print("   python src/tools/medication_tools.py")
