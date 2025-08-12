from deep_translator import GoogleTranslator

def initialize_language_support():
    translator = GoogleTranslator()
    language_dict = translator.get_supported_languages(as_dict=True)
    code_to_name = {v: k.title() for k, v in language_dict.items()}
    name_to_code = {k.title(): v for k, v in language_dict.items()}
    name_list = sorted(list(name_to_code.keys())) + ['Auto Detect']
    return code_to_name, name_to_code, name_list
