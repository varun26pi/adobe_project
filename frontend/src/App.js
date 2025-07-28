import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [documents, setDocuments] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [persona, setPersona] = useState("");
  const [jobToBeDone, setJobToBeDone] = useState("");
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState("upload");

  // Load documents and analyses on component mount
  useEffect(() => {
    loadDocuments();
    loadAnalyses();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error("Error loading documents:", error);
    }
  };

  const loadAnalyses = async () => {
    try {
      const response = await axios.get(`${API}/analyses`);
      setAnalyses(response.data);
    } catch (error) {
      console.error("Error loading analyses:", error);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      await axios.post(`${API}/upload-pdf`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      
      setSelectedFile(null);
      loadDocuments();
      alert("PDF uploaded and processed successfully!");
    } catch (error) {
      console.error("Error uploading PDF:", error);
      alert("Error uploading PDF. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handlePersonaAnalysis = async () => {
    if (!persona || !jobToBeDone || selectedDocs.length === 0) {
      alert("Please fill in all fields and select at least one document.");
      return;
    }

    setAnalyzing(true);
    try {
      await axios.post(`${API}/analyze-persona`, {
        persona,
        job_to_be_done: jobToBeDone,
        document_ids: selectedDocs,
      });

      setPersona("");
      setJobToBeDone("");
      setSelectedDocs([]);
      loadAnalyses();
      alert("Persona analysis completed successfully!");
    } catch (error) {
      console.error("Error analyzing persona:", error);
      alert("Error analyzing documents. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const toggleDocSelection = (docId) => {
    setSelectedDocs(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            🔗 Connecting the Dots
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Rethink Reading. Rediscover Knowledge. Transform your PDFs into intelligent, 
            interactive experiences that understand structure and connect ideas.
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg p-1 shadow-lg">
            <button
              onClick={() => setActiveTab("upload")}
              className={`px-6 py-3 rounded-md font-medium transition-all ${
                activeTab === "upload"
                  ? "bg-blue-500 text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              📄 Round 1A: Extract Structure
            </button>
            <button
              onClick={() => setActiveTab("analyze")}
              className={`px-6 py-3 rounded-md font-medium transition-all ${
                activeTab === "analyze"
                  ? "bg-blue-500 text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              🧠 Round 1B: Persona Intelligence
            </button>
            <button
              onClick={() => setActiveTab("results")}
              className={`px-6 py-3 rounded-md font-medium transition-all ${
                activeTab === "results"
                  ? "bg-blue-500 text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              📊 View Results
            </button>
          </div>
        </div>

        {/* Upload Tab */}
        {activeTab === "upload" && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
                📄 Document Structure Extraction
              </h2>
              <p className="text-gray-600 mb-8 text-center">
                Upload your PDF to extract its title and hierarchical structure (H1, H2, H3 headings)
              </p>

              {/* File Upload */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  className="hidden"
                  id="pdf-upload"
                />
                <label
                  htmlFor="pdf-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <span className="text-3xl">📁</span>
                  </div>
                  <span className="text-lg font-medium text-gray-700">
                    {selectedFile ? selectedFile.name : "Choose PDF file"}
                  </span>
                  <span className="text-sm text-gray-500 mt-2">
                    Maximum 50 pages supported
                  </span>
                </label>
              </div>

              <button
                onClick={handleFileUpload}
                disabled={!selectedFile || uploading}
                className={`w-full py-4 rounded-lg font-semibold text-lg transition-all ${
                  selectedFile && !uploading
                    ? "bg-blue-500 hover:bg-blue-600 text-white shadow-lg"
                    : "bg-gray-300 text-gray-500 cursor-not-allowed"
                }`}
              >
                {uploading ? "🔄 Processing PDF..." : "🚀 Extract Structure"}
              </button>
            </div>

            {/* Processed Documents */}
            {documents.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">
                  📚 Processed Documents ({documents.length})
                </h3>
                <div className="grid gap-4">
                  {documents.map((doc) => (
                    <div key={doc.id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-lg text-gray-800">
                          {doc.title}
                        </h4>
                        <span className="text-sm text-gray-500">
                          {doc.filename}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mb-3">
                        {doc.outline.length} headings extracted
                      </div>
                      <details className="text-sm">
                        <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                          View Structure
                        </summary>
                        <div className="mt-3 bg-gray-50 rounded p-3 max-h-64 overflow-y-auto">
                          {doc.outline.map((heading, idx) => (
                            <div key={idx} className={`mb-1 ${
                              heading.level === 'H1' ? 'ml-0 font-semibold' :
                              heading.level === 'H2' ? 'ml-4 font-medium' :
                              'ml-8'
                            }`}>
                              <span className="text-blue-600">{heading.level}</span>
                              {" - "}
                              <span>{heading.text}</span>
                              <span className="text-gray-500 ml-2">(p.{heading.page})</span>
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Analyze Tab */}
        {activeTab === "analyze" && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
                🧠 Persona-Driven Intelligence
              </h2>
              <p className="text-gray-600 mb-8 text-center">
                Analyze documents based on your specific role and job requirements
              </p>

              {documents.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">
                    Please upload and process some PDFs first in the Structure Extraction tab.
                  </p>
                </div>
              )}

              {documents.length > 0 && (
                <div className="space-y-6">
                  {/* Persona Input */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Your Persona/Role
                    </label>
                    <input
                      type="text"
                      value={persona}
                      onChange={(e) => setPersona(e.target.value)}
                      placeholder="e.g., PhD Researcher in Computational Biology, Investment Analyst, Undergraduate Chemistry Student"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* Job to be Done */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job to be Done
                    </label>
                    <textarea
                      value={jobToBeDone}
                      onChange={(e) => setJobToBeDone(e.target.value)}
                      placeholder="e.g., Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"
                      rows={3}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* Document Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Documents to Analyze
                    </label>
                    <div className="grid gap-3">
                      {documents.map((doc) => (
                        <div
                          key={doc.id}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            selectedDocs.includes(doc.id)
                              ? "border-blue-500 bg-blue-50"
                              : "border-gray-300 hover:border-gray-400"
                          }`}
                          onClick={() => toggleDocSelection(doc.id)}
                        >
                          <div className="flex items-center">
                            <input
                              type="checkbox"
                              checked={selectedDocs.includes(doc.id)}
                              onChange={() => toggleDocSelection(doc.id)}
                              className="mr-3"
                            />
                            <div>
                              <div className="font-medium text-gray-800">
                                {doc.title}
                              </div>
                              <div className="text-sm text-gray-500">
                                {doc.filename} • {doc.outline.length} sections
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handlePersonaAnalysis}
                    disabled={!persona || !jobToBeDone || selectedDocs.length === 0 || analyzing}
                    className={`w-full py-4 rounded-lg font-semibold text-lg transition-all ${
                      persona && jobToBeDone && selectedDocs.length > 0 && !analyzing
                        ? "bg-green-500 hover:bg-green-600 text-white shadow-lg"
                        : "bg-gray-300 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    {analyzing ? "🔄 Analyzing Documents..." : "🎯 Analyze & Extract Insights"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === "results" && (
          <div className="max-w-6xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
                📊 Analysis Results
              </h2>

              {analyses.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">
                    No persona analyses completed yet. Try the Persona Intelligence tab!
                  </p>
                </div>
              )}

              {analyses.map((analysis) => (
                <div key={analysis.id} className="mb-8 border rounded-lg p-6">
                  <div className="mb-4">
                    <h3 className="text-xl font-bold text-gray-800">
                      👤 {analysis.persona}
                    </h3>
                    <p className="text-gray-600 mt-2">
                      <strong>Job:</strong> {analysis.job_to_be_done}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Documents: {analysis.input_documents.join(", ")}
                    </p>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Extracted Sections */}
                    <div>
                      <h4 className="text-lg font-semibold text-gray-800 mb-3">
                        🎯 Most Relevant Sections
                      </h4>
                      <div className="space-y-2">
                        {analysis.extracted_sections.map((section, idx) => (
                          <div key={idx} className="bg-gray-50 rounded p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-blue-600">
                                #{section.importance_rank}
                              </span>
                              <span className="text-xs text-gray-500">
                                {section.document} (p.{section.page_number})
                              </span>
                            </div>
                            <div className="text-sm text-gray-800">
                              {section.section_title}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Sub-section Analysis */}
                    <div>
                      <h4 className="text-lg font-semibold text-gray-800 mb-3">
                        🔍 Detailed Analysis
                      </h4>
                      <div className="space-y-2">
                        {analysis.sub_section_analysis.map((subsection, idx) => (
                          <div key={idx} className="bg-blue-50 rounded p-3">
                            <div className="text-xs text-gray-500 mb-1">
                              {subsection.document} (p.{subsection.page_number})
                            </div>
                            <div className="text-sm text-gray-800">
                              {subsection.refined_text}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;