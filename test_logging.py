#!/usr/bin/env python3
"""
Test script to verify LLM logging functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:3002"

def test_logging():
    """Test the logging functionality by making API calls"""
    print("🧪 Testing LLM Logging Functionality")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    # Test 2: Document analysis (Legal Extractor)
    print("\n2. Testing Legal Extractor logging...")
    test_text = """
    Brown v. Board of Education of Topeka, 347 U.S. 483 (1954)
    
    SUPREME COURT OF THE UNITED STATES
    
    Facts:
    The case consolidated several legal challenges to racial segregation in public schools.
    
    Issue:
    Does the segregation of children in public schools solely on the basis of race violate the Equal Protection Clause?
    
    Holding:
    The Supreme Court held unanimously that racial segregation in public schools violates the Equal Protection Clause.
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-document",
            json={"text": test_text},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("   ✅ Legal Extractor call successful")
            data = response.json()
            print(f"   📊 Extracted fields: {list(data.get('data', {}).get('extracted_fields', {}).keys())}")
        else:
            print(f"   ❌ Legal Extractor failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Legal Extractor request failed: {e}")
    
    # Test 3: Brief generation
    print("\n3. Testing Brief Generator logging...")
    extracted_data = {
        "case_name": "Brown v. Board of Education",
        "court": "Supreme Court of the United States",
        "date": "1954",
        "facts": "Case about racial segregation in public schools",
        "legal_issues": ["Equal Protection Clause"],
        "holdings": ["Segregation violates Equal Protection"],
        "reasoning": ["Education is fundamental right"],
        "citations": ["347 U.S. 483"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate-brief",
            json={"extracted_data": extracted_data},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("   ✅ Brief Generator call successful")
            data = response.json()
            brief = data.get('data', {}).get('brief', {})
            print(f"   📊 Brief fields: {list(brief.keys())}")
        else:
            print(f"   ❌ Brief Generator failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Brief Generator request failed: {e}")
    
    # Test 4: Citation normalization
    print("\n4. Testing Citation Normalizer logging...")
    citations = ["347 U.S. 483", "Plessy v. Ferguson, 163 U.S. 537"]
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/normalize-citations",
            json={"citations": citations, "format": "bluebook"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("   ✅ Citation Normalizer call successful")
            data = response.json()
            normalized = data.get('data', {}).get('normalized_citations', [])
            print(f"   📊 Normalized citations: {len(normalized)}")
        else:
            print(f"   ❌ Citation Normalizer failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Citation Normalizer request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Logging test completed!")
    print("📝 Check the logs/ directory for the timestamped log file")
    print("💡 The log file will contain detailed LLM input/output for each agent")

if __name__ == "__main__":
    test_logging()
