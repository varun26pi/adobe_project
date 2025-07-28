#!/usr/bin/env python3
"""
Create a sample academic PDF for testing the PDF intelligence system
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_sample_pdf():
    doc = SimpleDocTemplate("/app/sample_research_paper.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=12
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=10
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=8
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Deep Learning for Document Understanding: A Comprehensive Survey", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Abstract
    story.append(Paragraph("Abstract", heading1_style))
    story.append(Paragraph(
        "This paper presents a comprehensive survey of deep learning techniques applied to document understanding. "
        "We review recent advances in neural network architectures, training methodologies, and evaluation frameworks "
        "that have significantly improved the state-of-the-art in document analysis tasks.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Introduction
    story.append(Paragraph("1. Introduction", heading1_style))
    story.append(Paragraph(
        "Document understanding has emerged as a critical task in artificial intelligence, with applications ranging "
        "from automated information extraction to intelligent document processing systems. Traditional approaches "
        "relied heavily on handcrafted features and rule-based systems, which often struggled with the complexity "
        "and variability of real-world documents.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("1.1 Problem Definition", heading2_style))
    story.append(Paragraph(
        "Document understanding encompasses several interconnected tasks including text extraction, layout analysis, "
        "semantic segmentation, and content classification. Each of these tasks presents unique challenges related "
        "to document diversity and structural complexity.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("1.2 Scope and Contributions", heading2_style))
    story.append(Paragraph(
        "This survey focuses on deep learning approaches developed in the past five years. Our main contributions "
        "include: (1) a comprehensive taxonomy of neural architectures, (2) analysis of training strategies, "
        "and (3) evaluation of current benchmarks and datasets.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Related Work
    story.append(Paragraph("2. Related Work", heading1_style))
    story.append(Paragraph(
        "Early work in document understanding relied on traditional computer vision and natural language processing "
        "techniques. Optical Character Recognition (OCR) systems formed the foundation for text extraction, while "
        "geometric analysis methods were used for layout understanding.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("2.1 Traditional Approaches", heading2_style))
    story.append(Paragraph(
        "Traditional document analysis systems typically followed a pipeline approach: preprocessing, segmentation, "
        "feature extraction, and classification. While effective for structured documents, these methods often "
        "failed on complex layouts and noisy inputs.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("2.1.1 OCR Systems", heading3_style))
    story.append(Paragraph(
        "Optical Character Recognition systems have evolved from simple template matching to sophisticated "
        "machine learning approaches. Modern OCR engines incorporate neural networks for improved accuracy "
        "on diverse fonts and imaging conditions.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("2.2 Deep Learning Revolution", heading2_style))
    story.append(Paragraph(
        "The introduction of deep learning transformed document understanding by enabling end-to-end learning "
        "of complex patterns and relationships. Convolutional neural networks proved particularly effective "
        "for visual document analysis tasks.",
        styles['Normal']
    ))
    
    # Add page break
    story.append(PageBreak())
    
    # Methodology
    story.append(Paragraph("3. Methodology", heading1_style))
    story.append(Paragraph(
        "Our approach to document understanding combines multiple neural network architectures in a unified "
        "framework. We leverage both visual and textual information through multi-modal learning techniques.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("3.1 Neural Architecture Design", heading2_style))
    story.append(Paragraph(
        "We propose a hierarchical neural architecture that processes documents at multiple granularities: "
        "pixel-level for visual features, word-level for semantic understanding, and document-level for "
        "global structure comprehension.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("3.1.1 Visual Feature Extraction", heading3_style))
    story.append(Paragraph(
        "The visual component employs a ResNet-based backbone for extracting visual features from document images. "
        "Feature pyramid networks are used to capture multi-scale information essential for handling documents "
        "with varying text sizes and layout complexity.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("3.1.2 Text Processing Module", heading3_style))
    story.append(Paragraph(
        "Text features are processed using transformer-based encoders that capture long-range dependencies "
        "within documents. Positional encodings incorporate spatial information to maintain layout awareness.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("3.2 Training Strategy", heading2_style))
    story.append(Paragraph(
        "We employ a multi-task learning framework that jointly optimizes for text detection, recognition, "
        "and layout analysis. This approach enables the model to learn shared representations that benefit "
        "all downstream tasks.",
        styles['Normal']
    ))
    
    # Experiments
    story.append(Paragraph("4. Experiments", heading1_style))
    story.append(Paragraph(
        "We evaluate our approach on standard document understanding benchmarks including DocVQA, FUNSD, "
        "and CORD datasets. Experimental results demonstrate significant improvements over existing methods.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("4.1 Datasets and Metrics", heading2_style))
    story.append(Paragraph(
        "Our evaluation covers diverse document types including forms, receipts, research papers, and "
        "administrative documents. Performance is measured using standard metrics including F1-score, "
        "exact match accuracy, and BLEU scores for text generation tasks.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("4.2 Comparative Analysis", heading2_style))
    story.append(Paragraph(
        "Comparison with state-of-the-art methods shows consistent improvements across all evaluation metrics. "
        "Our approach achieves particularly strong performance on complex document layouts that challenge "
        "traditional pipeline-based systems.",
        styles['Normal']
    ))
    
    # Conclusion
    story.append(Paragraph("5. Conclusion", heading1_style))
    story.append(Paragraph(
        "This work presents a comprehensive framework for document understanding that leverages the latest "
        "advances in deep learning. Our multi-modal approach achieves state-of-the-art results while "
        "maintaining computational efficiency suitable for practical applications.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("5.1 Future Work", heading2_style))
    story.append(Paragraph(
        "Future research directions include extending the framework to handle multilingual documents, "
        "incorporating external knowledge bases, and developing more efficient architectures for "
        "real-time processing applications.",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    print("Sample PDF created successfully: /app/sample_research_paper.pdf")

if __name__ == "__main__":
    create_sample_pdf()