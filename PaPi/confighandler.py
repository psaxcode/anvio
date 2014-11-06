# -*- coding: utf-8 -*-

# Copyright (C) 2014, A. Murat Eren
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.


import os
import sys
import ConfigParser

import PaPi.filesnpaths as filesnpaths
from PaPi.utils import ConfigError as ConfigError

config_template = {
    'general': {
                'output_file'    : {'mandatory': True, 'test': lambda x: filesnpaths.is_output_file_writable(x)},
                'num_components': {'mandatory': False, 'test': lambda x: RepresentsInt(x) and int(x) > 0 and int(x) <= 256,
                                   'required': "An integer value between 1 and 256"},
                'skip_scaling': {'mandatory': False, 'test': lambda x: x in ['True', 'False'], 'required': 'True or False'},
                'seed': {'mandatory': False, 'test': lambda x: RepresentsInt(x), 'required': 'An integer'}
    },
    'matrix': {},
}

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

class RunConfiguration:
    def __init__(self, config_file_path, input_directory = None):
        self.input_directory = input_directory or os.getcwd()

        filesnpaths.is_file_exists(config_file_path)
        config = ConfigParser.ConfigParser()
        config.read(config_file_path)

        self.sanity_check(config)

        self.output_file = self.get_option(config, 'general', 'output_file', str)
        self.skip_scaling = True if self.get_option(config, 'general', 'skip_scaling', str) == "True" else False
        self.num_components = self.get_option(config, 'general', 'num_components', int)
        self.seed = self.get_option(config, 'general', 'seed', int)


    def get_option(self, config, section, option, cast):
        try:
            return cast(config.get(section, option).strip())
        except ConfigParser.NoOptionError:
            return None


    def get_other_sections(self, config):
        return [s for s in config.sections() if s != 'general']


    def check_section(self, config, section, template_class):
        """section is the actual section name in the config file, template_class corresponds
           to the type of section it is..."""
        for option, value in config.items(section):
            if option not in config_template[template_class].keys():
                raise ConfigError, 'Unknown option under "%s" section: "%s"' % (section, option)
            if config_template[template_class][option].has_key('test') and not config_template[template_class][option]['test'](value):
                if config_template[template_class][option].has_key('required'):
                    r = config_template[template_class][option]['required']
                    raise ConfigError, 'Unexpected value for "%s" section "%s": %s \n    Expected: %s' % (option, section, value, r)
                else:
                    raise ConfigError, 'Unexpected value for "%s" section "%s": %s' % (option, section, value)

        for option in config_template[template_class]:
            if config_template[template_class][option].has_key('mandatory') and config_template[template_class][option]['mandatory'] and not config.has_option(section, option):
                raise ConfigError, 'Missing mandatory option for section "%s": %s' % (section, option)


    def sanity_check(self, config):
        filesnpaths.is_file_exists(self.input_directory)

        if 'general' not in config.sections():
            raise ConfigError, "[general] section is mandatory."

        if len(config.sections()) < 2:
            raise ConfigError, "Config file must contain at least one matrix sextion."

        self.check_section(config, 'general', 'general')
        for section in self.get_other_sections(config):
            if not os.path.exists(os.path.join(self.input_directory, section)):
                raise ConfigError, 'The matrix file "%s" you mentioned in the config file is not in the\
                                    input directory (which is the current working directory if you have\
                                    not specified one. Please specify the correct input directory' % (section)
            self.check_section(config, section, 'matrix')
