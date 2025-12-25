"""
Update Probenecid to have low inventory (15 units)
This allows testing of the low stock warning feature
"""

import sqlite3

def update_inventory():
    """Update Probenecid to have low stock"""
    
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()
    
    # Update Probenecid stock to 15 units
    cursor.execute('''
        UPDATE medications
        SET stock_quantity = 15
        WHERE name = 'Probenecid'
    ''')
    
    conn.commit()
    
    # Verify the update
    cursor.execute('''
        SELECT name, stock_quantity
        FROM medications
        WHERE name = 'Probenecid'
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print("="*60)
        print("INVENTORY UPDATE SUCCESSFUL")
        print("="*60)
        print(f"Medication: {result[0]}")
        print(f"New Stock Quantity: {result[1]} units")
        print(f"Status: Low stock - limited availability")
        print("="*60)
        print("\nTest Query:")
        print('  "Do you have Probenecid in stock?"')
        print("\nExpected Response:")
        print('  "Yes, but low stock - limited availability (15 units)"')
    else:
        print("ERROR: Probenecid not found in database")


if __name__ == "__main__":
    update_inventory()
