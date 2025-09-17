#!/usr/bin/env python3
"""
Test script for the audio routes
"""

import os
import sys
import requests
import json

def test_speak_audio_endpoint():
    """Test the speak-audio endpoint"""
    print("Testing /speak-audio endpoint...")
    
    # Test with a valid audio ID
    url = "http://localhost:5000/speak-audio"
    data = {"id": "lq1"}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ /speak-audio endpoint working correctly")
            return True
        else:
            print("❌ /speak-audio endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing /speak-audio endpoint: {e}")
        return False

def test_listening_audio_route():
    """Test the listening-questions audio route"""
    print("\nTesting /listening-questions route...")
    
    # Test with a valid audio file
    url = "http://localhost:5000/audio/listening-questions/lq1.wav"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            print("✅ /listening-questions route working correctly")
            return True
        else:
            print("❌ /listening-questions route failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing /listening-questions route: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting audio route tests...\n")
    
    # Test speak-audio endpoint
    speak_audio_working = test_speak_audio_endpoint()
    
    # Test listening-questions route
    listening_route_working = test_listening_audio_route()
    
    print("\n" + "="*50)
    print("Test Results:")
    print(f"Speak Audio Endpoint: {'✅ PASS' if speak_audio_working else '❌ FAIL'}")
    print(f"Listening Questions Route: {'✅ PASS' if listening_route_working else '❌ FAIL'}")
    
    if speak_audio_working and listening_route_working:
        print("\n🎉 All tests passed! Audio routes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the backend server and routes.")

if __name__ == "__main__":
    main() 