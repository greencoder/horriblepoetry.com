import json

# These are generic, empty objects used to make templating easier later
class Post(object):
    pass

class Section(object):
    pass

class Config(object):

    def __init__(self):
        self.sections = []

    @staticmethod
    def load(filename):
        """ Loads the config JSON, validates it, then returns an object """
        config_dict = json.loads(filename.read_text())
        sections = []

        for section_config in config_dict.get('sections', []):
            if set(('slug', 'name', 'order', 'description')) <= set(section_config.keys()):
                new_section = Section()
                new_section.slug = section_config.get('slug')
                new_section.name = section_config.get('name')
                new_section.order = section_config.get('order')
                new_section.description = section_config.get('description')
                sections.append(new_section)

        config = Config()
        config.sections = sorted(sections, key=lambda s: s.order)
        return config

    def find_section_name(self, section_name):
        """ Finds a section by the name provided """
        for section in self.sections:
            if section.slug == section_name:
                return section.name

        return ''