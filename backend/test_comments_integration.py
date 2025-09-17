#!/usr/bin/env python3
"""
Test script to verify comments integration with applicant data structure
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_comments_integration():
    """Test the integrated comments functionality"""
    print("🧪 Testing Comments Integration with Applicant Data Structure")
    print("=" * 60)
    
    # First, let's get the list of applicants
    print("1. Getting list of applicants...")
    try:
        response = requests.get(f"{BASE_URL}/admin/applicants")
        if response.status_code == 200:
            data = response.json()
            applicants = data.get("applicants", [])
            print(f"✅ Found {len(applicants)} applicants")
            
            if not applicants:
                print("❌ No applicants found. Create an applicant first.")
                return
            
            # Use the first applicant for testing
            test_applicant = applicants[0]
            applicant_id = test_applicant.get("id")
            applicant_name = test_applicant.get("applicant_info", {}).get("fullName", "Unknown")
            
            print(f"📋 Testing with applicant: {applicant_name} (ID: {applicant_id})")
            
        else:
            print(f"❌ Failed to get applicants: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting applicants: {e}")
        return
    
    # Test 1: Get existing comments
    print("\n2. Getting existing comments...")
    try:
        response = requests.get(f"{BASE_URL}/admin/applicants/{applicant_id}/comments")
        if response.status_code == 200:
            data = response.json()
            existing_comments = data.get("comments", [])
            print(f"✅ Found {len(existing_comments)} existing comments")
            for i, comment in enumerate(existing_comments):
                print(f"   Comment {i+1}: {comment.get('comment')[:50]}...")
        else:
            print(f"❌ Failed to get comments: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting comments: {e}")
        return
    
    # Test 2: Add a new comment
    print("\n3. Adding a new comment...")
    test_comment = {
        "comment": "This is a test comment added via integration test.",
        "evaluator": "Test Admin"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/applicants/{applicant_id}/comments",
            json=test_comment,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                new_comment = data.get("comment")
                print(f"✅ Comment added successfully: {new_comment.get('id')}")
                comment_id_to_delete = new_comment.get('id')
            else:
                print(f"❌ Failed to add comment: {data.get('message')}")
                return
        else:
            print(f"❌ Failed to add comment: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error adding comment: {e}")
        return
    
    # Test 3: Verify comment was added to applicants.json
    print("\n4. Verifying comment was stored in applicants.json...")
    try:
        response = requests.get(f"{BASE_URL}/admin/applicants/{applicant_id}/comments")
        if response.status_code == 200:
            data = response.json()
            updated_comments = data.get("comments", [])
            print(f"✅ Now have {len(updated_comments)} comments total")
            
            # Find our test comment
            test_comment_found = False
            for comment in updated_comments:
                if comment.get("comment") == test_comment["comment"]:
                    test_comment_found = True
                    print(f"✅ Test comment found: {comment.get('id')}")
                    break
            
            if not test_comment_found:
                print("❌ Test comment not found in updated list")
        else:
            print(f"❌ Failed to verify comments: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verifying comments: {e}")
    
    # Test 4: Delete the test comment
    print("\n5. Deleting the test comment...")
    try:
        response = requests.delete(f"{BASE_URL}/admin/applicants/{applicant_id}/comments/{comment_id_to_delete}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Comment deleted successfully")
            else:
                print(f"❌ Failed to delete comment: {data.get('message')}")
        else:
            print(f"❌ Failed to delete comment: {response.status_code}")
    except Exception as e:
        print(f"❌ Error deleting comment: {e}")
    
    # Test 5: Verify comment was deleted
    print("\n6. Verifying comment was deleted...")
    try:
        response = requests.get(f"{BASE_URL}/admin/applicants/{applicant_id}/comments")
        if response.status_code == 200:
            data = response.json()
            final_comments = data.get("comments", [])
            print(f"✅ Final comment count: {len(final_comments)}")
            
            # Make sure our test comment is gone
            test_comment_found = False
            for comment in final_comments:
                if comment.get("id") == comment_id_to_delete:
                    test_comment_found = True
                    break
            
            if not test_comment_found:
                print("✅ Test comment successfully deleted")
            else:
                print("❌ Test comment still exists after deletion")
        else:
            print(f"❌ Failed to verify deletion: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verifying deletion: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 Comments integration test completed!")

if __name__ == "__main__":
    test_comments_integration() 