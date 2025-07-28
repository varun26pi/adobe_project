#!/usr/bin/env python3
"""
Backend API Testing for PDF Document Intelligence System
Tests all backend endpoints systematically
"""

import requests
import json
import os
from pathlib import Path
import time

# Get backend URL from frontend .env file
def get_backend_url():
    frontend_env_path = Path("/app/frontend/.env")
    if frontend_env_path.exists():
        with open(frontend_env_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.split('=', 1)[1].strip()
                    return f"{base_url}/api"
    return "http://localhost:8001/api"  # fallback

BASE_URL = get_backend_url()
print(f"Testing backend at: {BASE_URL}")

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.uploaded_document_id = None
        self.test_results = {
            "root_endpoint": False,
            "pdf_upload": False,
            "document_retrieval": False,
            "persona_analysis": False,
            "error_handling": False
        }
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n=== Testing Root Endpoint ===")
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "PDF Document Intelligence API" in data["message"]:
                    print("✅ Root endpoint working correctly")
                    self.test_results["root_endpoint"] = True
                    return True
                else:
                    print("❌ Root endpoint response format incorrect")
                    return False
            else:
                print(f"❌ Root endpoint failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Root endpoint test failed: {e}")
            return False
    
    def test_pdf_upload(self):
        """Test PDF upload and structure extraction"""
        print("\n=== Testing PDF Upload and Structure Extraction ===")
        
        # Check if sample PDF exists
        sample_pdf_path = Path("/app/sample_research_paper.pdf")
        if not sample_pdf_path.exists():
            # Try alternative path
            sample_pdf_path = Path("/app/sample_paper.pdf")
            if not sample_pdf_path.exists():
                print("❌ No sample PDF found for testing")
                return False
        
        try:
            with open(sample_pdf_path, 'rb') as pdf_file:
                files = {'file': (sample_pdf_path.name, pdf_file, 'application/pdf')}
                response = self.session.post(f"{self.base_url}/upload-pdf", files=files)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Validate response structure
                required_fields = ['id', 'title', 'outline', 'filename', 'timestamp']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                # Check title extraction
                title = data.get('title', '')
                print(f"Extracted Title: '{title}'")
                if not title or title == "Untitled Document":
                    print("⚠️  Title extraction may need improvement")
                else:
                    print("✅ Title extracted successfully")
                
                # Check outline structure
                outline = data.get('outline', [])
                print(f"Number of headings extracted: {len(outline)}")
                
                if not outline:
                    print("❌ No headings extracted from PDF")
                    return False
                
                # Validate heading structure
                valid_headings = 0
                for i, heading in enumerate(outline[:5]):  # Check first 5 headings
                    print(f"  Heading {i+1}: {heading.get('level', 'N/A')} - '{heading.get('text', 'N/A')}' (Page {heading.get('page', 'N/A')})")
                    
                    if all(key in heading for key in ['level', 'text', 'page']):
                        if heading['level'] in ['H1', 'H2', 'H3'] and heading['text'] and isinstance(heading['page'], int):
                            valid_headings += 1
                
                if valid_headings > 0:
                    print(f"✅ PDF structure extraction working - {valid_headings} valid headings found")
                    self.uploaded_document_id = data['id']
                    self.test_results["pdf_upload"] = True
                    return True
                else:
                    print("❌ No valid headings found in extracted outline")
                    return False
            else:
                print(f"❌ PDF upload failed with status {response.status_code}")
                if response.text:
                    print(f"Error response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ PDF upload test failed: {e}")
            return False
    
    def test_document_retrieval(self):
        """Test document storage and retrieval"""
        print("\n=== Testing Document Storage and Retrieval ===")
        
        try:
            response = self.session.get(f"{self.base_url}/documents")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                documents = response.json()
                print(f"Number of documents retrieved: {len(documents)}")
                
                if not documents:
                    print("⚠️  No documents found in database")
                    return True  # Not necessarily an error if no docs uploaded yet
                
                # Validate document structure
                first_doc = documents[0]
                print(f"First document keys: {list(first_doc.keys())}")
                
                # Check UUID format (not ObjectID)
                doc_id = first_doc.get('id', '')
                if len(doc_id) == 36 and doc_id.count('-') == 4:  # UUID format
                    print("✅ Using UUIDs correctly (not ObjectID)")
                else:
                    print(f"❌ Document ID format incorrect: {doc_id}")
                    return False
                
                # Validate required fields
                required_fields = ['id', 'title', 'outline', 'filename', 'timestamp']
                if all(field in first_doc for field in required_fields):
                    print("✅ Document retrieval working correctly")
                    self.test_results["document_retrieval"] = True
                    return True
                else:
                    missing = [f for f in required_fields if f not in first_doc]
                    print(f"❌ Missing fields in retrieved document: {missing}")
                    return False
            else:
                print(f"❌ Document retrieval failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Document retrieval test failed: {e}")
            return False
    
    def test_persona_analysis(self):
        """Test persona-driven document analysis"""
        print("\n=== Testing Persona Analysis ===")
        
        if not self.uploaded_document_id:
            print("❌ No uploaded document ID available for persona analysis")
            return False
        
        # Test data
        test_persona = "PhD Researcher in Computer Science"
        test_job = "Prepare literature review on deep learning approaches"
        
        payload = {
            "persona": test_persona,
            "job_to_be_done": test_job,
            "document_ids": [self.uploaded_document_id]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/analyze-persona",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Validate response structure
                required_fields = ['id', 'persona', 'job_to_be_done', 'input_documents', 
                                 'processing_timestamp', 'extracted_sections', 'sub_section_analysis']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                # Check persona and job match
                if data['persona'] != test_persona or data['job_to_be_done'] != test_job:
                    print("❌ Persona or job-to-be-done not preserved correctly")
                    return False
                
                # Check extracted sections
                extracted_sections = data.get('extracted_sections', [])
                print(f"Number of extracted sections: {len(extracted_sections)}")
                
                if not extracted_sections:
                    print("❌ No sections extracted in persona analysis")
                    return False
                
                # Validate section structure
                first_section = extracted_sections[0]
                section_fields = ['document', 'page_number', 'section_title', 'importance_rank']
                if all(field in first_section for field in section_fields):
                    print(f"✅ Section structure valid: Rank {first_section['importance_rank']} - '{first_section['section_title']}'")
                else:
                    print("❌ Section structure invalid")
                    return False
                
                # Check sub-section analysis
                sub_sections = data.get('sub_section_analysis', [])
                print(f"Number of sub-sections analyzed: {len(sub_sections)}")
                
                if sub_sections:
                    first_sub = sub_sections[0]
                    if 'refined_text' in first_sub and test_persona in first_sub['refined_text']:
                        print("✅ Sub-section analysis includes persona context")
                    else:
                        print("⚠️  Sub-section analysis may not include proper persona context")
                
                print("✅ Persona analysis working correctly")
                self.test_results["persona_analysis"] = True
                return True
            else:
                print(f"❌ Persona analysis failed with status {response.status_code}")
                if response.text:
                    print(f"Error response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Persona analysis test failed: {e}")
            return False
    
    def test_error_handling(self):
        """Test API error handling"""
        print("\n=== Testing Error Handling ===")
        
        try:
            # Test 1: Upload non-PDF file
            print("Testing non-PDF file upload...")
            fake_file = {'file': ('test.txt', b'This is not a PDF', 'text/plain')}
            response = self.session.post(f"{self.base_url}/upload-pdf", files=fake_file)
            
            if response.status_code == 400:
                print("✅ Correctly rejects non-PDF files")
            else:
                print(f"⚠️  Non-PDF rejection status: {response.status_code}")
            
            # Test 2: Persona analysis with invalid document ID
            print("Testing persona analysis with invalid document ID...")
            invalid_payload = {
                "persona": "Test Persona",
                "job_to_be_done": "Test Job",
                "document_ids": ["invalid-uuid-12345"]
            }
            
            response = self.session.post(
                f"{self.base_url}/analyze-persona",
                json=invalid_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [400, 404]:
                print("✅ Correctly handles invalid document IDs")
            else:
                print(f"⚠️  Invalid document ID handling status: {response.status_code}")
            
            self.test_results["error_handling"] = True
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests")
        print("=" * 50)
        
        # Test sequence
        tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("PDF Upload & Structure Extraction", self.test_pdf_upload),
            ("Document Storage & Retrieval", self.test_document_retrieval),
            ("Persona Analysis", self.test_persona_analysis),
            ("Error Handling", self.test_error_handling)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
            
            # Small delay between tests
            time.sleep(1)
        
        # Summary
        print("\n" + "="*50)
        print("🏁 TEST SUMMARY")
        print("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{test_name}: {status}")
            if passed_test:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All backend tests PASSED!")
        else:
            print(f"⚠️  {total - passed} test(s) FAILED")
        
        return results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()