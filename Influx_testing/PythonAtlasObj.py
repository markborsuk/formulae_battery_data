import win32com.client


class PythonAtlasObj:

    def __init__(self):
        # Try to open Atlas
        self.hATLAS = win32com.client.Dispatch("ATLAS.Application")

        # Initialise a number of ATLAS API Modules
        self.hWorkbook = self.hATLAS.Workbook
        self.hLayers = self.hWorkbook.Layers
