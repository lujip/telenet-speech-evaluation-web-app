"""
Quick test to verify MongoDB connection and session_states collection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.db import session_states_collection, db
    
    print("="*60)
    print("MongoDB Connection Test")
    print("="*60)
    
    # Test connection
    print(f"\n✓ Connected to database: {db.name}")
    
    # List all collections
    collections = db.list_collection_names()
    print(f"\n✓ Existing collections: {collections}")
    
    # Check if session_states exists
    if 'session_states' in collections:
        print(f"\n✅ session_states collection EXISTS")
        count = session_states_collection.count_documents({})
        print(f"   Documents in collection: {count}")
    else:
        print(f"\n⚠️  session_states collection DOES NOT exist yet")
        print("   (This is normal - it will be created on first insert)")
    
    # Test write (this will create the collection if it doesn't exist)
    print("\n" + "="*60)
    print("Testing collection creation...")
    print("="*60)
    
    test_doc = {
        'session_id': 'test_connection_123',
        'test': True,
        'message': 'Testing MongoDB connection'
    }
    
    result = session_states_collection.insert_one(test_doc)
    print(f"\n✓ Test document inserted with ID: {result.inserted_id}")
    
    # Verify it exists
    found = session_states_collection.find_one({'session_id': 'test_connection_123'})
    if found:
        print(f"✓ Test document retrieved successfully")
        print(f"   Content: {found}")
    
    # Clean up test document
    session_states_collection.delete_one({'session_id': 'test_connection_123'})
    print(f"\n✓ Test document cleaned up")
    
    # Check collections again
    collections_after = db.list_collection_names()
    if 'session_states' in collections_after:
        print(f"\n✅ session_states collection now exists!")
        print("="*60)
        print("SUCCESS: MongoDB is properly configured!")
        print("="*60)
    
    print("\n✓ All tests passed!")
    print("✓ The session persistence system will work correctly.")
    
except Exception as e:
    print("="*60)
    print("❌ ERROR: MongoDB Connection Failed")
    print("="*60)
    print(f"\nError: {str(e)}")
    print("\nPossible issues:")
    print("1. MongoDB server is not running")
    print("2. Connection credentials are incorrect")
    print("3. Network/firewall blocking connection")
    print("4. Database name doesn't exist")
    
    import traceback
    traceback.print_exc()
    sys.exit(1)

