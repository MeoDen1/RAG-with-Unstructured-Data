from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams, LTTextBoxHorizontal, LTTextLineHorizontal, LTChar
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager

import pypdf
import io
import tempfile
from pikepdf import Pdf
from typing import BinaryIO
import json


def init_pdfminer():
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    return device, interpreter


def get_page_data(fp: BinaryIO, page_number: int):
    """
    Find the binary data for a given page number from a PDF binary file.
    Source: https://github.com/Unstructured-IO/unstructured/tree/main/unstructured/partition/pdf_image
    """
    pdf_reader = pypdf.PdfReader(fp)
    pdf_writer = pypdf.PdfWriter()
    page = pdf_reader.pages[page_number]
    pdf_writer.add_page(page)
    page_data = io.BytesIO()
    pdf_writer.write(page_data)
    return page_data


def extract_page(fp: BinaryIO):
    """
    Extract page layout from document.
    Source: https://github.com/Unstructured-IO/unstructured/blob/main/unstructured/partition/pdf.py
    """
    device, interpreter = init_pdfminer()

    for i, page in enumerate(PDFPage.get_pages(fp)):
        try:
            interpreter.process_page(page)
        except:
            print("Invalid dictionary construct for PDFminer in page %d. Repairing..." % (i + 1))
            error_page_data = get_page_data(fp, i)

            with tempfile.NamedTemporaryFile() as tmp:
                with Pdf.open(error_page_data) as pdf:
                    pdf.save(tmp.name)

                page = next(PDFPage.get_pages(open(tmp.name, "rb")))
                interpreter.process_page(page)
        
        yield device.get_result()


def get_type(element: LTTextBoxHorizontal):
    """
    Determine a element is a title or text
    """
    # Check for number of sentence
    if len(element) > 3: 
        return "text"
    
    # Check if the text is fully bold

    pass


def extract_element(fp: BinaryIO) -> list:
    """
    Parse a pdf into a list of data element.

    Return
    -
    List of data object in the following structure
    - **type**: header | text
    - **text**
    - **page_number**
    - **file_name**
    """
    output = []
    font_size_map = {}

    for page_number, page_layout in enumerate(extract_page(fp)):
        width, height = page_layout.width, page_layout.height

        for element in page_layout:
            if not isinstance(element, LTTextBoxHorizontal):
                continue
            
            element_obj = {"element": element}
            # Preprocess element

            element_obj['fully_bold'] = True
            element_obj['fully_capitalized'] = True
            element_obj['page_number'] = page_number

            # Loop through each line in an element
            for line in element:
                if not isinstance(line, LTTextLineHorizontal):
                    continue
                    
                # Loop through each character in a line
                for char in line:
                    if not isinstance(char, LTChar):
                        continue

                    
                    # Check if the char is bold
                    element_obj['fully_bold']  &= ('bold' in str.lower(char.fontname))

                    # Check if the char is capitalized
                    element_obj['fully_capitalized'] &= char._text.isupper()

                    font_size = round(char.size)
                    print(font_size)
                    if font_size in font_size_map.keys():
                        font_size_map[font_size] += 1
                    else:
                        font_size_map[font_size] = 1


            output.append(element_obj)
        
    
    return output


## Main
def main(file_path: str):
    with open(file_path, 'rb') as fp:
        print(extract_element(fp))

    pass


file = "../doc/article (1).pdf"

if __name__ == "__main__":
    main(file)