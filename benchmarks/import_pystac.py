class ImportPySTACBench:
    repeat = 10

    def timeraw_import_pystac(self) -> str:
        return """
        import pystac
        """
