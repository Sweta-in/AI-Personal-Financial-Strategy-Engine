"""
Document ingestion — PDF extraction, chunking, and index building.

Processes Indian tax rules (80C, 80D, 24B), IRDAI guidelines,
and financial glossary documents.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger


def extract_text_from_pdf(path: str) -> str:
    """
    Extract text from a PDF file using pymupdf.

    Args:
        path: Path to the PDF file

    Returns:
        Extracted text as string
    """
    try:
        import fitz  # pymupdf
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        logger.warning("pymupdf not installed — returning empty text")
        return ""
    except Exception as e:
        logger.error(f"PDF extraction failed for {path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Source text
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < text_len:
            # Look for sentence-ending punctuation near the end
            for sep in [". ", ".\n", "\n\n", "\n", " "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > chunk_size // 2:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def ingest_documents(docs_folder: str, index_output: str) -> int:
    """
    Ingest all documents from a folder and build a FAISS index.

    Args:
        docs_folder: Path to folder containing PDFs and text files
        index_output: Output path for the FAISS index

    Returns:
        Number of chunks indexed
    """
    from rag.pipeline import pipeline

    all_chunks = []
    docs_path = Path(docs_folder)

    if not docs_path.exists():
        logger.warning(f"Docs folder {docs_folder} not found — using built-in knowledge")
        all_chunks = _get_builtin_knowledge()
    else:
        # Process PDFs
        for pdf_path in docs_path.glob("*.pdf"):
            logger.info(f"Ingesting: {pdf_path.name}")
            text = extract_text_from_pdf(str(pdf_path))
            chunks = chunk_text(text)
            all_chunks.extend(chunks)

        # Process text files
        for txt_path in docs_path.glob("*.txt"):
            logger.info(f"Ingesting: {txt_path.name}")
            text = txt_path.read_text(encoding="utf-8")
            chunks = chunk_text(text)
            all_chunks.extend(chunks)

    if not all_chunks:
        all_chunks = _get_builtin_knowledge()

    pipeline.build_index(all_chunks, save_path=index_output)
    logger.info(f"Indexed {len(all_chunks)} chunks to {index_output}")
    return len(all_chunks)


def _get_builtin_knowledge() -> list[str]:
    """Built-in financial knowledge for bootstrapping without external documents."""
    return [
        # Section 80C
        "Section 80C of the Income Tax Act allows deductions up to ₹1,50,000 per financial year. "
        "Eligible instruments include ELSS mutual funds (3-year lock-in), PPF (15-year lock-in), "
        "NSC, 5-year tax-saving fixed deposits, NPS contributions, life insurance premiums, "
        "tuition fees for children, and home loan principal repayment.",

        "Under Section 80CCD(1B), an additional deduction of ₹50,000 is available for contributions "
        "to the National Pension System (NPS), over and above the ₹1,50,000 limit of Section 80C.",

        # Section 80D
        "Section 80D provides deductions for health insurance premiums. For individuals below 60, "
        "the limit is ₹25,000 for self and family. For senior citizens, the limit is ₹50,000. "
        "An additional ₹25,000 (₹50,000 for senior citizen parents) is available for parents' premiums. "
        "Preventive health check-ups up to ₹5,000 are included within these limits.",

        # Section 24(b)
        "Section 24(b) allows deduction of home loan interest up to ₹2,00,000 per year for "
        "self-occupied property. For let-out property, there is no upper limit on interest deduction. "
        "The property must be acquired or constructed within 5 years from the end of the financial year "
        "in which the loan was taken to claim the full ₹2,00,000 deduction.",

        # HRA
        "HRA exemption under Section 10(14) is the minimum of: (1) actual HRA received, "
        "(2) 50% of basic salary for metro cities / 40% for non-metro, (3) rent paid minus 10% of basic salary. "
        "Employees not receiving HRA can claim deduction under Section 80GG up to ₹5,000/month.",

        # Term Insurance
        "Term insurance provides pure life cover without any investment component. IRDAI recommends "
        "coverage of 10-15 times annual income. Key factors for selection: claim settlement ratio "
        "(CSR > 95%), incurred claim ratio, solvency ratio (> 1.5x mandatory), and policy term "
        "till retirement age (60-65). Add critical illness rider if not covered by employer.",

        # Health Insurance
        "Health insurance should cover at minimum ₹10 lakh for metro city residents. Key features to check: "
        "no co-payment clause, adequate room rent limits, restoration benefit for family floater plans, "
        "daycare procedures coverage, pre-existing disease waiting period (typically 2-4 years), "
        "and network hospital coverage in your city.",

        # Emergency Fund
        "Financial planners recommend maintaining an emergency fund of 6-12 months of expenses. "
        "This fund should be held in highly liquid instruments: savings account, liquid mutual funds, "
        "or short-term FDs. The fund covers job loss, medical emergencies, and unexpected large expenses.",

        # Asset Allocation
        "The classic rule of thumb for equity allocation: (100 - age)% in equity. However, this varies "
        "based on risk tolerance, income stability, and financial goals. Conservative: 30-40% equity, "
        "Moderate: 50-60% equity, Aggressive: 70-80% equity. Rebalance annually.",

        # SIP and Compounding
        "Systematic Investment Plans (SIPs) benefit from rupee-cost averaging and compounding. "
        "A ₹10,000 monthly SIP at 12% CAGR grows to approximately ₹1 crore in 20 years. "
        "Starting early is crucial — a 5-year delay almost halves the final corpus at the same rate.",

        # Debt-to-Income Ratio
        "Debt-to-Income (DTI) ratio guidelines: Below 20% is healthy, 20-36% is manageable, "
        "36-50% is stressed, above 50% is critical. Banks typically approve loans when DTI is below 50%. "
        "Total EMIs including the new loan should not exceed 50% of net monthly income.",

        # Home Loan Prepayment
        "Home loan prepayment is most effective in the early years when interest component is highest. "
        "Most banks allow prepayment without penalty for floating rate loans (RBI directive). "
        "Compare the guaranteed return from prepayment (loan interest rate) vs expected return "
        "from alternative investments after tax.",

        # Mutual Fund Categories
        "SEBI categorization: Large Cap (top 100 stocks), Mid Cap (101-250), Small Cap (251+), "
        "Multi Cap (min 25% each in large/mid/small), Flexi Cap (no restriction). "
        "Index funds tracking Nifty 50 or Nifty Next 50 offer low-cost passive exposure. "
        "Expense ratio for index funds should be below 0.5%.",
    ]
