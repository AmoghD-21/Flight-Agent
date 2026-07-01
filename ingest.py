# import os
# import pdfplumber
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# def extract_clean_pdf_content(pdf_path):

#     """Extract text from a PDF file and clean it up."""
#     page_documents=[]

#     with pdfplumber.open(pdf_path) as pdf:
#         for page_num,page in enumerate(pdf.pages,start=1):
#             page_text=""

#             # Extract and format the tables
#             tables=page.extract_tables()
#             if tables:
#                 for table in tables:
#                     cleaned_table=[[str(cell).strip() for cell in row] for row in table]

#                     # Convert row data into markdown format

#                     if len(cleaned_table)>0:
#                         table_md="| " + " | ".join(cleaned_table[0]) + " |\n"
#                         table_md+="| " + " | ".join(["---"]*len(cleaned_table[0])) + " |\n"
#                         for row in cleaned_table[1:]:
#                             table_md+="| " + " | ".join(row) + " |\n"
#                         page_text+=table_md+"\n"

#             text=page.extract_text()
#             if text:
#                 page_text+=text

#                 # Convert to Langchain Document format with metadata

#             if page_text.strip():
#                 doc=Document(
#                     page_content=page_text,
#                     metadata={"source": os.path.basename(pdf_path), "page": page_num}

#                 )
#                 page_documents.append(doc)

#     return page_documents

# def process_air_india_docs():
#     data_folder="./data"
#     all_documents = []

#     if not os.path.exists(data_folder) or not os.listdir(data_folder):
#         print(f"❌ Error: Please make sure your PDFs are downloaded inside '{data_folder}'.")
#         return None
    
#     print("Processing Air India documents...")
#     for file in os.listdir(data_folder):
#         if file.endswith(".pdf"):
#             pdf_path=os.path.join(data_folder,file)
#             print(f"Extracting content from: {file}")
#             all_documents.extend(extract_clean_pdf_content(pdf_path))

#     print(f"✅ Successfully extracted {len(all_documents)} structural pages.")

#     print(" Splitting documents into optimized chunks...")
#     text_splitter=RecursiveCharacterTextSplitter(
#                 chunk_size=1000,
#                 chunk_overlap=200,
#                 length_function=len
#             )
#     chunks = text_splitter.split_documents(all_documents)
#     print(f"🧩 Created {len(chunks)} optimized chunks ready for your Vector Store.")

#     # Quick peek to see how our formatted tables look!
#     for chunk in chunks:
#         if "|" in chunk.page_content:
#             print("\n--- Preview of a Table-Preserved Chunk ---")
#             print("\n".join(chunk.page_content.split("\n")[:8]) + "\n...")
#             print("------------------------------------------")
#             break

#     return chunks

# if __name__ == "__main__":
#     process_air_india_docs()










import os
import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_clean_pdf_content(pdf_path):
    """Extract text + tables from a PDF and convert into clean structured format."""

    page_documents = []

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "intersection_tolerance": 5,
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            page_text_parts = []

            # -------------------------
            # 1. TABLE EXTRACTION
            # -------------------------
            tables = page.extract_tables(table_settings)

            print(f"Page {page_num}: {len(tables)} table(s) found")

            for table in tables:

                if not table or len(table) < 2:
                    continue

                cleaned_table = [
                    [cell.strip() if cell else "" for cell in row]
                    for row in table
                ]

                headers = cleaned_table[0]

                # Build Markdown table
                table_md = "| " + " | ".join(headers) + " |\n"
                table_md += "|" + "|".join(["---"] * len(headers)) + "|\n"

                for row in cleaned_table[1:]:
                    row = row[:len(headers)]

                    if len(row) < len(headers):
                        row.extend([""] * (len(headers) - len(row)))

                    table_md += "| " + " | ".join(row) + " |\n"

                page_text_parts.append(table_md)

            # -------------------------
            # 2. NORMAL TEXT EXTRACTION
            # -------------------------
            text = page.extract_text()

            if text:
                page_text_parts.append(text)

            # -------------------------
            # 3. COMBINE PAGE CONTENT
            # -------------------------
            page_text = "\n\n".join(page_text_parts)

            if page_text.strip():
                doc = Document(
                    page_content=page_text,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "page": page_num
                    }
                )
                page_documents.append(doc)

    return page_documents


def process_air_india_docs():
    data_folder = "./data"
    all_documents = []

    if not os.path.exists(data_folder) or not os.listdir(data_folder):
        print(f"❌ Error: Please place PDFs inside '{data_folder}'.")
        return None

    print("Processing Air India documents...")

    for file in os.listdir(data_folder):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(data_folder, file)
            print(f"Extracting content from: {file}")

            all_documents.extend(extract_clean_pdf_content(pdf_path))

    print(f"✅ Extracted {len(all_documents)} page-level documents.")

    # -------------------------
    # 4. CHUNKING
    # -------------------------
    print("Splitting documents into chunks...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    chunks = text_splitter.split_documents(all_documents)

    print(f"🧩 Created {len(chunks)} chunks for vector store.")

    # -------------------------
    # 5. DEBUG PREVIEW
    # -------------------------
    for chunk in chunks:
        if "|" in chunk.page_content:
            print("\n--- TABLE CHUNK PREVIEW ---")
            print("\n".join(chunk.page_content.split("\n")[:10]))
            print("----------------------------")
            break

    return chunks


if __name__ == "__main__":
    process_air_india_docs()