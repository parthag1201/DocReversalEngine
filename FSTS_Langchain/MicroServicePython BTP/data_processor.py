import os
import PyPDF2
# from fpdf import FPDF


class DataProcessor:
    def __init__(self, base_path=""):
        self.base_path = base_path
        self.run_folder = "last_run_output"
        self.final_dir = os.path.join(self.base_path, self.run_folder)
        os.makedirs(self.final_dir, exist_ok=True)
    
    def get_run_folder(self):
        """Get the run folder name"""
        return self.run_folder
    
    def get_final_dir(self):
        """Get the final directory path"""
        return self.final_dir
    
    def read_code_files(self, code_input_b64=None):
        """Decode and return user-supplied Base64-encoded code only. No file reading."""
        import base64
        if code_input_b64 is not None:
            try:
                return base64.b64decode(code_input_b64).decode('utf-8')
            except Exception as e:
                return f"[Error decoding provided code_input_b64: {e}]"
        return "[No code input provided]"
    
    def read_template_pdf(self):
        """Read the template from an uploaded PDF"""
        template_pdf_path = os.path.join(self.base_path, 'template.pdf')
        template_text = ""
        
        # try:
        with open(template_pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                template_text += page.extract_text()
        # except FileNotFoundError:
        #     print("Please upload a 'template.pdf' file to use as the template.")
        #     # Create a dummy template.pdf for demonstration if it doesn't exist
        #     pdf = FPDF()
        #     pdf.add_page()
        #     pdf.set_font("Arial", size=12)
        #     pdf.cell(200, 10, txt="This is a dummy template.", ln=True, align='C')
        #     pdf.output(template_pdf_path)
        #     print("A dummy 'template.pdf' has been created for you.")
            
        #     with open(template_pdf_path, 'rb') as f:
        #         reader = PyPDF2.PdfReader(f)
        #         for page in reader.pages:
        #             template_text += page.extract_text()
        
        return template_text
    
    def get_data(self):
        """Get both code input and template text"""
        code_input = self.read_code_files()
        template_text = self.read_template_pdf()
        return code_input, template_text
