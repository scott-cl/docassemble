# -*- coding: utf-8 -*-
import mimetypes
import traceback
import re
from io import open
from six import string_types, text_type, PY2, PY3
from jinja2.runtime import StrictUndefined, UndefinedError
from jinja2.exceptions import TemplateError
from jinja2.environment import Environment
from jinja2.environment import Template as JinjaTemplate
from jinja2 import meta as jinja2meta
from jinja2.lexer import Token
from jinja2.utils import internalcode, missing, object_type_repr
from jinja2.ext import Extension
import ast
import ruamel.yaml as yaml
import string
import os
import os.path
import sys
import types
if PY2:
    from urllib import urlretrieve
else:
    from urllib.request import urlretrieve
import httplib2
import datetime
import time
import operator
import pprint
import copy
import codecs
import array
import random
import tempfile
import json
import docassemble.base.filter
import docassemble.base.pdftk
import docassemble.base.file_docx
from docassemble.base.error import DAError, MandatoryQuestion, DAErrorNoEndpoint, DAErrorMissingVariable, ForcedNameError, QuestionError, ResponseError, BackgroundResponseError, BackgroundResponseActionError, CommandError, CodeExecute, DAValidationError, ForcedReRun, LazyNameError, DAAttributeError, DAIndexError
import docassemble.base.functions
from docassemble.base.functions import pickleable_objects, word, get_language, server, RawValue, get_config
from docassemble.base.logger import logmessage
from docassemble.base.pandoc import MyPandoc, word_to_markdown
from docassemble.base.mako.template import Template as MakoTemplate
from docassemble.base.mako.exceptions import SyntaxException, CompileException
from docassemble.base.astparser import myvisitnode
if PY2:
    import collections as abc
else:
    import collections.abc as abc
from collections import OrderedDict
from types import CodeType
RangeType = type(range(1,2))
NoneType = type(None)

debug = True
import_core = compile("import docassemble.base.core", '<code block>', 'exec')
import_util = compile('from docassemble.base.util import *', '<code block>', 'exec')
import_process_action = compile('from docassemble.base.util import process_action', '<code block>', 'exec')
run_process_action = compile('process_action()', '<code block>', 'exec')
match_process_action = re.compile(r'process_action\(')
match_mako = re.compile(r'<%|\${|% if|% for|% while')
emoji_match = re.compile(r':([^ ]+):')
valid_variable_match = re.compile(r'^[^\d][A-Za-z0-9\_]*$')
nameerror_match = re.compile(r'\'(.*)\' (is not defined|referenced before assignment|is undefined)')
document_match = re.compile(r'^--- *$', flags=re.MULTILINE)
remove_trailing_dots = re.compile(r'[\n\r]+\.\.\.$')
fix_tabs = re.compile(r'\t')
dot_split = re.compile(r'([^\.\[\]]+(?:\[.*?\])?)')
match_brackets_at_end = re.compile(r'^(.*)(\[.+?\])')
match_inside_brackets = re.compile(r'\[(.+?)\]')
match_brackets = re.compile(r'(\[.+?\])')
match_brackets_or_dot = re.compile(r'(\[.+?\]|\.[a-zA-Z_][a-zA-Z0-9_]*)')
complications = re.compile(r'[\.\[]')
list_of_indices = ['i', 'j', 'k', 'l', 'm', 'n']
extension_of_doc_format = {'pdf':'pdf', 'docx': 'docx', 'rtf': 'rtf', 'rtf to docx': 'docx', 'tex': 'tex', 'html': 'html'}

def process_audio_video_list(the_list, the_user_dict):
    output = list()
    for the_item in the_list:
        output.append({'text': the_item['text'].text(the_user_dict), 'package': the_item['package'], 'type': the_item['type']})
    return output

def textify(data, the_user_dict):
    return list(map((lambda x: x.text(the_user_dict)), data))

# def set_absolute_filename(func):
#     #logmessage("Running set_absolute_filename in parse")
#     docassemble.base.functions.set_absolute_filename(func)

# def set_url_finder(func):
#     docassemble.base.filter.set_url_finder(func)
#     docassemble.base.functions.set_url_finder(func)

# def set_url_for(func):
#     docassemble.base.filter.set_url_for(func)

# def set_file_finder(func):
#     docassemble.base.filter.set_file_finder(func)

# def set_da_send_mail(func):
#     docassemble.base.filter.set_da_send_mail(func)

# def blank_save_numbered_file(*args, **kwargs):
#     return(None, None, None)

# save_numbered_file = blank_save_numbered_file

# def set_save_numbered_file(func):
#     global save_numbered_file
#     #logmessage("set the save_numbered_file function to " + str(func))
#     save_numbered_file = func
#     return

initial_dict = dict(_internal=dict(progress=0, tracker=0, docvar=dict(), doc_cache=dict(), steps=1, steps_offset=0, secret=None, informed=dict(), livehelp=dict(availability='unavailable', mode='help', roles=list(), partner_roles=list()), answered=set(), answers=dict(), objselections=dict(), starttime=None, modtime=None, accesstime=dict(), tasks=dict(), gather=list(), event_stack=dict()), url_args=dict(), nav=docassemble.base.functions.DANav())

def set_initial_dict(the_dict):
    global initial_dict
    initial_dict = the_dict
    return

def get_initial_dict():
    return copy.deepcopy(initial_dict);

class PackageImage(object):
    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename', None)
        self.attribution = kwargs.get('attribution', None)
        self.setname = kwargs.get('setname', None)
        self.package = kwargs.get('package', 'docassemble.base')
    def get_filename(self):
        return(docassemble.base.functions.static_filename_path(str(self.package) + ':' + str(self.filename)))
    def get_reference(self):
        #logmessage("get_reference is considering " + str(self.package) + ':' + str(self.filename))
        return str(self.package) + ':' + str(self.filename)

class InterviewSource(object):
    def __init__(self, **kwargs):
        if not hasattr(self, 'package'):
            self.package = kwargs.get('package', None)
        self.language = kwargs.get('language', '*')
        self.dialect = kwargs.get('dialect', None)
        self.testing = kwargs.get('testing', False)
    def __le__(self, other):
        return text_type(self) <= (text_type(other) if isinstance(other, InterviewSource) else other)
    def __ge__(self, other):
        return text_type(self) >= (text_type(other) if isinstance(other, InterviewSource) else other)
    def __gt__(self, other):
        return text_type(self) > (text_type(other) if isinstance(other, InterviewSource) else other)
    def __lt__(self, other):
        return text_type(self) < (text_type(other) if isinstance(other, InterviewSource) else other)
    def __eq__(self, other):
        return self is other
    def __ne__(self, other):
        return self is not other
    def __str__(self):
        return self.__unicode__().encode('utf-8') if PY2 else self.__unicode__()
    def __unicode__(self):
        if hasattr(self, 'path'):
            return text_type(self.path)
        return 'interviewsource'
    def __hash__(self):
        if hasattr(self, 'path'):
            return hash((self.path,))
        else:
            return hash(('interviewsource',))
    def set_path(self, path):
        self.path = path
        return
    def get_index(self):
        the_index = docassemble.base.functions.server.server_redis.get('da:interviewsource:' + self.path)
        if the_index is None:
            #sys.stderr.write("Updating index from get_index for " + self.path + "\n")
            the_index = docassemble.base.functions.server.server_redis.incr('da:interviewsource:' + self.path)
        return the_index
    def update_index(self):
        #sys.stderr.write("Updating index for " + self.path + "\n")
        docassemble.base.functions.server.server_redis.incr('da:interviewsource:' + self.path)
    def set_filepath(self, filepath):
        self.filepath = filepath
        return
    def set_directory(self, directory):
        self.directory = directory
        return
    def set_content(self, content):
        self.content = content
        return
    def set_language(self, language):
        self.language = language
        return
    def set_dialect(self, dialect):
        self.dialect = dialect
        return
    def set_testing(self, testing):
        self.testing = testing
        return
    def set_package(self, package):
        self.package = package
        return
    def update(self):
        return True
    def get_modtime(self):
        return self._modtime
    def get_language(self):
        return self.language
    def get_dialect(self):
        return self.dialect
    def get_package(self):
        return self.package
    def get_testing(self):
        return self.testing
    def get_interview(self):
        return Interview(source=self)
    def append(self, path):
        return None

class InterviewSourceString(InterviewSource):
    def __init__(self, **kwargs):
        #self.playground = None
        #self.package = None
        #self.set_filepath(kwargs.get('filepath', None))
        self.set_path(kwargs.get('path', None))
        self.set_directory(kwargs.get('directory', None))
        self.set_content(kwargs.get('content', None))
        self._modtime = datetime.datetime.utcnow()
        return super(InterviewSourceString, self).__init__(**kwargs)

class InterviewSourceFile(InterviewSource):
    def __init__(self, **kwargs):
        self.playground = None
        if 'filepath' in kwargs:
            if re.search(r'SavedFile', str(type(kwargs['filepath']))):
                #logmessage("We have a saved file on our hands")
                self.playground = kwargs['filepath']
                if os.path.isfile(self.playground.path) and os.access(self.playground.path, os.R_OK):
                    self.set_filepath(self.playground.path)
                else:
                    raise DAError("Reference to invalid playground path")
            else:
                self.set_filepath(kwargs['filepath'])
        else:
            self.filepath = None
        if 'path' in kwargs:
            self.set_path(kwargs['path'])
        return super(InterviewSourceFile, self).__init__(**kwargs)
    def set_path(self, path):
        self.path = path
        parts = path.split(":")
        if len(parts) == 2:
            self.package = parts[0]
            self.basename = parts[1]
        else:
            self.package = None
        # if self.package is None:
        #     m = re.search(r'^/(playground\.[0-9]+)/', path)
        #     if m:
        #         self.package = m.group(1)
        if self.filepath is None:
            self.set_filepath(interview_source_from_string(self.path))
        if self.package is None and re.search(r'docassemble.base.data.', self.filepath):
            self.package = 'docassemble.base'
        return
    def set_filepath(self, filepath):
        #logmessage("Called set_filepath with " + str(filepath))
        self.filepath = filepath
        if self.filepath is None:
            self.directory = None
        else:
            self.set_directory(os.path.dirname(self.filepath))
        return
    def reset_modtime(self):
        try:
            with open(self.filepath, 'a'):
                os.utime(self.filepath, None)
        except:
            logmessage("InterviewSourceFile: could not reset modification time on interview")
    def update(self):
        #logmessage("Update: " + str(self.filepath))
        try:
            with open(self.filepath, 'rU', encoding='utf-8') as the_file:
                self.set_content(the_file.read())
                #sys.stderr.write("Returning true\n")
                return True
        except Exception as errmess:
            #sys.stderr.write("Error: " + str(errmess) + "\n")
            pass
        return False
    def get_modtime(self):
        #logmessage("get_modtime called in parse where path is " + str(self.path))
        if self.playground is not None:
            return self.playground.get_modtime(filename=self.basename)
        self._modtime = os.path.getmtime(self.filepath)
        return(self._modtime)
    def append(self, path):
        new_file = os.path.join(self.directory, path)
        if os.path.isfile(new_file) and os.access(new_file, os.R_OK):
            new_source = InterviewSourceFile()
            new_source.path = path
            new_source.basename = path
            new_source.filepath = new_file
            new_source.playground = self.playground
            if hasattr(self, 'package'):
                new_source.package = self.package
            if new_source.update():
                return(new_source)
        return(None)
    
class InterviewSourceURL(InterviewSource):
    def __init__(self, **kwargs):
        self.set_path(kwargs.get('path', None))
        return super(InterviewSourceURL, self).__init__(**kwargs)
    def set_path(self, path):
        self.path = path
        if self.path is None:
            self.directory = None
        else:
            self.directory = re.sub('/[^/]*$', '', re.sub('\?.*', '', self.path))
        return
    def update(self):
        try:
            h = httplib2.Http()
            resp, content = h.request(self.path, "GET")
            if resp['status'] >= 200 and resp['status'] < 300:
                self.set_content(content.decode())
                self._modtime = datetime.datetime.utcnow()
                return True
        except:
            pass
        return False
    def append(self, path):
        new_file = os.path.join(self.directory, path)
        if os.path.isfile(new_file) and os.access(new_file, os.R_OK):
            new_source = InterviewSourceFile()
            new_source.path = path
            new_source.filepath = new_file
            if new_source.update():
                return(new_source)
        return None

class InterviewStatus(object):
    def __init__(self, current_info=dict(), **kwargs):
        self.current_info = current_info
        self.attributions = set()
        self.seeking = list()
        self.tracker = kwargs.get('tracker', -1)
        self.maps = list()
        self.extra_scripts = list()
        self.extra_css = list()
        self.using_screen_reader = False
        self.can_go_back = True
        self.attachments = None
        self.linkcounter = 0
        #restore this, maybe
        #self.next_action = list()
        self.embedded = set()
        self.extras = dict()
        self.followed_mc = False
        self.tentatively_answered = set()
        self.checkin = False
    def get_field_list(self):
        if 'sub_fields' in self.extras:
            field_list = list()
            for field in self.question.fields:
                if field.number in self.extras['sub_fields']:
                    field_list.extend(self.extras['sub_fields'][field.number])
                else:
                    field_list.append(field)
            return field_list
        return self.question.fields
    def mark_tentative_as_answered(self, the_user_dict):
        for question in self.tentatively_answered:
            question.mark_as_answered(the_user_dict)
        self.tentatively_answered.clear()
    def initialize_screen_reader(self):
        self.using_screen_reader = True
        self.screen_reader_text = dict()
        self.screen_reader_links = {'question': [], 'help': []}
    def populate(self, question_result):
        self.question = question_result['question']
        self.questionText = question_result['question_text']
        self.subquestionText = question_result['subquestion_text']
        self.continueLabel = question_result['continue_label']
        self.decorations = question_result['decorations']
        self.audiovideo = question_result['audiovideo']
        self.helpText = question_result['help_text']
        self.attachments = question_result['attachments']
        self.selectcompute = question_result['selectcompute']
        self.defaults = question_result['defaults']
        #self.defined = question_result['defined']
        self.hints = question_result['hints']
        self.helptexts = question_result['helptexts']
        self.extras = question_result['extras']
        self.labels = question_result['labels']
        self.sought = question_result['sought']
        self.orig_sought = question_result['orig_sought']
    def set_tracker(self, tracker):
        self.tracker = tracker
    def as_data(self, the_user_dict, encode=True):
        result = dict(language=self.question.language)
        if self.question.language in self.question.interview.default_validation_messages:
            result['validation_messages'] = copy.copy(self.question.interview.default_validation_messages[self.question.language])
        else:
            result['validation_messages'] = dict()
        if self.orig_sought is not None:
            result['event_list'] = [self.orig_sought]
        for param in ('questionText', 'subquestionText', 'continueLabel', 'helpLabel'):
            if hasattr(self, param) and getattr(self, param) is not None:
                result[param] = getattr(self, param).rstrip()
        if 'menu_items' in self.extras and isinstance(self.extras['menu_items'], list):
            result['menu_items'] = self.extras['menu_items']
        for param in ('rightText', 'underText', 'back_button_label', 'css', 'script'):
            if param in self.extras and isinstance(self.extras[param], string_types):
                result[param] = self.extras[param].rstrip()
        if hasattr(self, 'audiovideo') and self.audiovideo is not None:
            audio_result = docassemble.base.filter.get_audio_urls(self.audiovideo)
            video_result = docassemble.base.filter.get_video_urls(self.audiovideo)
            if len(audio_result) > 0:
                result['audio'] = [dict(url=re.sub(r'.*"(http[^"]+)".*', r'\1', x)) if isinstance(x, string_types) else dict(url=x[0], mime_type=x[1]) for x in audio_result]
            if len(video_result) > 0:
                result['video'] = [dict(url=re.sub(r'.*"(http[^"]+)".*', r'\1', x)) if isinstance(x, string_types) else dict(url=x[0], mime_type=x[1]) for x in video_result]
        if hasattr(self, 'helpText') and len(self.helpText) > 0:
            result['helpText'] = list()
            for help_text in self.helpText:
                the_help = dict()
                if 'audiovideo' in help_text and help_text['audiovideo'] is not None:
                    audio_result = docassemble.base.filter.get_audio_urls(help_text['audiovideo'])
                    video_result = docassemble.base.filter.get_video_urls(help_text['audiovideo'])
                    if len(audio_result) > 0:
                        the_help['audio'] = [dict(url=x[0], mime_type=x[1]) for x in audio_result]
                    if len(video_result) > 0:
                        the_help['video'] = [dict(url=x[0], mime_type=x[1]) for x in video_result]
                if 'content' in help_text and help_text['content'] is not None:
                    the_help['content'] = help_text['content'].rstrip()
                if 'heading' in help_text and help_text['heading'] is not None:
                    the_help['heading'] = help_text['heading'].rstrip()
                result['helpText'].append(the_help)
        if 'questionText' not in result and self.question.question_type == "signature":
            result['questionText'] = word('Sign Your Name')
        result['questionType'] = self.question.question_type
        if self.question.is_mandatory or self.question.mandatory_code is not None:
            result['mandatory'] = True
        if hasattr(self.question, 'name'):
            result['_question_name'] = self.question.name
        result['_tracker'] = self.tracker
        if hasattr(self, 'datatypes'):
            result['_datatypes'] = safeid(json.dumps(self.datatypes))
        if hasattr(self, 'varnames'):
            result['_varnames'] = safeid(json.dumps(self.varnames))
        if len(self.question.fields) > 0:
            result['fields'] = list()
        if hasattr(self.question, 'review_saveas'):
            result['question_variable_name'] = self.question.review_saveas
        if hasattr(self.question, 'fields_saveas'):
            result['question_variable_name'] = self.question.fields_saveas
        if self.decorations is not None:
            for decoration in self.decorations:
                if 'image' in decoration:
                    the_image = self.question.interview.images.get(decoration['image'], None)
                    if the_image is not None:
                        the_url = docassemble.base.functions.server.url_finder(str(the_image.package) + ':' + str(the_image.filename))
                        if the_url is not None and the_image.attribution is not None:
                            result['decoration_url'] = the_url
                            self.attributions.add(the_image.attribution)
                        break
                    elif get_config('default icons', None) in ('material icons', 'font awesome'):
                        result['decoration_name'] = decoration['image']
                        break
        if len(self.attachments) > 0:
            result['attachments'] = list()
            if self.current_info['user']['is_authenticated'] and self.current_info['user']['email']:
                result['default_email'] = self.current_info['user']['email']
            for attachment in self.attachments:
                the_attachment = dict(url=dict(), number=dict(), filename_with_extension=dict())
                for key in ('valid_formats', 'filename', 'name', 'description', 'content', 'markdown'):
                    if key in attachment:
                        if attachment[key]:
                            the_attachment[key] = attachment[key]
                for the_format in attachment['file']:
                    the_attachment['url'][the_format] = docassemble.base.functions.server.url_finder(attachment['file'][the_format], filename=attachment['filename'] + '.' + extension_of_doc_format[the_format])
                    the_attachment['number'][the_format] = attachment['file'][the_format]
                    the_attachment['filename_with_extension'][the_format] = attachment['filename'] + '.' + extension_of_doc_format[the_format]
                result['attachments'].append(the_attachment)
        for field in self.question.fields:
            the_field = dict()
            the_field['number'] = field.number
            if hasattr(field, 'saveas'):
                the_field['variable_name'] = from_safeid(field.saveas)
                if encode:
                    the_field['variable_name_encoded'] = field.saveas
            for param in ('datatype', 'fieldtype', 'sign', 'inputtype', 'address_autocomplete'):
                if hasattr(field, param):
                    the_field[param] = getattr(field, param)
            if hasattr(field, 'shuffle') and field.shuffle is not False:
                the_field['shuffle'] = True
            if hasattr(field, 'disableothers') and field.disableothers and hasattr(field, 'saveas'):
                the_field['disable_others'] = True
            if hasattr(field, 'uncheckothers') and field.uncheckothers is not False:
                the_field['uncheck_others'] = True
            for key in ('minlength', 'maxlength', 'min', 'max', 'step', 'scale', 'inline width', 'rows', 'accept'):
                if key in self.extras and field.number in self.extras[key]:
                    the_field[key] = self.extras[key][field.number]
            if hasattr(field, 'saveas') and field.saveas in self.embedded:
                the_field['embedded'] = True
            if hasattr(self, 'shuffle'):
                the_field['shuffle'] = self.shuffle
            if field.number in self.defaults:
                the_default = self.defaults[field.number]
                if isinstance(the_default, (string_types, int, bool, float)):
                    the_field['default'] = the_default
            else:
                the_default = None
            if self.question.question_type == 'multiple_choice' or hasattr(field, 'choicetype') or (hasattr(field, 'datatype') and field.datatype in ('object', 'checkboxes', 'object_checkboxes', 'object_radio')):
                the_field['choices'] = self.get_choices_data(field, the_default, the_user_dict, encode=encode)
            if hasattr(field, 'nota'):
                the_field['none_of_the_above'] = self.extras['nota'][field.number]
            the_field['active'] = self.extras['ok'][field.number]
            if field.number in self.extras['required']:
                the_field['required'] = self.extras['required'][field.number]
            if 'validation messages' in self.extras and field.number in self.extras['validation messages']:
                the_field['validation_messages'].update(self.extras['validation messages'][field.number])
            if hasattr(field, 'datatype') and field.datatype in ('file', 'files', 'camera', 'user', 'environment') and 'max_image_size' in self.extras and self.extras['max_image_size']:
                the_field['max_image_size'] = self.extras['max_image_size']
            if hasattr(field, 'extras'):
                if 'ml_group' in field.extras or 'ml_train' in field.extras:
                    the_field['ml_info'] = dict()
                    if 'ml_group' in field.extras:
                        the_field['ml_info']['group_id'] = self.extras['ml_group'][field.number]
                    if 'ml_train' in field.extras:
                        the_field['ml_info']['train'] = self.extras['ml_train'][field.number]
                if 'show_if_var' in field.extras and 'show_if_val' in self.extras:
                    the_field['show_if_sign'] = field.extras['show_if_sign']
                    the_field['show_if_var'] = from_safeid(field.extras['show_if_var'])
                    the_field['show_if_val'] = self.extras['show_if_val'][field.number]
                if 'show_if_js' in self.extras:
                    the_field['show_if_js'] = field.extras['show_if_js']
            if hasattr(field, 'datatype'):
                if field.datatype == 'note' and 'note' in self.extras and field.number in self.extras['note']:
                    the_field['note'] = self.extras['note'][field.number]
                if field.datatype == 'html' and 'html' in self.extras and field.number in self.extras['html']:
                    the_field['html'] = self.extras['html'][field.number]
                if field.number in self.labels:
                    the_field['label'] = self.labels[field.number]
                if field.number in self.helptexts:
                    the_field['helptext'] = self.helptexts[field.number]
            result['fields'].append(the_field)
            if self.question.question_type in ("yesno", "yesnomaybe"):
                the_field['true_label'] = self.question.yes()
                the_field['false_label'] = self.question.no()
            if self.question.question_type == 'yesnomaybe':
                the_field['maybe_label'] = self.question.maybe()
        if len(self.attributions):
            result['attributions'] = [x.rstrip() for x in self.attributions]
        if 'track_location' in self.extras and self.extras['track_location']:
            result['track_location'] = True
        return result
    def get_choices(self, field, the_user_dict):
        question = self.question
        choice_list = list()
        if hasattr(field, 'saveas') and field.saveas is not None:
            saveas = from_safeid(field.saveas)
            if self.question.question_type == "multiple_choice":
                #if hasattr(field, 'has_code') and field.has_code:
                pairlist = list(self.selectcompute[field.number])
                for pair in pairlist:
                    choice_list.append([pair['label'], saveas, pair['key']])
            elif hasattr(field, 'choicetype'):
                if field.choicetype in ('compute', 'manual'):
                    pairlist = list(self.selectcompute[field.number])
                elif field.datatype in ('checkboxes', 'object_checkboxes'):
                    pairlist = list()
                if field.datatype == 'object_checkboxes':
                    for pair in pairlist:
                        choice_list.append([pair['label'], saveas, from_safeid(pair['key'])])
                elif field.datatype in ('object', 'object_radio'):
                    for pair in pairlist:
                        choice_list.append([pair['label'], saveas, from_safeid(pair['key'])])
                elif field.datatype == 'checkboxes':
                    for pair in pairlist:
                        choice_list.append([pair['label'], saveas + "[" + repr(pair['key']) + "]", True])
                else:
                    for pair in pairlist:
                        choice_list.append([pair['label'], saveas, pair['key']])
                if hasattr(field, 'nota') and self.extras['nota'][field.number] is not False:
                    if self.extras['nota'][field.number] is True:
                        formatted_item = word("None of the above")
                    else:
                        formatted_item = self.extras['nota'][field.number]
                    choice_list.append([formatted_item, None, None])
        else:
            indexno = 0
            for choice in self.selectcompute[field.number]:
                choice_list.append([choice['label'], '_internal["answers"][' + repr(question.extended_question_name(the_user_dict)) + ']', indexno])
                indexno += 1
        return choice_list
    def icon_url(self, name):
        the_image = self.question.interview.images.get(name, None)
        if the_image is None:
            return None
        if the_image.attribution is not None:
            self.attributions.add(the_image.attribution)
        url = docassemble.base.functions.server.url_finder(str(the_image.package) + ':' + str(the_image.filename))
        return url
    def get_choices_data(self, field, defaultvalue, the_user_dict, encode=True):
        question = self.question
        choice_list = list()
        if hasattr(field, 'saveas') and field.saveas is not None:
            saveas = from_safeid(field.saveas)
            if self.question.question_type == "multiple_choice":
                pairlist = list(self.selectcompute[field.number])
                for pair in pairlist:
                    item = dict(label=pair['label'], value=pair['key'])
                    if 'help' in pair:
                        item['help'] = pair['help'].rstrip()
                    if 'default' in pair:
                        item['default'] = pair['default']
                    if 'image' in pair:
                        if isinstance(pair['image'], dict):
                            if pair['image']['type'] == 'url':
                                item['image'] = pair['image']['value']
                            else:
                                item['image'] = self.icon_url(pair['image']['value'])
                        else:
                            item['image'] = self.icon_url(pair['image'])
                    choice_list.append(item)
            elif hasattr(field, 'choicetype'):
                if field.choicetype in ('compute', 'manual'):
                    pairlist = list(self.selectcompute[field.number])
                elif field.datatype in ('checkboxes', 'object_checkboxes'):
                    pairlist = list()
                if field.datatype == 'object_checkboxes':
                    for pair in pairlist:
                        item = dict(label=pair['label'], value=from_safeid(pair['key']))
                        if ('default' in pair and pair['default']) or (defaultvalue is not None and isinstance(defaultvalue, (list, set)) and text_type(pair['key']) in defaultvalue) or (isinstance(defaultvalue, dict) and text_type(pair['key']) in defaultvalue and defaultvalue[text_type(pair['key'])]) or (isinstance(defaultvalue, (string_types, int, bool, float)) and text_type(pair['key']) == text_type(defaultvalue)):
                            item['selected'] = True
                        if 'help' in pair:
                            item['help'] = pair['help']
                        choice_list.append(item)
                elif field.datatype in ('object', 'object_radio'):
                    for pair in pairlist:
                        item = dict(label=pair['label'], value=from_safeid(pair['key']))
                        if ('default' in pair and pair['default']) or (defaultvalue is not None and isinstance(defaultvalue, (string_types, int, bool, float)) and text_type(pair['key']) == text_type(defaultvalue)):
                            item['selected'] = True
                        if 'default' in pair:
                            item['default'] = text_type(pair['default'])
                        if 'help' in pair:
                            item['help'] = pair['help']
                        choice_list.append(item)
                elif field.datatype == 'checkboxes':
                    for pair in pairlist:
                        item = dict(label=pair['label'], variable_name=saveas + "[" + repr(pair['key']) + "]", value=True)
                        if encode:
                            item[variable_name_encoded] = safeid(saveas + "[" + repr(pair['key']) + "]")
                        if ('default' in pair and pair['default']) or (defaultvalue is not None and isinstance(defaultvalue, (list, set)) and text_type(pair['key']) in defaultvalue) or (isinstance(defaultvalue, dict) and text_type(pair['key']) in defaultvalue and defaultvalue[text_type(pair['key'])]) or (isinstance(defaultvalue, (string_types, int, bool, float)) and text_type(pair['key']) == text_type(defaultvalue)):
                            item['selected'] = True
                        if 'help' in pair:
                            item['help'] = pair['help']
                        choice_list.append(item)
                else:
                    for pair in pairlist:
                        item = dict(label=pair['label'], value=pair['key'])
                        if ('default' in pair and pair['default']) or (defaultvalue is not None and isinstance(defaultvalue, (string_types, int, bool, float)) and text_type(pair['key']) == text_type(defaultvalue)):
                            item['selected'] = True
                        choice_list.append(item)
                if hasattr(field, 'nota') and self.extras['nota'][field.number] is not False:
                    if self.extras['nota'][field.number] is True:
                        formatted_item = word("None of the above")
                    else:
                        formatted_item = self.extras['nota'][field.number]
                    choice_list.append(dict(label=formatted_item))
        else:
            indexno = 0
            for choice in self.selectcompute[field.number]:
                item = dict(label=choice['label'], variable_name='_internal["answers"][' + repr(question.extended_question_name(the_user_dict)) + ']', value=indexno)
                if encode:
                    item['variable_name_encoded'] = safeid('_internal["answers"][' + repr(question.extended_question_name(the_user_dict)) + ']')
                if 'image' in choice:
                    the_image = self.icon_url(choice['image'])
                    if the_image:
                        item['image'] = the_image
                if 'help' in choice:
                    item['help'] = choice['help']
                if 'default' in choice:
                    item['default'] = choice['default']
                choice_list.append(item)
                indexno += 1
        return choice_list
    
# def new_counter(initial_value=0):
#     d = {'counter': initial_value}
#     def f():
#         return_value = d['counter']
#         d['counter'] += 1
#         return(return_value)
#     return f

# increment_question_counter = new_counter()

class TextObject(object):
    def __init__(self, x, names_used=set()):
        self.original_text = x
        if isinstance(x, string_types) and match_mako.search(x):
            self.template = MakoTemplate(x, strict_undefined=True, input_encoding='utf-8')
            for x in self.template.names_used:
                if x not in self.template.names_set:
                    names_used.add(x)
            self.uses_mako = True
        else:
            self.uses_mako = False
    def text(self, the_user_dict):
        if self.uses_mako:
            return(self.template.render(**the_user_dict))
        else:
            return(self.original_text)

def safeid(text):
    return codecs.encode(text.encode('utf8'), 'base64').decode().replace('\n', '')

def from_safeid(text):
    return(codecs.decode(bytearray(text, encoding='utf-8'), 'base64').decode('utf8'))

class Field:
    def __init__(self, data):
        if 'number' in data:
            self.number = data['number']
        else:
            self.number = 0
        if 'saveas' in data:
            self.saveas = safeid(data['saveas'])
        if 'saveas_code' in data:
            self.saveas_code = data['saveas_code']
        if 'showif_code' in data:
            self.showif_code = data['showif_code']
        if 'action' in data:
            self.action = data['action']
        if 'label' in data:
            self.label = data['label']
        if 'type' in data:
            self.datatype = data['type']
        if 'choicetype' in data:
            self.choicetype = data['choicetype']
        if 'disable others' in data:
            self.disableothers = data['disable others']
        if 'uncheck others' in data:
            self.uncheckothers = data['uncheck others']
        if 'default' in data:
            self.default = data['default']
        if 'hint' in data:
            self.hint = data['hint']
        if 'data' in data:
            self.data = data['data']
        if 'help' in data:
            self.helptext = data['help']
        if 'validate' in data:
            self.validate = data['validate']
        if 'validation messages' in data:
            self.validation_messages = data['validation messages']
        if 'address_autocomplete' in data:
            self.address_autocomplete = data['address_autocomplete']
        if 'max_image_size' in data:
            self.max_image_size = data['max_image_size']
        if 'accept' in data:
            self.accept = data['accept']
        if 'rows' in data:
            self.rows = data['rows']
        if 'object_labeler' in data:
            self.object_labeler = data['object_labeler']
        if 'extras' in data:
            self.extras = data['extras']
        if 'selections' in data:
            self.selections = data['selections']
        if 'boolean' in data:
            self.datatype = 'boolean'
            self.sign = data['boolean']
            if 'type' in data:
                self.inputtype = data['type']
        if 'threestate' in data:
            self.datatype = 'threestate'
            self.sign = data['threestate']
            if 'type' in data:
                self.inputtype = data['type']
        if 'choices' in data:
            self.fieldtype = 'multiple_choice'
            self.choices = data['choices']
        if 'inputtype' in data:
            self.inputtype = data['inputtype']
        if 'has_code' in data:
            self.has_code = True
        # if 'script' in data:
        #     self.script = data['script']
        # if 'css' in data:
        #     self.css = data['css']
        if 'shuffle' in data:
            self.shuffle = data['shuffle']
        if 'nota' in data:
            self.nota = data['nota']
        if 'required' in data:
            self.required = data['required']
        else:
            self.required = True

    def validation_message(self, validation_type, status, default_message, parameters=None):
        message = None
        if 'validation messages' in status.extras and self.number in status.extras['validation messages']:
            validation_type_tail = re.sub(r'.* ', '', validation_type)
            if validation_type in status.extras['validation messages'][self.number]:
                message = status.extras['validation messages'][self.number][validation_type]
            elif validation_type != validation_type_tail and validation_type_tail in status.extras['validation messages'][self.number]:
                message = status.extras['validation messages'][self.number][validation_type_tail]
        if message is None and status.question.language in status.question.interview.default_validation_messages and validation_type in status.question.interview.default_validation_messages[status.question.language]:
            message = status.question.interview.default_validation_messages[status.question.language][validation_type]
        if message is None:
            message = default_message
        if parameters is not None and len(parameters) > 0:
            try:
                message = message % parameters
            except TypeError:
                pass
        return message

def recursive_eval_dataobject(target, the_user_dict):
    if isinstance(target, dict) or (hasattr(target, 'elements') and isinstance(target.elements, dict)):
        new_dict = dict()
        for key, val in target.items():
            new_dict[key] = recursive_eval_dataobject(val, the_user_dict)
        return new_dict
    if isinstance(target, list) or (hasattr(target, 'elements') and isinstance(target.elements, list)):
        new_list = list()
        for val in target.__iter__():
            new_list.append(recursive_eval_dataobject(val, the_user_dict))
        return new_list
    if isinstance(target, set) or (hasattr(target, 'elements') and isinstance(target.elements, set)):
        new_set = set()
        for val in target.__iter__():
            new_set.add(recursive_eval_dataobject(val, the_user_dict))
        return new_set
    if isinstance(target, (bool, float, int, NoneType)):
        return target
    if isinstance(target, TextObject):
        return target.text(the_user_dict)
    else:
        raise DAError("recursive_eval_dataobject: expected a TextObject, but found a " + str(type(target)))

def recursive_eval_data_from_code(target, the_user_dict):
    if isinstance(target, dict):
        new_dict = dict()
        for key, val in target.items():
            new_dict[key] = recursive_eval_data_from_code(val, the_user_dict)
        return new_dict
    if isinstance(target, list):
        new_list = list()
        for val in target:
            new_list.append(recursive_eval_data_from_code(val, the_user_dict))
        return new_list
    if isinstance(target, set):
        new_set = set()
        for val in target:
            new_set.add(recursive_eval_data_from_code(val, the_user_dict))
        return new_set
    if isinstance(target, CodeType):
        return eval(target, the_user_dict)
    else:
        return target
    
def recursive_textobject(target, names_used):
    if isinstance(target, dict) or (hasattr(target, 'elements') and isinstance(target.elements, dict)):
        new_dict = dict()
        for key, val in target.items():
            new_dict[key] = recursive_textobject(val, names_used)
        return new_dict
    if isinstance(target, list) or (hasattr(target, 'elements') and isinstance(target.elements, list)):
        new_list = list()
        for val in target.__iter__():
            new_list.append(recursive_textobject(val, names_used))
        return new_list
    if isinstance(target, set) or (hasattr(target, 'elements') and isinstance(target.elements, set)):
        new_set = set()
        for val in target.__iter__():
            new_set.add(recursive_textobject(val, names_used))
        return new_set
    return TextObject(text_type(target), names_used=names_used)

def recursive_eval_textobject(target, the_user_dict, question, tpl):
    if isinstance(target, dict) or (hasattr(target, 'elements') and isinstance(target.elements, dict)):
        new_dict = dict()
        for key, val in target.items():
            new_dict[key] = recursive_eval_textobject(val, the_user_dict, question, tpl)
        return new_dict
    if isinstance(target, list) or (hasattr(target, 'elements') and isinstance(target.elements, list)):
        new_list = list()
        for val in target.__iter__():
            new_list.append(recursive_eval_textobject(val, the_user_dict, question, tpl))
        return new_list
    if isinstance(target, set) or (hasattr(target, 'elements') and isinstance(target.elements, set)):
        new_set = set()
        for val in target.__iter__():
            new_set.add(recursive_eval_textobject(val, the_user_dict, question, tpl))
        return new_set
    if isinstance(target, (bool, NoneType)):
        return target
    if isinstance(target, TextObject):
        text = target.text(the_user_dict)
        return docassemble.base.file_docx.transform_for_docx(text, question, tpl)
    else:
        raise DAError("recursive_eval_textobject: expected a TextObject, but found a " + str(type(target)))

def fix_quotes(match):
    instring = match.group(1)
    n = len(instring)
    output = ''
    for i in range(n):
        if instring[i] == u'\u201c' or instring[i] == u'\u201d':
            output += '"'
        elif instring[i] == u'\u2018' or instring[i] == u'\u2019':
            output += "'"
        else:
            output += instring[i]
    return output

def docx_variable_fix(variable):
    variable = re.sub(r'\\', '', variable)
    variable = re.sub(r'^([A-Za-z\_][A-Za-z\_0-9]*).*', r'\1', variable)
    return variable

class FileInPackage:
    def __init__(self, fileref, area, package):
        if area == 'template' and not isinstance(fileref, dict):
            docassemble.base.functions.package_template_filename(fileref, package=package)
        self.fileref = fileref
        if isinstance(self.fileref, dict):
            self.is_code = True
            if 'code' not in self.fileref:
                raise DAError("A docx or pdf template file expressed in the form of a dictionary must have 'code' as the key" + str(self.fileref))
            self.code = compile(self.fileref['code'], '<template file code>', 'eval')
        else:
            self.is_code = False
        self.area = area
        self.package = package
    def path(self, the_user_dict=dict()):
        if self.area == 'template':
            if self.is_code:
                if len(the_user_dict) == 0:
                    raise Exception("FileInPackage.path: called with empty dict")
                the_file_ref = eval(self.code, the_user_dict)
                if the_file_ref.__class__.__name__ == 'DAFile':
                    the_file_ref = the_file_ref.path()
                elif the_file_ref.__class__.__name__ == 'DAFileList' and len(the_file_ref.elements) > 0:
                    the_file_ref = the_file_ref.elements[0].path()
                elif the_file_ref.__class__.__name__ == 'DAStaticFile':
                    the_file_ref = the_file_ref.path()
                elif re.search(r'^https?://', str(the_file_ref)):
                    temp_template_file = tempfile.NamedTemporaryFile(prefix="datemp", mode="wb", delete=False)
                    try:
                        urlretrieve(str(the_file_ref), temp_template_file.name)
                    except Exception as err:
                        raise DAError("FileInPackage: error downloading " + str(the_file_ref) + ": " + str(err))
                    the_file_ref = temp_template_file.name
                if not str(the_file_ref).startswith('/'):
                    the_file_ref = docassemble.base.functions.package_template_filename(str(the_file_ref), package=self.package)
                return the_file_ref
            else:
                return docassemble.base.functions.package_template_filename(self.fileref, package=self.package)

class FileOnServer:
    def __init__(self, fileref, question):
        self.fileref = fileref
        self.question = question
    def path(self):
        info = docassemble.base.functions.server.file_finder(self.fileref, question=self.question)
        if 'fullpath' in info and info['fullpath']:
            return info['fullpath']
        raise DAError("Could not find the file " + str(self.fileref))

class Question:
    def idebug(self, data):
        if hasattr(self, 'from_source') and hasattr(self, 'package'):
            return "\nIn file " + str(self.from_source.path) + " from package " + str(self.package) + ":\n\n" + yaml.dump(data)
        else:
            return yaml.dump(data)
    def __init__(self, orig_data, caller, **kwargs):
        if not isinstance(orig_data, dict):
            raise DAError("A block must be in the form of a dictionary." + self.idebug(orig_data))
        data = dict()
        for key, value in orig_data.items():
            data[key.lower()] = value
        should_append = True
        if 'register_target' in kwargs:
            register_target = kwargs['register_target']
            main_list = False
        else:
            register_target = self
            main_list = True
        self.from_source = kwargs.get('source', None)
        self.package = kwargs.get('package', None)
        self.interview = caller
        if self.interview.debug:
            self.source_code = kwargs.get('source_code', None)
        self.fields = []
        self.attachments = []
        self.is_generic = False
        self.name = None
        self.role = list()
        self.condition = list()
        self.terms = dict()
        self.autoterms = dict()
        self.need = None
        self.scan_for_variables = True
        self.embeds = False
        self.helptext = None
        self.subcontent = None
        self.reload_after = None
        self.continuelabel = None
        self.backbuttonlabel = None
        self.helplabel = None
        self.progress = None
        self.section = None
        self.script = None
        self.css = None
        self.checkin = None
        self.target = None
        self.decorations = None
        self.audiovideo = None
        self.compute_attachment = None
        self.can_go_back = True
        self.fields_used = set()
        self.names_used = set()
        self.mako_names = set()
        self.reconsider = list()
        self.undefine = list()
        self.validation_code = None
        num_directives = 0
        for directive in ('yesno', 'noyes', 'yesnomaybe', 'noyesmaybe', 'fields', 'buttons', 'choices', 'dropdown', 'combobox', 'signature', 'review'):
            if directive in data:
                num_directives += 1
        if num_directives > 1:
            raise DAError("There can only be one directive in a question.  You had more than one.\nThe directives are yesno, noyes, yesnomaybe, noyesmaybe, fields, buttons, choices, dropdown, combobox, and signature." + self.idebug(data))
        if num_directives > 0 and 'question' not in data:
            raise DAError("This block is missing a 'question' directive." + self.idebug(data))
        if 'features' in data:
            should_append = False
            if not isinstance(data['features'], dict):
                raise DAError("A features section must be a dictionary." + self.idebug(data))
            if 'table width' in data['features']:
                if not isinstance(data['features']['table width'], int):
                    raise DAError("Table width in features must be an integer." + self.idebug(data))
                self.interview.table_width = data['features']['table width']
            if 'progress bar' in data['features']:
                self.interview.use_progress_bar = True if data['features']['progress bar'] else False
            if 'show progress bar percentage' in data['features'] and data['features']['show progress bar percentage']:
                self.interview.show_progress_bar_percentage = True
            if 'progress bar method' in data['features'] and isinstance(data['features']['progress bar method'], text_type):
                self.interview.progress_bar_method = data['features']['progress bar method']
            if 'progress bar multiplier' in data['features'] and isinstance(data['features']['progress bar multiplier'], (int, float)):
                if data['features']['progress bar multiplier'] <= 0.0 or data['features']['progress bar multiplier'] >= 1.0:
                    raise DAError("progress bar multiplier in features must be between 0 and 1." + self.idebug(data))
                self.interview.progress_bar_method = data['features']['progress bar multiplier']
            if 'question back button' in data['features']:
                self.interview.question_back_button = True if data['features']['question back button'] else False
            if 'question help button' in data['features']:
                self.interview.question_help_button = True if data['features']['question help button'] else False
            if 'navigation back button' in data['features']:
                self.interview.navigation_back_button = True if data['features']['navigation back button'] else False
            if 'go full screen' in data['features'] and data['features']['go full screen']:
                self.interview.force_fullscreen = data['features']['go full screen']
            if 'navigation' in data['features'] and data['features']['navigation']:
                self.interview.use_navigation = data['features']['navigation']
            if 'centered' in data['features'] and not data['features']['centered']:
                self.interview.flush_left = True
            if 'maximum image size' in data['features']:
                self.interview.max_image_size = eval(str(data['features']['maximum image size']))
            if 'debug' in data['features'] and isinstance(data['features']['debug'], bool):
                self.interview.debug = data['features']['debug']
            if 'cache documents' in data['features']:
                self.interview.cache_documents = data['features']['cache documents']
            if 'loop limit' in data['features']:
                self.interview.loop_limit = data['features']['loop limit']
            if 'recursion limit' in data['features']:
                self.interview.recursion_limit = data['features']['recursion limit']
            if 'pdf/a' in data['features'] and data['features']['pdf/a'] in (True, False):
                self.interview.use_pdf_a = data['features']['pdf/a']
            if 'tagged pdf' in data['features'] and data['features']['tagged pdf'] in (True, False):
                self.interview.use_tagged_pdf = data['features']['tagged pdf']
            if 'bootstrap theme' in data['features'] and data['features']['bootstrap theme']:
                self.interview.bootstrap_theme = data['features']['bootstrap theme']
            if 'inverse navbar' in data['features']:
                self.interview.options['inverse navbar'] = data['features']['inverse navbar']
            if 'hide navbar' in data['features']:
                self.interview.options['hide navbar'] = data['features']['hide navbar']
            if 'hide standard menu' in data['features']:
                self.interview.options['hide standard menu'] = data['features']['hide standard menu']
            if 'checkin interval' in data['features']:
                if not isinstance(data['features']['checkin interval'], int):
                    raise DAError("A features section checkin interval entry must be an integer." + self.idebug(data))
                if data['features']['checkin interval'] > 0 and data['features']['checkin interval'] < 1000:
                    raise DAError("A features section checkin interval entry must be at least 1000, if not 0." + self.idebug(data))
                self.interview.options['checkin interval'] = data['features']['checkin interval']
            for key in ('javascript', 'css'):
                if key in data['features']:
                    if isinstance(data['features'][key], list):
                        the_list = data['features'][key]
                    elif isinstance(data['features'][key], dict):
                        raise DAError("A features section " + key + " entry must be a list or plain text." + self.idebug(data))
                    else:
                        the_list = [data['features'][key]]
                    for the_file in the_list:
                        if key not in self.interview.external_files:
                            self.interview.external_files[key] = list()
                        self.interview.external_files[key].append((self.from_source.get_package(), the_file))
        if 'scan for variables' in data:
            if data['scan for variables']:
                self.scan_for_variables = True
            else:
                self.scan_for_variables = False
        if 'only sets' in data:
            if isinstance(data['only sets'], string_types):
                self.fields_used.add(data['only sets'])
            elif isinstance(data['only sets'], list):
                for key in data['only sets']:
                    self.fields_used.add(key)
            else:
                raise DAError("An only sets phrase must be text or a list." + self.idebug(data))
            self.scan_for_variables = False
        if 'question' in data and 'code' in data:
            raise DAError("A block can be a question block or a code block but cannot be both at the same time." + self.idebug(data))
        if 'event' in data:
            if 'field' in data or 'fields' in data or 'yesno' in data or 'noyes' in data:
                raise DAError("The 'event' designator is for special screens that do not gather information and can only be used with 'buttons' or with no other controls." + self.idebug(data))
        if 'default language' in data:
            should_append = False
            self.from_source.set_language(data['default language'])
        if 'sections' in data:
            should_append = False
            if not isinstance(data['sections'], list):
                raise DAError("A sections list must be a list." + self.idebug(data))
            if 'language' in data:
                the_language = data['language']
            else:
                the_language = '*'
            self.interview.sections[the_language] = data['sections']
        if 'progressive' in data:
            if 'sections' not in data:
                raise DAError("A progressive directive can only be used with sections." + self.idebug(data))
            if not isinstance(data['progressive'], bool):
                raise DAError("A progressive directive can only be true or false." + self.idebug(data))
            self.interview.sections_progressive = data['progressive']
        if 'section' in data:
            if 'question' not in data:
                raise DAError("You can only set the section from a question." + self.idebug(data))
            self.section = data['section']
        if 'machine learning storage' in data:
            should_append = False
            new_storage = data['machine learning storage']
            if not new_storage.endswith('.json'):
                raise DAError("Invalid machine learning storage entry '" + str(data['machine learning storage']) + ".'  A machine learning storage entry must refer to a file ending in .json." + self.idebug(data))
            parts = new_storage.split(":")
            if len(parts) == 1:
                new_storage = re.sub(r'^data/sources/', '', new_storage)
                the_package = self.from_source.get_package()
                if the_package is not None:
                    new_storage = self.from_source.get_package() + ':data/sources/' + new_storage
                self.interview.set_ml_store(new_storage)
            elif len(parts) == 2 and parts[0].startswith('docassemble.') and parts[1].startswith('data/sources/'):
                self.interview.set_ml_store(data['machine learning storage'])
            else:
                raise DAError("Invalid machine learning storage entry: " + str(data['machine learning storage']) + self.idebug(data))
        if 'language' in data:
            self.language = data['language']
        else:
            self.language = self.from_source.get_language()
        if 'prevent going back' in data and data['prevent going back']:
            self.can_go_back = False
        if 'back button' in data:
            if isinstance(data['back button'], (bool, NoneType)):
                self.back_button = data['back button']
            else:
                self.back_button = compile(data['back button'], '<back button>', 'eval')
        else:
            self.back_button = None
        if 'usedefs' in data:
            defs = list()
            if isinstance(data['usedefs'], list):
                usedefs = data['usedefs']
            else:
                usedefs = [data['usedefs']]
            for usedef in usedefs:
                if isinstance(usedef, (dict, list, set, bool)):
                    raise DAError("A usedefs section must consist of a list of strings or a single string." + self.idebug(data))
                if usedef not in self.interview.defs:
                    raise DAError('Referred to a non-existent def "' + usedef + '."  All defs must be defined before they are used.' + self.idebug(data))
                defs.extend(self.interview.defs[usedef])
            definitions = "\n".join(defs) + "\n";
        else:
            definitions = "";        
        if 'continue button label' in data:
            if 'yesno' in data or 'noyes' in data or 'yesnomaybe' in data or 'noyesmaybe' in data or 'buttons' in data:
                raise DAError("You cannot set a continue button label if the type of question is yesno, noyes, yesnomaybe, noyesmaybe, or buttons." + self.idebug(data))
            self.continuelabel = TextObject(definitions + text_type(data['continue button label']), names_used=self.mako_names)
        if 'resume button label' in data:
            if 'review' not in data:
                raise DAError("You cannot set a resume button label if the type of question is not review." + self.idebug(data))
            self.continuelabel = TextObject(definitions + text_type(data['resume button label']), names_used=self.mako_names)
        if 'back button label' in data:
            self.backbuttonlabel = TextObject(definitions + text_type(data['back button label']), names_used=self.mako_names)
        if 'skip undefined' in data:
            if 'review' not in data:
                raise DAError("You cannot set the skip undefined directive if the type of question is not review." + self.idebug(data))
            if not data['skip undefined']:
                self.skip_undefined = False
        if 'mandatory' in data:
            if 'question' not in data and 'code' not in data and 'objects' not in data and 'attachment' not in data and 'data' not in data and 'data from code' not in data:
                raise DAError("You cannot use the mandatory modifier on this type of block." + self.idebug(data))
            if data['mandatory'] is True:
                self.is_mandatory = True
                self.mandatory_code = None
            elif data['mandatory'] in (False, None):
                self.is_mandatory = False
                self.mandatory_code = None
            else:
                self.is_mandatory = False
                if isinstance(data['mandatory'], string_types):
                    self.mandatory_code = compile(data['mandatory'], '<mandatory code>', 'eval')
                    self.find_fields_in(data['mandatory'])
                else:
                    self.mandatory_code = None
        else:
            self.is_mandatory = False
            self.mandatory_code = None
        if 'attachment options' in data:
            should_append = False
            if not isinstance(data['attachment options'], list):
                data['attachment options'] = [data['attachment options']]
            for attachment_option in data['attachment options']:
                if not isinstance(attachment_option, dict):
                    raise DAError("An attachment option must a dictionary." + self.idebug(data))
                for key in attachment_option:
                    value = attachment_option[key]
                    if key == 'initial yaml':
                        if 'initial_yaml' not in self.interview.attachment_options:
                            self.interview.attachment_options['initial_yaml'] = list()
                        if isinstance(value, list):
                            the_list = value
                        else:
                            the_list = [value]
                        for yaml_file in the_list:
                            if not isinstance(yaml_file, string_types):
                                raise DAError('An initial yaml file must be a string.' + self.idebug(data))
                            self.interview.attachment_options['initial_yaml'].append(FileInPackage(yaml_file, 'template', self.package))
                    elif key == 'additional yaml':
                        if 'additional_yaml' not in self.interview.attachment_options:
                            self.interview.attachment_options['additional_yaml'] = list()
                        if isinstance(value, list):
                            the_list = value
                        else:
                            the_list = [value]
                        for yaml_file in the_list:
                            if not isinstance(yaml_file, string_types):
                                raise DAError('An additional yaml file must be a string.' + self.idebug(data))
                            self.interview.attachment_options['additional_yaml'].append(FileInPackage(yaml_file, 'template', self.package))
                    elif key == 'template file':
                        if not isinstance(value, string_types):
                            raise DAError('The template file must be a string.' + self.idebug(data))
                        self.interview.attachment_options['template_file'] = FileInPackage(value, 'template', self.package)
                    elif key == 'rtf template file':
                        if not isinstance(value, string_types):
                            raise DAError('The rtf template file must be a string.' + self.idebug(data))
                        self.interview.attachment_options['rtf_template_file'] = FileInPackage(value, 'template', self.package)
                    elif key == 'docx reference file':
                        if not isinstance(value, string_types):
                            raise DAError('The docx reference file must be a string.' + self.idebug(data))
                        self.interview.attachment_options['docx_reference_file'] = FileInPackage(value, 'template', self.package)
        if 'script' in data:
            if not isinstance(data['script'], string_types):
                raise DAError("A script section must be plain text." + self.idebug(data))
            self.script = TextObject(definitions + text_type(data['script']), names_used=self.mako_names)
        if 'css' in data:
            if not isinstance(data['css'], string_types):
                raise DAError("A css section must be plain text." + self.idebug(data))
            self.css = TextObject(definitions + text_type(data['css']), names_used=self.mako_names)
        if 'initial' in data and 'code' not in data:
            raise DAError("Only a code block can be marked as initial." + self.idebug(data))
        if 'initial' in data or 'default role' in data:
            if 'default role' in data or data['initial'] is True:
                self.is_initial = True
                self.initial_code = None
            elif data['initial'] in (False, None):
                self.is_initial = False
                self.initial_code = None
            else:
                self.is_initial = False
                if isinstance(data['initial'], string_types):
                    self.initial_code = compile(data['initial'], '<initial code>', 'eval')
                    self.find_fields_in(data['initial'])
                else:
                    self.initial_code = None
        else:
            self.is_initial = False
            self.initial_code = None
        if 'command' in data and data['command'] in ('exit', 'logout', 'exit_logout', 'continue', 'restart', 'leave', 'refresh', 'signin', 'register', 'new_session'):
            self.question_type = data['command']
            self.content = TextObject(data.get('url', ''), names_used=self.mako_names)
            return
        if 'objects from file' in data:
            if not isinstance(data['objects from file'], list):
                data['objects from file'] = [data['objects from file']]
            self.question_type = 'objects_from_file'
            self.objects_from_file = data['objects from file']
            for item in data['objects from file']:
                if isinstance(item, dict):
                    for key in item:
                        self.fields.append(Field({'saveas': key, 'type': 'object_from_file', 'file': item[key]}))
                        if self.scan_for_variables:
                            self.fields_used.add(key)
                else:
                    raise DAError("An objects section cannot contain a nested list." + self.idebug(data))
        if 'data' in data and 'variable name' in data:
            if not isinstance(data['variable name'], string_types):
                raise DAError("A data block variable name must be plain text." + self.idebug(data))
            if self.scan_for_variables:
                self.fields_used.add(data['variable name'].strip())
            self.question_type = 'data'
            self.fields.append(Field({'saveas': data['variable name'].strip(), 'type': 'data', 'data': self.recursive_dataobject(data['data'])}))
        if 'data from code' in data and 'variable name' in data:
            if not isinstance(data['variable name'], string_types):
                raise DAError("A data from code block variable name must be plain text." + self.idebug(data))
            if self.scan_for_variables:
                self.fields_used.add(data['variable name'])
            self.question_type = 'data_from_code'
            self.fields.append(Field({'saveas': data['variable name'], 'type': 'data_from_code', 'data': self.recursive_data_from_code(data['data from code'])}))
        if 'objects' in data:
            if not isinstance(data['objects'], list):
                data['objects'] = [data['objects']]
                #raise DAError("An objects section must be organized as a list." + self.idebug(data))
            self.question_type = 'objects'
            self.objects = data['objects']
            for item in data['objects']:
                if isinstance(item, dict):
                    for key in item:
                        self.fields.append(Field({'saveas': key, 'type': 'object', 'objecttype': item[key]}))
                        if self.scan_for_variables:
                            self.fields_used.add(key)
                else:
                    raise DAError("An objects section cannot contain a nested list." + self.idebug(data))
        if 'id' in data:
            # if text_type(data['id']) in self.interview.ids_in_use:
            #     raise DAError("The id " + text_type(data['id']) + " is already in use by another block.  Id names must be unique." + self.idebug(data))
            self.id = text_type(data['id']).strip()
            self.interview.ids_in_use.add(self.id)
            self.interview.questions_by_id[self.id] = self
        if 'supersedes' in data:
            if not isinstance(data['supersedes'], list):
                supersedes_list = [text_type(data['supersedes'])]
            else:
                supersedes_list = [text_type(x) for x in data['supersedes']]
            self.interview.id_orderings.append(dict(type="supersedes", question=self, supersedes=supersedes_list))
        if 'order' in data:
            should_append = False
            if 'question' in data or 'code' in data or 'attachment' in data or 'attachments' in data or 'template' in data:
                raise DAError("An 'order' block cannot be combined with another type of block." + self.idebug(data))
            if not isinstance(data['order'], list):
                raise DAError("An 'order' block must be a list." + self.idebug(data))
            self.interview.id_orderings.append(dict(type="order", order=[text_type(x) for x in data['order']]))
        for key in ('image sets', 'images'):
            if key not in data:
                continue
            should_append = False
            if not isinstance(data[key], dict):
                raise DAError("The '" + key + "' section needs to be a dictionary, not a list or text." + self.idebug(data))
            if key == 'images':
                data[key] = {'unspecified': {'images': data[key]}}
            elif 'images' in data[key] and 'attribution' in data[key]:
                data[key] = {'unspecified': data[key]}
            for setname, image_set in data[key].items():
                if not isinstance(image_set, dict):
                    if key == 'image sets':
                        raise DAError("Each item in the 'image sets' section needs to be a dictionary, not a list.  Each dictionary item should have an 'images' definition (which can be a dictionary or list) and an optional 'attribution' definition (which must be text)." + self.idebug(data))
                    else:
                        raise DAError("Each item in the 'images' section needs to be a dictionary, not a list." + self.idebug(data))
                if 'attribution' in image_set:
                    if not isinstance(image_set['attribution'], string_types):
                        raise DAError("An attribution in an 'image set' section cannot be a dictionary or a list." + self.idebug(data))
                    attribution = re.sub(r'\n', ' ', image_set['attribution'].strip())
                else:
                    attribution = None
                if 'images' in image_set:
                    if isinstance(image_set['images'], list):
                        image_list = image_set['images']
                    elif isinstance(image_set['images'], dict):
                        image_list = [image_set['images']]
                    else:
                        if key == 'image set':
                            raise DAError("An 'images' definition in an 'image set' item must be a dictionary or a list." + self.idebug(data))
                        else:
                            raise DAError("An 'images' section must be a dictionary or a list." + self.idebug(data))                            
                    for image in image_list:
                        if not isinstance(image, dict):
                            the_image = {str(image): str(image)}
                        else:
                            the_image = image
                        for key, value in the_image.items():
                            self.interview.images[key] = PackageImage(filename=value, attribution=attribution, setname=setname, package=self.package)
        if 'def' in data:
            should_append = False
            if not isinstance(data['def'], string_types):
                raise DAError("A def name must be a string." + self.idebug(data))
            if data['def'] not in self.interview.defs:
                self.interview.defs[data['def']] = list()
            if 'mako' in data:
                if isinstance(data['mako'], string_types):
                    list_of_defs = [data['mako']]
                elif isinstance(data['mako'], list):
                    list_of_defs = data['mako']
                else:
                    raise DAError("A mako template definition must be a string or a list of strings." + self.idebug(data))
                for definition in list_of_defs:
                    if not isinstance(definition, string_types):
                        raise DAError("A mako template definition must be a string." + self.idebug(data))
                    self.interview.defs[data['def']].append(definition)
        if 'interview help' in data:
            should_append = False
            if isinstance(data['interview help'], list):
                raise DAError("An interview help section must not be in the form of a list." + self.idebug(data))
            elif not isinstance(data['interview help'], dict):
                data['interview help'] = {'content': text_type(data['interview help'])}
            audiovideo = list()
            if 'label' in data['interview help']:
                data['interview help']['label'] = text_type(data['interview help']['label'])
            if 'audio' in data['interview help']:
                if not isinstance(data['interview help']['audio'], list):
                    the_list = [data['interview help']['audio']]
                else:
                    the_list = data['interview help']['audio']
                audiovideo = list()
                for the_item in the_list:
                    if isinstance(the_item, (list, dict)):
                        raise DAError("An interview help audio section must be in the form of a text item or a list of text items." + self.idebug(data))
                    audiovideo.append({'text': TextObject(definitions + text_type(data['interview help']['audio']), names_used=self.mako_names), 'package': self.package, 'type': 'audio'})
            if 'video' in data['interview help']:
                if not isinstance(data['interview help']['video'], list):
                    the_list = [data['interview help']['video']]
                else:
                    the_list = data['interview help']['video']
                for the_item in the_list:
                    if isinstance(the_item, (list, dict)):
                        raise DAError("An interview help video section must be in the form of a text item or a list of text items." + self.idebug(data))
                    audiovideo.append({'text': TextObject(definitions + text_type(data['interview help']['video']), names_used=self.mako_names), 'package': self.package, 'type': 'video'})
            if 'video' not in data['interview help'] and 'audio' not in data['interview help']:
                audiovideo = None
            if 'heading' in data['interview help']:
                if not isinstance(data['interview help']['heading'], (dict, list)):
                    help_heading = TextObject(definitions + text_type(data['interview help']['heading']), names_used=self.mako_names)
                else:
                    raise DAError("A heading within an interview help section must be text, not a list or a dictionary." + self.idebug(data))
            else:
                help_heading = None
            if 'content' in data['interview help']:
                if not isinstance(data['interview help']['content'], (dict, list)):
                    help_content = TextObject(definitions + text_type(data['interview help']['content']), names_used=self.mako_names)
                else:
                    raise DAError("Help content must be text, not a list or a dictionary." + self.idebug(data))
            else:
                raise DAError("No content section was found in an interview help section." + self.idebug(data))
            if 'label' in data['interview help']:
                if not isinstance(data['interview help']['label'], (dict, list)):
                    help_label = TextObject(definitions + text_type(data['interview help']['label']), names_used=self.mako_names)
                else:
                    raise DAError("Help label must be text, not a list or a dictionary." + self.idebug(data))
            else:
                help_label = None
            if self.language not in self.interview.helptext:
                self.interview.helptext[self.language] = list()
            self.interview.helptext[self.language].append({'content': help_content, 'heading': help_heading, 'audiovideo': audiovideo, 'label': help_label, 'from': 'interview'})
        if 'default screen parts' in data:
            should_append = False
            if not isinstance(data['default screen parts'], dict):
                raise DAError("A default screen parts block must be in the form of a dictionary." + self.idebug(data))
            if self.language not in self.interview.default_screen_parts:
                self.interview.default_screen_parts[self.language] = dict()
            for key, content in data['default screen parts'].items():
                if content is None:
                    if key in self.interview.default_screen_parts[self.language]:
                        del self.interview.default_screen_parts[self.language][key]
                else:
                    if not (isinstance(key, string_types) and isinstance(content, string_types)):
                        raise DAError("A default screen parts block must be a dictionary of text keys and text values." + self.idebug(data))
                self.interview.default_screen_parts[self.language][key] = TextObject(definitions + text_type(content.strip()), names_used=self.mako_names)
        if 'default validation messages' in data:
            should_append = False
            if not isinstance(data['default validation messages'], dict):
                raise DAError("A default validation messages block must be in the form of a dictionary." + self.idebug(data))
            if self.language not in self.interview.default_validation_messages:
                self.interview.default_validation_messages[self.language] = dict()
            for validation_key, validation_message in data['default validation messages'].items():
                if not (isinstance(validation_key, string_types) and isinstance(validation_message, string_types)):
                    raise DAError("A validation messages block must be a dictionary of text keys and text values." + self.idebug(data))
                self.interview.default_validation_messages[self.language][validation_key] = validation_message.strip()
        if 'generic object' in data:
            self.is_generic = True
            #self.is_generic_list = False
            self.generic_object = data['generic object']
        elif 'generic list object' in data:
            self.is_generic = True
            #self.is_generic_list = True
            self.generic_object = data['generic list object']
        else:
            self.is_generic = False
        if 'comment' in data and len(data) == 1:
            should_append = False
        if 'metadata' in data:
            for key in data:
                if key not in ('metadata', 'comment'):
                    raise DAError("A metadata directive cannot be mixed with other directives." + self.idebug(data))
            should_append = False
            if isinstance(data['metadata'], dict):
                data['metadata']['origin_path'] = self.from_source.path
                self.interview.metadata.append(data['metadata'])
            else:
                raise DAError("A metadata section must be organized as a dictionary." + self.idebug(data))
        if 'modules' in data:
            if isinstance(data['modules'], string_types):
                data['modules'] = [data['modules']]
            if isinstance(data['modules'], list):
                if 'docassemble.base.util' in data['modules'] or 'docassemble.base.legal' in data['modules']:
                    # logmessage("setting imports_util to true")
                    self.interview.imports_util = True
                # else:
                #     logmessage("not setting imports_util to true")                    
                self.question_type = 'modules'
                self.module_list = data['modules']
            else:
                raise DAError("A modules section must be organized as a list." + self.idebug(data))
        if 'reset' in data:
            #logmessage("Found a reset")
            if isinstance(data['reset'], string_types):
                data['reset'] = [data['reset']]
            if isinstance(data['reset'], list):
                self.question_type = 'reset'
                self.reset_list = data['reset']
            else:
                raise DAError("A reset section must be organized as a list." + self.idebug(data))
        if 'imports' in data:
            if isinstance(data['imports'], string_types):
                data['imports'] = [data['imports']]
            if isinstance(data['imports'], list):
                self.question_type = 'imports'
                self.module_list = data['imports']
            else:
                raise DAError("An imports section must be organized as a list." + self.idebug(data))
        if 'terms' in data and 'question' in data:
            if not isinstance(data['terms'], (dict, list)):
                raise DAError("Terms must be organized as a dictionary or a list." + self.idebug(data))
            if isinstance(data['terms'], dict):
                data['terms'] = [data['terms']]
            for termitem in data['terms']:
                if not isinstance(termitem, dict):
                    raise DAError("A terms section organized as a list must be a list of dictionary items." + self.idebug(data))
                for term in termitem:
                    lower_term = term.lower()
                    self.terms[lower_term] = {'definition': TextObject(definitions + text_type(termitem[term]), names_used=self.mako_names), 're': re.compile(r"{(?i)(%s)}" % (lower_term,), re.IGNORECASE)}
        if 'auto terms' in data and 'question' in data:
            if not isinstance(data['auto terms'], (dict, list)):
                raise DAError("Terms must be organized as a dictionary or a list." + self.idebug(data))
            if isinstance(data['auto terms'], dict):
                data['auto terms'] = [data['auto terms']]
            for termitem in data['auto terms']:
                if not isinstance(termitem, dict):
                    raise DAError("A terms section organized as a list must be a list of dictionary items." + self.idebug(data))
                for term in termitem:
                    lower_term = term.lower()
                    self.autoterms[lower_term] = {'definition': TextObject(definitions + text_type(termitem[term]), names_used=self.mako_names), 're': re.compile(r"{?(?i)\b(%s)\b}?" % (lower_term,), re.IGNORECASE)}
        if 'terms' in data and 'question' not in data:
            should_append = False
            if self.language not in self.interview.terms:
                self.interview.terms[self.language] = dict()
            if isinstance(data['terms'], list):
                for termitem in data['terms']:
                    if isinstance(termitem, dict):
                        for term in termitem:
                            lower_term = term.lower()
                            self.interview.terms[self.language][lower_term] = {'definition': termitem[term], 're': re.compile(r"{(?i)(%s)}" % (lower_term,), re.IGNORECASE)}
                    else:
                        raise DAError("A terms section organized as a list must be a list of dictionary items." + self.idebug(data))
            elif isinstance(data['terms'], dict):
                for term in data['terms']:
                    lower_term = term.lower()
                    self.interview.terms[self.language][lower_term] = {'definition': data['terms'][term], 're': re.compile(r"{(?i)(%s)}" % (lower_term,), re.IGNORECASE)}
            else:
                raise DAError("A terms section must be organized as a dictionary or a list." + self.idebug(data))
        if 'auto terms' in data and 'question' not in data:
            should_append = False
            if self.language not in self.interview.autoterms:
                self.interview.autoterms[self.language] = dict()
            if isinstance(data['auto terms'], list):
                for termitem in data['auto terms']:
                    if isinstance(termitem, dict):
                        for term in termitem:
                            lower_term = term.lower()
                            self.interview.autoterms[self.language][lower_term] = {'definition': termitem[term], 're': re.compile(r"{?(?i)\b(%s)\b}?" % (lower_term,), re.IGNORECASE)}
                    else:
                        raise DAError("An auto terms section organized as a list must be a list of dictionary items." + self.idebug(data))
            elif isinstance(data['auto terms'], dict):
                for term in data['auto terms']:
                    lower_term = term.lower()
                    self.interview.autoterms[self.language][lower_term] = {'definition': data['auto terms'][term], 're': re.compile(r"{?(?i)\b(%s)\b}?" % (lower_term,), re.IGNORECASE)}
            else:
                raise DAError("An auto terms section must be organized as a dictionary or a list." + self.idebug(data))
        if 'default role' in data:
            if 'code' not in data:
                should_append = False
            if isinstance(data['default role'], string_types):
                self.interview.default_role = [data['default role']]
            elif isinstance(data['default role'], list):
                self.interview.default_role = data['default role']
            else:
                raise DAError("A default role must be a list or a string." + self.idebug(data))
        if 'role' in data:
            if isinstance(data['role'], string_types):
                if data['role'] not in self.role:
                    self.role.append(data['role'])
            elif isinstance(data['role'], list):
                for rolename in data['role']:
                    if data['role'] not in self.role:
                        self.role.append(rolename)
            else:
                raise DAError("The role of a question must be a string or a list." + self.idebug(data))
        else:
            self.role = list()
        if 'include' in data:
            should_append = False
            if isinstance(data['include'], string_types):
                data['include'] = [data['include']]
            if isinstance(data['include'], list):
                for questionPath in data['include']:
                    self.interview.read_from(interview_source_from_string(questionPath, context_interview=self.interview))
            else:
                raise DAError("An include section must be organized as a list." + self.idebug(data))
        if 'if' in data:
            if isinstance(data['if'], string_types):
                self.condition = [compile(data['if'], '<if code>', 'eval')]
                self.find_fields_in(data['if'])
            elif isinstance(data['if'], list):
                self.condition = [compile(x, '<if code>', 'eval') for x in data['if']]
                for x in data['if']:
                    self.find_fields_in(x)
            else:
                raise DAError("An if statement must either be text or a list." + self.idebug(data))
        if 'validation code' in data:
            if not isinstance(data['validation code'], string_types):
                raise DAError("A validation code statement must be text." + self.idebug(data))
            self.validation_code = compile(data['validation code'], '<code block>', 'exec')
            self.find_fields_in(data['validation code'])
        if 'require' in data:
            if isinstance(data['require'], list):
                self.question_type = 'require'
                try:
                    self.require_list = list(map((lambda x: compile(x, '<require code>', 'eval')), data['require']))
                    for x in data['require']:
                        self.find_fields_in(x)
                except:
                    logmessage("Compile error in require:\n" + str(data['require']) + "\n" + str(sys.exc_info()[0]))
                    raise
                if 'orelse' in data:
                    if isinstance(data['orelse'], dict):
                        self.or_else_question = Question(data['orelse'], self.interview, register_target=register_target, source=self.from_source, package=self.package)
                    else:
                        raise DAError("The orelse part of a require section must be organized as a dictionary." + self.idebug(data))
                else:
                    raise DAError("A require section must have an orelse part." + self.idebug(data))
            else:
                raise DAError("A require section must be organized as a list." + self.idebug(data))
        if 'attachment' in data:
            self.attachments = self.process_attachment_list(data['attachment'])
        elif 'attachments' in data:
            self.attachments = self.process_attachment_list(data['attachments'])
        elif 'attachment code' in data:
            self.process_attachment_code(data['attachment code'])
        elif 'attachments code' in data:
            self.process_attachment_code(data['attachments code'])
        if 'allow emailing' in data:
            self.allow_emailing = data['allow emailing']
        if 'allow downloading' in data:
            self.allow_downloading = data['allow downloading']
        # if 'role' in data:
        #     if isinstance(data['role'], list):
        #         for rolename in data['role']:
        #             if rolename not in self.role:
        #                 self.role.append(rolename)
        #     elif isinstance(data['role'], string_types) and data['role'] not in self.role:
        #         self.role.append(data['role'])
        #     else:
        #         raise DAError("A role section must be text or a list." + self.idebug(data))
        if 'progress' in data:
            try:
                self.progress = int(data['progress'])
                self.interview.progress_points.add(self.progress)
            except:
                logmessage("Invalid progress number " + repr(data['progress']))
        if 'zip filename' in data:
            self.zip_filename = TextObject(definitions + text_type(data['zip filename']), names_used=self.mako_names)
        if 'action' in data:
            self.question_type = 'backgroundresponseaction'
            self.content = TextObject('action')
            self.action = data['action']
        if 'backgroundresponse' in data:
            self.question_type = 'backgroundresponse'
            self.content = TextObject('backgroundresponse')
            self.backgroundresponse = data['backgroundresponse']
        if 'response' in data:
            self.content = TextObject(definitions + text_type(data['response']), names_used=self.mako_names)
            self.question_type = 'response'
        elif 'binaryresponse' in data:
            self.question_type = 'response'
            self.content = TextObject('binary')
            self.binaryresponse = data['binaryresponse']
            if 'response' not in data:
                self.content = TextObject('')
        elif 'all_variables' in data:
            self.question_type = 'response'
            self.all_variables = True
            if 'include_internal' in data:
                self.include_internal = data['include_internal']
            self.content = TextObject('all_variables')
        elif 'response filename' in data:
            self.question_type = 'sendfile'
            if data['response filename'].__class__.__name__ == 'DAFile':
                self.response_file = data['response filename']
                if hasattr(data['response filename'], 'mimetype') and data['response filename'].mimetype:
                    self.content_type = TextObject(data['response filename'].mimetype)
            else:
                info = docassemble.base.functions.server.file_finder(data['response filename'], question=self)
                if 'fullpath' in info and info['fullpath']:
                    self.response_file = FileOnServer(data['response filename'], self) #info['fullpath']
                else:
                    self.response_file = None
                if 'mimetype' in info and info['mimetype']:
                    self.content_type = TextObject(info['mimetype'])
                else:
                    self.content_type = TextObject('text/plain; charset=utf-8')
            self.content = TextObject('')
            if 'content type' in data:
                self.content_type = TextObject(definitions + text_type(data['content type']), names_used=self.mako_names)
            elif not (hasattr(self, 'content_type') and self.content_type):
                if self.response_file is not None:
                    self.content_type = TextObject(get_mimetype(self.response_file.path()))
                else:
                    self.content_type = TextObject('text/plain; charset=utf-8')
        elif 'redirect url' in data:
            self.question_type = 'redirect'
            self.content = TextObject(definitions + text_type(data['redirect url']), names_used=self.mako_names)
        elif 'null response' in data:
            self.content = TextObject('null')
            self.question_type = 'response'
        if 'response' in data or 'binaryresponse' in data or 'all_variables' or 'null response' in data:
            if 'include_internal' in data:
                self.include_internal = data['include_internal']
            if 'content type' in data:
                self.content_type = TextObject(definitions + text_type(data['content type']), names_used=self.mako_names)
            else:
                self.content_type = TextObject('text/plain; charset=utf-8')
        if 'question' in data:
            self.content = TextObject(definitions + text_type(data['question']), names_used=self.mako_names)
        if 'subquestion' in data:
            self.subcontent = TextObject(definitions + text_type(data['subquestion']), names_used=self.mako_names)
        if 'reload' in data and data['reload']:
            self.reload_after = TextObject(definitions + text_type(data['reload']), names_used=self.mako_names)
        if 'help' in data:
            if isinstance(data['help'], dict):
                for key, value in data['help'].items():
                    if key == 'label':
                        self.helplabel = TextObject(definitions + text_type(value), names_used=self.mako_names)
                    if key == 'audio':
                        if not isinstance(value, list):
                            the_list = [value]
                        else:
                            the_list = value
                        for list_item in the_list:
                            if isinstance(list_item, (dict, list, set)):
                                raise DAError("An audio declaration in a help block can only contain a text item or a list of text items." + self.idebug(data))
                            if self.audiovideo is None:
                                self.audiovideo = dict()
                            if 'help' not in self.audiovideo:
                                self.audiovideo['help'] = list()
                            self.audiovideo['help'].append({'text': TextObject(definitions + text_type(list_item.strip()), names_used=self.mako_names), 'package': self.package, 'type': 'audio'})
                    if key == 'video':
                        if not isinstance(value, list):
                            the_list = [value]
                        else:
                            the_list = value
                        for list_item in the_list:
                            if isinstance(list_item, (dict, list, set)):
                                raise DAError("A video declaration in a help block can only contain a text item or a list of text items." + self.idebug(data))
                            if self.audiovideo is None:
                                self.audiovideo = dict()
                            if 'help' not in self.audiovideo:
                                self.audiovideo['help'] = list()
                            self.audiovideo['help'].append({'text': TextObject(definitions + text_type(list_item.strip()), names_used=self.mako_names), 'package': self.package, 'type': 'video'})
                    if key == 'content':
                        if isinstance(value, (dict, list, set)):
                            raise DAError("A content declaration in a help block can only contain text." + self.idebug(data))
                        self.helptext = TextObject(definitions + text_type(value), names_used=self.mako_names)
            else:
                self.helptext = TextObject(definitions + text_type(data['help']), names_used=self.mako_names)
        if 'audio' in data:
            if not isinstance(data['audio'], list):
                the_list = [data['audio']]
            else:
                the_list = data['audio']
            for list_item in the_list:
                if isinstance(list_item, (dict, list, set)):
                    raise DAError("An audio declaration can only contain a text item or a list of text items." + self.idebug(data))
                if self.audiovideo is None:
                    self.audiovideo = dict()    
                if 'question' not in self.audiovideo:
                    self.audiovideo['question'] = list()
                self.audiovideo['question'].append({'text': TextObject(definitions + text_type(list_item.strip()), names_used=self.mako_names), 'package': self.package, 'type': 'audio'})
        if 'video' in data:
            if not isinstance(data['video'], list):
                the_list = [data['video']]
            else:
                the_list = data['video']
            for list_item in the_list:
                if isinstance(list_item, (dict, list, set)):
                    raise DAError("A video declaration can only contain a text item or a list of text items." + self.idebug(data))
                if self.audiovideo is None:
                    self.audiovideo = dict()    
                if 'question' not in self.audiovideo:
                    self.audiovideo['question'] = list()
                self.audiovideo['question'].append({'text': TextObject(definitions + text_type(list_item.strip()), names_used=self.mako_names), 'package': self.package, 'type': 'video'})
        if 'decoration' in data:
            if isinstance(data['decoration'], dict):
                decoration_list = [data['decoration']]
            elif isinstance(data['decoration'], list):
                decoration_list = data['decoration']
            else:
                decoration_list = [{'image': str(data['decoration'])}]
            processed_decoration_list = []
            for item in decoration_list:
                if isinstance(item, dict):
                    the_item = item
                else:
                    the_item = {'image': str(item.rstrip())}
                item_to_add = dict()
                for key, value in the_item.items():
                    item_to_add[key] = TextObject(value, names_used=self.mako_names)
                processed_decoration_list.append(item_to_add)
            self.decorations = processed_decoration_list
        if 'signature' in data:
            self.question_type = 'signature'
            self.fields.append(Field({'saveas': data['signature']}))
            if self.scan_for_variables:
                self.fields_used.add(data['signature'])
        if 'under' in data:
            self.undertext = TextObject(definitions + text_type(data['under']), names_used=self.mako_names)
        if 'right' in data:
            self.righttext = TextObject(definitions + text_type(data['right']), names_used=self.mako_names)
        if 'check in' in data:
            self.interview.uses_action = True
            if isinstance(data['check in'], (dict, list, set)):
                raise DAError("A check in event must be text or a list." + self.idebug(data))
            self.checkin = str(data['check in'])
            self.names_used.add(str(data['check in']))
        if 'yesno' in data:
            self.fields.append(Field({'saveas': data['yesno'], 'boolean': 1}))
            if self.scan_for_variables:
                self.fields_used.add(data['yesno'])
            self.question_type = 'yesno'
        if 'noyes' in data:
            self.fields.append(Field({'saveas': data['noyes'], 'boolean': -1}))
            if self.scan_for_variables:
                self.fields_used.add(data['noyes'])
            self.question_type = 'noyes'
        if 'yesnomaybe' in data:
            self.fields.append(Field({'saveas': data['yesnomaybe'], 'threestate': 1}))
            if self.scan_for_variables:
                self.fields_used.add(data['yesnomaybe'])
            self.question_type = 'yesnomaybe'
        if 'noyesmaybe' in data:
            self.fields.append(Field({'saveas': data['noyesmaybe'], 'threestate': -1}))
            if self.scan_for_variables:
                self.fields_used.add(data['noyesmaybe'])
            self.question_type = 'noyesmaybe'
        if 'sets' in data:
            if isinstance(data['sets'], string_types):
                self.fields_used.add(data['sets'])
            elif isinstance(data['sets'], list):
                for key in data['sets']:
                    self.fields_used.add(key)
            else:
                raise DAError("A sets phrase must be text or a list." + self.idebug(data))
        if 'event' in data:
            self.interview.uses_action = True
            if isinstance(data['event'], string_types):
                self.fields_used.add(data['event'])
            elif isinstance(data['event'], list):
                for key in data['event']:
                    self.fields_used.add(key)
            else:
                raise DAError("An event phrase must be text or a list." + self.idebug(data))
        if 'choices' in data or 'buttons' in data or 'dropdown' in data or 'combobox' in data:
            if 'field' in data:
                uses_field = True
                data['field'] = data['field'].strip()
            else:
                uses_field = False
            if 'shuffle' in data and data['shuffle']:
                shuffle = True
            else:
                shuffle = False
            if 'choices' in data or 'dropdown' in data or 'combobox' in data:
                if 'choices' in data:
                    has_code, choices = self.parse_fields(data['choices'], register_target, uses_field)
                    self.question_variety = 'radio'
                elif 'combobox' in data:
                    has_code, choices = self.parse_fields(data['combobox'], register_target, uses_field)
                    self.question_variety = 'combobox'
                else:
                    has_code, choices = self.parse_fields(data['dropdown'], register_target, uses_field)
                    self.question_variety = 'dropdown'
                field_data = {'choices': choices, 'shuffle': shuffle}
                if has_code:
                    field_data['has_code'] = True
                if 'default' in data:
                    field_data['default'] = TextObject(definitions + text_type(data['default']), names_used=self.mako_names)
            elif 'buttons' in data:
                has_code, choices = self.parse_fields(data['buttons'], register_target, uses_field)
                field_data = {'choices': choices, 'shuffle': shuffle}
                if has_code:
                    field_data['has_code'] = True
                self.question_variety = 'buttons'
            if 'validation messages' in data:
                if not isinstance(data['validation messages'], dict):
                    raise DAError("A validation messages indicator must be a dictionary." + self.idebug(data))
                field_data['validation messages'] = dict()
                for validation_key, validation_message in data['validation messages'].items():
                    if not (isinstance(validation_key, string_types) and isinstance(validation_message, string_types)):
                        raise DAError("A validation messages indicator must be a dictionary of text keys and text values." + self.idebug(data))
                    field_data['validation messages'][validation_key] = TextObject(definitions + text_type(validation_message).strip(), names_used=self.mako_names)
            if uses_field:
                data['field'] = data['field'].strip()
                if invalid_variable_name(data['field']):
                    raise DAError("Missing or invalid variable name " + repr(data['field']) + "." + self.idebug(data))
                if self.scan_for_variables:
                    self.fields_used.add(data['field'])
                field_data['saveas'] = data['field']
                if 'datatype' in data and 'type' not in field_data:
                    field_data['type'] = data['datatype']
                elif is_boolean(field_data):
                    field_data['type'] = 'boolean'
                elif is_threestate(field_data):
                    field_data['type'] = 'threestate'
            self.fields.append(Field(field_data))
            self.question_type = 'multiple_choice'
        elif 'field' in data:
            if not isinstance(data['field'], string_types):
                raise DAError("A field must be plain text." + self.idebug(data))
            if self.scan_for_variables:
                self.fields_used.add(data['field'])
            if 'review' in data:
                self.review_saveas = data['field']
            else:
                field_data = {'saveas': data['field']}
                self.fields.append(Field(field_data))
                self.question_type = 'settrue'
        if 'need' in data:
            if isinstance(data['need'], string_types):
                need_list = [data['need']]
            elif isinstance(data['need'], list):
                need_list = data['need']
            else:
                raise DAError("A need phrase must be text or a list." + self.idebug(data))
            try:
                self.need = list(map((lambda x: compile(x, '<need expression>', 'exec')), need_list))
                for x in need_list:
                    self.find_fields_in(x)
            except:
                logmessage("Question: compile error in need code:\n" + str(data['need']) + "\n" + str(sys.exc_info()[0]))
                raise
        if 'target' in data:
            self.interview.uses_action = True
            if isinstance(data['target'], (list, dict, set, bool, int, float)):
                raise DAError("The target of a template must be plain text." + self.idebug(data))
            if 'template' not in data:
                raise DAError("A target directive can only be used with a template." + self.idebug(data))
            self.target = data['target']
        if 'table' in data or 'rows' in data or 'columns' in data:
            if 'table' not in data or 'rows' not in data or 'columns' not in data:
                raise DAError("A table definition must have definitions for table, row, and column." + self.idebug(data))
            if isinstance(data['rows'], (list, dict, set, bool, int, float)):
                raise DAError("The row part of a table definition must be plain Python code." + self.idebug(data))
            data['rows'] = data['rows'].strip()
            if not isinstance(data['columns'], list):
                raise DAError("The column part of a table definition must be a list." + self.idebug(data))
            row = compile(data['rows'], '<row code>', 'eval')
            self.find_fields_in(data['rows'])
            header = list()
            column = list()
            read_only = dict(edit=True, delete=True)
            is_editable = False
            is_reorderable = False
            for col in data['columns']:
                if not isinstance(col, dict):
                    raise DAError("The column items in a table definition must be dictionaries." + self.idebug(data))
                if len(col) == 0:
                    raise DAError("A column item in a table definition cannot be empty." + self.idebug(data))
                if 'header' in col and 'cell' in col:
                    header_text = col['header']
                    cell_text = text_type(col['cell']).strip()
                else:
                    for key, val in col.items():
                        header_text = key
                        cell_text = text_type(val).strip()
                        break
                if header_text == '':
                    header.append(TextObject('&nbsp;'))
                else:
                    header.append(TextObject(definitions + text_type(header_text), names_used=self.mako_names))
                self.find_fields_in(cell_text)
                column.append(compile(cell_text, '<column code>', 'eval'))
            if 'allow reordering' in data and data['allow reordering'] is not False:
                reorder = True
            else:
                reorder = False
            if 'edit' in data and data['edit'] is not False:
                is_editable = True
                if not isinstance(data['edit'], list) or len(data['edit']) == 0:
                    raise DAError("The edit directive must be a list of attributes, or False" + self.idebug(data))
                for attribute_name in data['edit']:
                    if not isinstance(attribute_name, string_types):
                        raise DAError("The edit directive must be a list of attribute names" + self.idebug(data))
                keyword_args = ''
                if 'delete buttons' in data and not data['delete buttons']:
                    keyword_args += ', delete=False'
                if 'read only' in data:
                    if not isinstance(data['read only'], string_types):
                        raise DAError("The read only directive must be plain text referring to an attribute" + self.idebug(data))
                    keyword_args += ', read_only_attribute=' + repr(data['read only'].strip())
                column.append(compile('(' + data['rows'] + ').item_actions(row_item, row_index, ' + ', '.join([repr(y) for y in data['edit']]) + keyword_args + ', reorder=' + repr(reorder) + ')', '<edit code>', 'eval'))
                if 'edit header' in data:
                    if not isinstance(data['edit header'], string_types):
                        raise DAError("The edit header directive must be text" + self.idebug(data))
                    if data['edit header'] == '':
                        header.append(TextObject('&nbsp;'))
                    else:
                        header.append(TextObject(definitions + text_type(data['edit header']), names_used=self.mako_names))
                else:
                    header.append(TextObject(word("Actions")))
            elif ('delete buttons' in data and data['delete buttons']) or reorder:
                is_editable = True
                keyword_args = ''
                if 'read only' in data:
                    if not isinstance(data['read only'], string_types):
                        raise DAError("The read only directive must be plain text referring to an attribute" + self.idebug(data))
                    keyword_args += ', read_only_attribute=' + repr(data['read only'].strip())
                if 'delete buttons' in data and data['delete buttons']:
                    column.append(compile('(' + data['rows'] + ').item_actions(row_item, row_index, edit=False' + keyword_args + ', reorder=' + repr(reorder) + ')', '<delete button code>', 'eval'))
                else:
                    column.append(compile('(' + data['rows'] + ').item_actions(row_item, row_index, edit=False' + keyword_args + ', delete=False, reorder=' + repr(reorder) + ')', '<reorder buttons code>', 'eval'))
                if 'edit header' in data:
                    if not isinstance(data['edit header'], string_types):
                        raise DAError("The edit header directive must be text" + self.idebug(data))
                    if data['edit header'] == '':
                        header.append(TextObject('&nbsp;'))
                    else:
                        header.append(TextObject(definitions + text_type(data['edit header']), names_used=self.mako_names))
                else:
                    header.append(TextObject(word("Actions")))
            if self.scan_for_variables:
                self.fields_used.add(data['table'])
            empty_message = data.get('show if empty', True)
            if empty_message not in (True, False, None):
                empty_message = TextObject(definitions + text_type(empty_message), names_used=self.mako_names)
            field_data = {'saveas': data['table'], 'extras': dict(header=header, row=row, column=column, empty_message=empty_message, indent=data.get('indent', False), is_editable=is_editable, is_reorderable=is_reorderable)}
            self.fields.append(Field(field_data))
            self.content = TextObject('')
            self.subcontent = TextObject('')
            self.question_type = 'table'
        if 'template' in data and 'content file' in data:
            if not isinstance(data['content file'], list):
                data['content file'] = [data['content file']]
            data['content'] = ''
            for content_file in data['content file']:
                if not isinstance(content_file, string_types):
                    raise DAError('A content file must be specified as text or a list of text filenames' + self.idebug(data))
                file_to_read = docassemble.base.functions.package_template_filename(content_file, package=self.package)
                #if file_to_read is not None and get_mimetype(file_to_read) != 'text/markdown':
                #    raise DAError('The content file ' + str(data['content file']) + ' is not a markdown file ' + str(file_to_read) + self.idebug(data))
                if file_to_read is not None and os.path.isfile(file_to_read) and os.access(file_to_read, os.R_OK):
                    with open(file_to_read, 'rU', encoding='utf-8') as the_file:
                        data['content'] += the_file.read()
                else:
                    raise DAError('Unable to read content file ' + str(data['content file']) + ' after trying to find it at ' + str(file_to_read) + self.idebug(data))
        if 'template' in data and 'content' in data:
            if isinstance(data['template'], (list, dict)):
                raise DAError("A template must designate a single variable expressed as text." + self.idebug(data))
            if isinstance(data['content'], (list, dict)):
                raise DAError("The content of a template must be expressed as text." + self.idebug(data))
            if self.scan_for_variables:
                self.fields_used.add(data['template'])
            field_data = {'saveas': data['template']}
            self.fields.append(Field(field_data))
            self.content = TextObject(definitions + text_type(data['content']), names_used=self.mako_names)
            #logmessage("keys are: " + str(self.mako_names))
            if 'subject' in data:
                self.subcontent = TextObject(definitions + text_type(data['subject']), names_used=self.mako_names)
            else:
                self.subcontent = TextObject("")
            self.question_type = 'template'
            #if self.scan_for_variables:
            #    self.reset_list = self.fields_used
        if 'code' in data:
            if 'event' in data:
                self.question_type = 'event_code'
            else:
                self.question_type = 'code'
            if isinstance(data['code'], string_types):
                if not self.interview.calls_process_action and match_process_action.search(data['code']):
                    self.interview.calls_process_action = True
                try:
                    self.compute = compile(data['code'], '<code block>', 'exec')
                    self.sourcecode = data['code']
                except:
                    logmessage("Question: compile error in code:\n" + text_type(data['code']) + "\n" + str(sys.exc_info()[0]))
                    raise
                if self.question_type == 'code':
                    self.find_fields_in(data['code'])
            else:
                raise DAError("A code section must be text, not a list or a dictionary." + self.idebug(data))
        if 'reconsider' in data:
            #if not isinstance(data['reconsider'], bool):
            #    raise DAError("A reconsider directive must be true or false." + self.idebug(data))
            if isinstance(data['reconsider'], bool):
                if data['reconsider']:
                    if self.is_generic:
                        if self.generic_object not in self.interview.reconsider_generic:
                            self.interview.reconsider_generic[self.generic_object] = set()
                        self.interview.reconsider_generic[self.generic_object].update(self.fields_used)
                    else:
                        self.interview.reconsider.update(self.fields_used)
            else:
                if isinstance(data['reconsider'], string_types):
                    fields = [data['reconsider']]
                elif isinstance(data['reconsider'], list):
                    fields = data['reconsider']
                else:
                    raise DAError("A reconsider directive must be true, false, a single variable or a list." + self.idebug(data))
                for the_field in fields:
                    if not isinstance(the_field, string_types):
                        raise DAError("A reconsider directive must refer to variable names expressed as text." + self.idebug(data))
                    self.find_fields_in(the_field)
                    self.reconsider.append(the_field)
        if 'undefine' in data:
            if isinstance(data['undefine'], string_types):
                fields = [data['undefine']]
            elif isinstance(data['undefine'], list):
                fields = data['undefine']
            else:
                raise DAError("A undefine directive must a single variable or a list." + self.idebug(data))
            for the_field in fields:
                if not isinstance(the_field, string_types):
                    raise DAError("A undefine directive must refer to variable names expressed as text." + self.idebug(data))
                self.find_fields_in(the_field)
                self.undefine.append(the_field)
        if 'fields' in data:
            self.question_type = 'fields'
            if 'continue button field' in data:
                if not isinstance(data['continue button field'], string_types):
                    raise DAError("A continue button field must be plain text." + self.idebug(data))
                if self.scan_for_variables:
                    self.fields_used.add(data['continue button field'])
                self.fields_saveas = data['continue button field']
            if isinstance(data['fields'], dict):
                data['fields'] = [data['fields']]
            if not isinstance(data['fields'], list):
                raise DAError("The fields must be written in the form of a list." + self.idebug(data))
            else:
                field_number = 0
                for field in data['fields']:
                    docassemble.base.functions.this_thread.misc['current_field'] = field_number
                    if isinstance(field, dict):
                        manual_keys = set()
                        field_info = {'type': 'text', 'number': field_number}
                        if 'datatype' in field and field['datatype'] in ('radio', 'combobox', 'pulldown'):
                            field['input type'] = field['datatype']
                            field['datatype'] = 'text'
                        if len(field) == 1 and 'code' in field:
                            field_info['type'] = 'fields_code'
                            self.find_fields_in(field['code'])
                            field_info['extras'] = dict(fields_code=compile(field['code'], '<fields code>', 'eval'))
                            self.fields.append(Field(field_info))
                            continue
                        if 'datatype' in field and field['datatype'] in ('radio', 'object', 'object_radio', 'combobox', 'checkboxes', 'object_checkboxes') and not ('choices' in field or 'code' in field):
                            raise DAError("A multiple choice field must refer to a list of choices." + self.idebug(data))
                        if 'object labeler' in field and ('datatype' not in field or not field['datatype'].startswith('object')):
                            raise DAError("An object labeler can only be used with an object data type")
                        if 'note' in field and 'html' in field:
                            raise DAError("You cannot include both note and html in a field." + self.idebug(data))
                        for key in field:
                            if key == 'default' and 'datatype' in field and field['datatype'] in ('object', 'object_radio', 'object_checkboxes'):
                                continue
                            if key == 'input type':
                                field_info['inputtype'] = field[key]
                            elif 'datatype' in field and field['datatype'] in ('ml', 'mlarea') and key in ('using', 'keep for training'):
                                if key == 'using':
                                    if 'extras' not in field_info:
                                        field_info['extras'] = dict()
                                    field_info['extras']['ml_group'] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                                if key == 'keep for training':
                                    if 'extras' not in field_info:
                                        field_info['extras'] = dict()
                                    if isinstance(field[key], bool):
                                        field_info['extras']['ml_train'] = field[key]
                                    else:
                                        field_info['extras']['ml_train'] = {'compute': compile(field[key], '<keep for training code>', 'eval'), 'sourcecode': field[key]}
                                        self.find_fields_in(field[key])
                            elif key == 'validation messages':
                                if not isinstance(field[key], dict):
                                    raise DAError("A validation messages indicator must be a dictionary." + self.idebug(data))
                                field_info['validation messages'] = dict()
                                for validation_key, validation_message in field[key].items():
                                    if not (isinstance(validation_key, string_types) and isinstance(validation_message, string_types)):
                                        raise DAError("A validation messages indicator must be a dictionary of text keys and text values." + self.idebug(data))
                                    field_info['validation messages'][validation_key] = TextObject(definitions + text_type(validation_message).strip(), names_used=self.mako_names)
                            elif key == 'validate':
                                field_info['validate'] = {'compute': compile(field[key], '<validate code>', 'eval'), 'sourcecode': field[key]}
                                self.find_fields_in(field[key])
                            elif 'datatype' in field and field['datatype'] == 'area' and key == 'rows':
                                field_info['rows'] = {'compute': compile(text_type(field[key]), '<rows code>', 'eval'), 'sourcecode': text_type(field[key])}
                                self.find_fields_in(field[key])
                            elif 'datatype' in field and field['datatype'] in ('file', 'files', 'camera', 'user', 'environment') and key == 'maximum image size':
                                field_info['max_image_size'] = {'compute': compile(text_type(field[key]), '<maximum image size code>', 'eval'), 'sourcecode': text_type(field[key])}
                                self.find_fields_in(field[key])
                            elif 'datatype' in field and field['datatype'] in ('file', 'files', 'camera', 'user', 'environment') and key == 'accept':
                                field_info['accept'] = {'compute': compile(field[key], '<accept code>', 'eval'), 'sourcecode': field[key]}
                                self.find_fields_in(field[key])
                            elif key == 'object labeler':
                                field_info['object_labeler'] = {'compute': compile(text_type(field[key]), '<object labeler code>', 'eval'), 'sourcecode': text_type(field[key])}
                                self.find_fields_in(field[key])
                            elif key == 'required':
                                if isinstance(field[key], bool):
                                    field_info['required'] = field[key]
                                else:
                                    field_info['required'] = {'compute': compile(field[key], '<required code>', 'eval'), 'sourcecode': field[key]}
                                    self.find_fields_in(field[key])
                            elif key == 'js show if' or key == 'js hide if':
                                if not isinstance(field[key], string_types):
                                    raise DAError("A js show if or js hide if expression must be a string" + self.idebug(data))
                                js_info = dict()
                                if key == 'js show if':
                                    js_info['sign'] = True
                                else:
                                    js_info['sign'] = False
                                js_info['expression'] = field[key]
                                js_info['vars'] = list(set(re.findall(r'val\(\'([^\)]+)\'\)', field[key]) + re.findall(r'val\("([^\)]+)"\)', field[key])))
                                if 'extras' not in field_info:
                                    field_info['extras'] = dict()
                                field_info['extras']['show_if_js'] = js_info
                            elif key == 'show if' or key == 'hide if':
                                if 'js show if' in field or 'js hide if' in field:
                                    raise DAError("You cannot mix js show if and non-js show if" + self.idebug(data))
                                if 'extras' not in field_info:
                                    field_info['extras'] = dict()
                                if isinstance(field[key], dict):
                                    if 'variable' in field[key] and 'is' in field[key]:
                                        field_info['extras']['show_if_var'] = safeid(field[key]['variable'].strip())
                                        field_info['extras']['show_if_val'] = TextObject(definitions + text_type(field[key]['is']).strip(), names_used=self.mako_names)
                                    elif 'code' in field[key]:
                                        field_info['showif_code'] = compile(field[key]['code'], '<show if code>', 'eval')
                                        self.find_fields_in(field[key]['code'])
                                    else:
                                        raise DAError("The keys of '" + key + "' must be 'variable' and 'is.'" + self.idebug(data))
                                elif isinstance(field[key], list):
                                    raise DAError("The keys of '" + key + "' cannot be a list" + self.idebug(data))
                                elif isinstance(field[key], string_types):
                                    field_info['extras']['show_if_var'] = safeid(field[key].strip())
                                    field_info['extras']['show_if_val'] = TextObject('True')
                                else:
                                    raise DAError("Invalid variable name in show if/hide if")
                                if key == 'show if':
                                    field_info['extras']['show_if_sign'] = 1
                                else:
                                    field_info['extras']['show_if_sign'] = 0
                            elif key == 'default' or key == 'hint' or key == 'help':
                                if not isinstance(field[key], dict) and not isinstance(field[key], list):
                                    field_info[key] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                                if key == 'default':
                                    if isinstance(field[key], dict) and 'code' in field[key]:
                                        if 'extras' not in field_info:
                                            field_info['extras'] = dict()
                                        field_info['extras']['default'] = {'compute': compile(field[key]['code'], '<default code>', 'eval'), 'sourcecode': field[key]['code']}
                                        self.find_fields_in(field[key]['code'])
                                    else:
                                        if isinstance(field[key], (dict, list)):
                                            field_info[key] = field[key]
                                        if 'datatype' not in field and 'code' not in field and 'choices' not in field:
                                            auto_determine_type(field_info, the_value=field[key])
                            elif key == 'disable others':
                                if 'datatype' in field and field['datatype'] in ('file', 'files', 'range', 'checkboxes', 'camera', 'user', 'environment', 'camcorder', 'microphone', 'object_checkboxes'): #'yesno', 'yesnowide', 'noyes', 'noyeswide', 
                                    raise DAError("A 'disable others' directive cannot be used with this data type." + self.idebug(data))
                                if not isinstance(field[key], (list, bool)):
                                    raise DAError("A 'disable others' directive must be True, False, or a list of variable names." + self.idebug(data))
                                field_info['disable others'] = field[key]
                                if field[key] is not False:
                                    field_info['required'] = False
                            elif key == 'uncheck others' and 'datatype' in field and field['datatype'] in ('yesno', 'yesnowide', 'noyes', 'noyeswide'):
                                if not isinstance(field[key], (list, bool)):
                                    raise DAError("An 'uncheck others' directive must be True, False, or a list of variable names." + self.idebug(data))
                                field_info['uncheck others'] = field[key]
                            elif key == 'datatype':
                                field_info['type'] = field[key]
                                if field[key] in ('yesno', 'yesnowide', 'noyes', 'noyeswide') and 'required' not in field_info:
                                    field_info['required'] = False
                                if field[key] == 'range' and 'required' not in field_info:
                                    field_info['required'] = False
                                if field[key] == 'range' and not ('min' in field and 'max' in field):
                                    raise DAError("If the datatype of a field is 'range', you must provide a min and a max." + self.idebug(data))
                                if field[key] in ('yesno', 'yesnowide', 'yesnoradio'):
                                    field_info['boolean'] = 1
                                elif field[key] in ('noyes', 'noyeswide', 'noyesradio'):
                                    field_info['boolean'] = -1
                                elif field[key] == 'yesnomaybe':
                                    field_info['threestate'] = 1
                                elif field[key] == 'noyesmaybe':
                                    field_info['threestate'] = -1
                            elif key == 'code':
                                self.find_fields_in(field[key])
                                field_info['choicetype'] = 'compute'
                                field_info['selections'] = {'compute': compile(field[key], '<choices code>', 'eval'), 'sourcecode': field[key]}
                                self.find_fields_in(field[key])
                                if 'exclude' in field:
                                    if isinstance(field['exclude'], dict):
                                        raise DAError("An exclude entry cannot be a dictionary." + self.idebug(data))
                                    if not isinstance(field['exclude'], list):
                                        field_info['selections']['exclude'] = [compile(field['exclude'], '<expression>', 'eval')]
                                        self.find_fields_in(field['exclude'])
                                    else:
                                        field_info['selections']['exclude'] = list()
                                        for x in field['exclude']:
                                            field_info['selections']['exclude'].append(compile(x, '<expression>', 'eval'))
                                            self.find_fields_in(x)
                            elif key == 'address autocomplete':
                                field_info['address_autocomplete'] = True
                            elif key == 'exclude':
                                pass
                            elif key == 'choices':
                                if 'datatype' in field and field['datatype'] in ('object', 'object_radio', 'object_checkboxes'):
                                    field_info['choicetype'] = 'compute'
                                    if not isinstance(field[key], (list, str)):
                                        raise DAError("choices is not in appropriate format" + self.idebug(data))
                                    field_info['selections'] = dict()
                                else:
                                    field_info['choicetype'] = 'manual'
                                    field_info['selections'] = dict(values=process_selections_manual(field[key]))
                                    if 'datatype' not in field:
                                        auto_determine_type(field_info)
                                    for item in field_info['selections']['values']:
                                        if not item['key'].uses_mako:
                                            manual_keys.add(item['key'].original_text)
                                if 'exclude' in field:
                                    if isinstance(field['exclude'], dict):
                                        raise DAError("An exclude entry cannot be a dictionary." + self.idebug(data))
                                    if not isinstance(field['exclude'], list):
                                        self.find_fields_in(field['exclude'])
                                        field_info['selections']['exclude'] = [compile(field['exclude'].strip(), '<expression>', 'eval')]
                                    else:
                                        field_info['selections']['exclude'] = list()
                                        for x in field['exclude']:
                                            self.find_fields_in(x)
                                            field_info['selections']['exclude'].append(compile(x, '<expression>', 'eval'))
                            elif key in ('note', 'html'):
                                if 'extras' not in field_info:
                                    field_info['extras'] = dict()
                                field_info['extras'][key] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                            elif key in ('min', 'max', 'minlength', 'maxlength', 'step', 'scale', 'inline width'):
                                if 'extras' not in field_info:
                                    field_info['extras'] = dict()
                                field_info['extras'][key] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                            # elif key in ('css', 'script'):
                            #     if 'extras' not in field_info:
                            #         field_info['extras'] = dict()
                            #     if field_info['type'] == 'text':
                            #         field_info['type'] = key
                            #     field_info['extras'][key] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                            elif key == 'shuffle':
                                field_info['shuffle'] = field[key]
                            elif key == 'none of the above' and 'datatype' in field and field['datatype'] in ('checkboxes', 'object_checkboxes', 'object_radio'):
                                if isinstance(field[key], bool):
                                    field_info['nota'] = field[key]
                                else:
                                    field_info['nota'] = TextObject(definitions + interpret_label(field[key]), names_used=self.mako_names)
                            elif key == 'field':
                                if 'label' not in field:
                                    raise DAError("If you use 'field' to indicate a variable in a 'fields' section, you must also include a 'label.'" + self.idebug(data))
                                if not isinstance(field[key], string_types):
                                    raise DAError("Fields in a 'field' section must be plain text." + self.idebug(data))
                                field[key] = field[key].strip()
                                if invalid_variable_name(field[key]):
                                    raise DAError("Missing or invalid variable name " + repr(field[key]) + "." + self.idebug(data))
                                field_info['saveas'] = field[key]                                
                            elif key == 'label':
                                if 'field' not in field:
                                    raise DAError("If you use 'label' to label a field in a 'fields' section, you must also include a 'field.'" + self.idebug(data))                                    
                                field_info['label'] = TextObject(definitions + interpret_label(field[key]), names_used=self.mako_names)
                            else:
                                if 'label' in field_info:
                                    raise DAError("Syntax error: field label '" + str(key) + "' overwrites previous label, '" + str(field_info['label'].original_text) + "'" + self.idebug(data))
                                field_info['label'] = TextObject(definitions + interpret_label(key), names_used=self.mako_names)
                                if not isinstance(field[key], string_types):
                                    raise DAError("Fields in a 'field' section must be plain text." + self.idebug(data))
                                field[key] = field[key].strip()
                                if invalid_variable_name(field[key]):
                                    raise DAError("Missing or invalid variable name " + repr(field[key]) + " for key " + repr(key) + "." + self.idebug(data))
                                field_info['saveas'] = field[key]
                        if 'type' in field_info:
                            if field_info['type'] in ('checkboxes', 'object_checkboxes') and 'nota' not in field_info:
                                field_info['nota'] = True
                            if field_info['type'] == 'object_radio' and 'nota' not in field_info:
                                field_info['nota'] = False
                        if 'choicetype' in field_info and field_info['choicetype'] == 'compute' and 'type' in field_info and field_info['type'] in ('object', 'object_radio', 'object_checkboxes'):
                            if 'choices' not in field:
                                raise DAError("You need to have a choices element if you want to set a variable to an object." + self.idebug(data))
                            if not isinstance(field['choices'], list):
                                select_list = [str(field['choices'])]
                            else:
                                select_list = field['choices']
                            if 'exclude' in field:
                                if isinstance(field['exclude'], dict):
                                    raise DAError("choices exclude list is not in appropriate format" + self.idebug(data))
                                if not isinstance(field['exclude'], list):
                                    exclude_list = [str(field['exclude']).strip()]
                                else:
                                    exclude_list = [x.strip() for x in field['exclude']]
                                if len(exclude_list):
                                    select_list.append('exclude=[' + ", ".join(exclude_list) + ']')
                            if 'default' in field:
                                if not isinstance(field['default'], (list, str)):
                                    raise DAError("default list is not in appropriate format" + self.idebug(data))
                                if not isinstance(field['default'], list):
                                    default_list = [str(field['default'])]
                                else:
                                    default_list = field['default']
                            else:
                                default_list = list()
                            if field_info['type'] == 'object_checkboxes':
                                default_list.append('_DAOBJECTDEFAULTDA')
                            if len(default_list):
                                select_list.append('default=[' + ", ".join(default_list) + ']')
                            if 'object_labeler' in field_info:
                                source_code = "docassemble.base.core.selections(" + ", ".join(select_list) + ", object_labeler=_DAOBJECTLABELER)"
                            else:
                                source_code = "docassemble.base.core.selections(" + ", ".join(select_list) + ")"
                            #logmessage("source_code is " + source_code)
                            field_info['selections'] = {'compute': compile(source_code, '<expression>', 'eval'), 'sourcecode': source_code}
                        if 'saveas' in field_info:
                            if not isinstance(field_info['saveas'], string_types):
                                raise DAError("Invalid variable name " + repr(field_info['saveas']) + "." + self.idebug(data))
                            self.fields.append(Field(field_info))
                            if 'type' in field_info:
                                if field_info['type'] in ('checkboxes', 'object_checkboxes'):
                                    if self.scan_for_variables:
                                        self.fields_used.add(field_info['saveas'])
                                        self.fields_used.add(field_info['saveas'] + '.gathered')
                                        if field_info['type'] == 'checkboxes':
                                            for the_key in manual_keys:
                                                self.fields_used.add(field_info['saveas'] + '[' + repr(the_key) + ']')
                                elif field_info['type'] in ('ml', 'mlarea'):
                                    if self.scan_for_variables:
                                        self.fields_used.add(field_info['saveas'])
                                    self.interview.mlfields[field_info['saveas']] = dict(saveas=field_info['saveas'])
                                    if 'extras' in field_info and 'ml_group' in field_info['extras']:
                                        self.interview.mlfields[field_info['saveas']]['ml_group'] = field_info['extras']['ml_group']
                                    if re.search(r'\.text$', field_info['saveas']):
                                        field_info['saveas'] = field_info['saveas'].strip()
                                        if invalid_variable_name(field_info['saveas']):
                                            raise DAError("Missing or invalid variable name " + repr(field_info['saveas']) + "." + self.idebug(data))
                                        field_info['saveas'] = re.sub(r'\.text$', '', field_info['saveas'])
                                        if self.scan_for_variables:
                                            self.fields_used.add(field_info['saveas'])
                                    else:
                                        if self.scan_for_variables:
                                            self.fields_used.add(field_info['saveas'] + '.text')
                                else:
                                    if self.scan_for_variables:
                                        self.fields_used.add(field_info['saveas'])
                            else:
                                if self.scan_for_variables:
                                    self.fields_used.add(field_info['saveas'])
                        elif 'note' in field or 'html' in field:
                            if 'note' in field:
                                field_info['type'] = 'note'
                            else:
                                field_info['type'] = 'html'
                            self.fields.append(Field(field_info))
                        else:
                            raise DAError("A field was listed without indicating a label or a variable name, and the field was not a note or raw HTML." + self.idebug(data) + " and field_info was " + repr(field_info))
                    else:
                        raise DAError("Each individual field in a list of fields must be expressed as a dictionary item, e.g., ' - Fruit: user.favorite_fruit'." + self.idebug(data))
                    field_number += 1
                if 'current_field' in docassemble.base.functions.this_thread.misc:
                    del docassemble.base.functions.this_thread.misc['current_field']
        else:
            if 'continue button field' in data:
                raise DAError("A continue button field can only be used with a fields directive." + self.idebug(data))
        if 'review' in data:
            self.question_type = 'review'
            if isinstance(data['review'], dict):
                data['review'] = [data['review']]
            if not isinstance(data['review'], list):
                raise DAError("The review must be written in the form of a list." + self.idebug(data))
            field_number = 0
            for field in data['review']:
                if not isinstance(field, dict):
                    raise DAError("Each individual field in a list of fields must be expressed as a dictionary item, e.g., ' - Fruit: user.favorite_fruit'." + self.idebug(data))
                field_info = {'number': field_number, 'data': []}
                for key in field:
                    if key == 'action':
                        continue
                    elif key == 'help':
                        if not isinstance(field[key], dict) and not isinstance(field[key], list):
                            field_info[key] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                        if 'button' in field: #or 'css' in field or 'script' in field:
                            raise DAError("In a review block, you cannot mix help text with a button item." + self.idebug(data)) #, css, or script
                    elif key == 'button':
                        if not isinstance(field[key], dict) and not isinstance(field[key], list):
                            field_info['help'] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                            field_info['type'] = 'button'
                    elif key in ('note', 'html'):
                        if 'type' not in field_info:
                            field_info['type'] = key
                        if 'extras' not in field_info:
                            field_info['extras'] = dict()
                        field_info['extras'][key] = TextObject(definitions + text_type(field[key]), names_used=self.mako_names)
                    elif key == 'show if':
                        if not isinstance(field[key], list):
                            field_list = [field[key]]
                        else:
                            field_list = field[key]
                        field_data = []
                        for the_saveas in field_list:
                            #if not isinstance(the_saveas, string_types):
                            #    raise DAError("Invalid variable name in fields." + self.idebug(data))
                            the_saveas = text_type(the_saveas).strip()
                            #if invalid_variable_name(the_saveas):
                            #    raise DAError("Missing or invalid variable name " + repr(the_saveas) + " ." + self.idebug(data))
                            if the_saveas not in field_data:
                                field_data.append(the_saveas)
                            self.find_fields_in(the_saveas)
                        if len(field_list):
                            if 'saveas_code' not in field_info:
                                field_info['saveas_code'] = []
                            field_info['saveas_code'].extend([(compile(y, '<expression>', 'eval'), True) for y in field_list])
                    elif key in ('field', 'fields'):
                        if 'label' not in field:
                            raise DAError("If you use 'field' or 'fields' to indicate variables in a 'review' section, you must also include a 'label.'" + self.idebug(data))
                        if not isinstance(field[key], list):
                            field_list = [field[key]]
                        else:
                            field_list = field[key]
                        field_info['data'] = []
                        for the_saveas in field_list:
                            if isinstance(the_saveas, dict) and len(the_saveas) == 1 and ('undefine' in the_saveas or 'recompute' in the_saveas or 'set' in the_saveas or 'follow up' in the_saveas):
                                if 'set' in the_saveas:
                                    if not isinstance(the_saveas['set'], list):
                                        raise DAError("The set statement must refer to a list." + self.idebug(data))
                                    clean_list = []
                                    for the_dict in the_saveas['set']:
                                        if not isinstance(the_dict, dict):
                                            raise DAError("A set command must refer to a list of dicts." + self.idebug(data))
                                        for the_var, the_val in the_dict.items():
                                            if not isinstance(the_var, string_types):
                                                raise DAError("A set command must refer to a list of dicts with keys as variable names." + self.idebug(data))
                                            the_var_stripped = the_var.strip()
                                        if invalid_variable_name(the_var_stripped):
                                            raise DAError("Missing or invalid variable name " + repr(the_var) + " ." + self.idebug(data))
                                        self.find_fields_in(the_var_stripped)
                                        clean_list.append([the_var_stripped, the_val])
                                    field_info['data'].append(dict(action='_da_set', arguments=dict(variables=clean_list)))
                                if 'follow up' in the_saveas:
                                    if not isinstance(the_saveas['follow up'], list):
                                        raise DAError("The follow up statement must refer to a list." + self.idebug(data))
                                    for var in the_saveas['follow up']:
                                        if not isinstance(var, string_types):
                                            raise DAError("Invalid variable name in follow up " + command + "." + self.idebug(data))
                                        var_saveas = var.strip()
                                        if invalid_variable_name(var_saveas):
                                            raise DAError("Missing or invalid variable name " + repr(var_saveas) + " ." + self.idebug(data))
                                        self.find_fields_in(var_saveas)
                                        #field_info['data'].append(dict(action="_da_follow_up", arguments=dict(action=var)))
                                        field_info['data'].append(dict(action=var, arguments=dict()))
                                for command in ('undefine', 'recompute'):
                                    if command not in the_saveas:
                                        continue
                                    if not isinstance(the_saveas[command], list):
                                        raise DAError("The " + command + " statement must refer to a list." + self.idebug(data))
                                    clean_list = []
                                    for undef_var in the_saveas[command]:
                                        if not isinstance(undef_var, string_types):
                                            raise DAError("Invalid variable name " + repr(undef_var) + " in " + command + "." + self.idebug(data))
                                        undef_saveas = undef_var.strip()
                                        if invalid_variable_name(undef_saveas):
                                            raise DAError("Missing or invalid variable name " + repr(undef_saveas) + " ." + self.idebug(data))
                                        self.find_fields_in(undef_saveas)
                                        clean_list.append(undef_saveas)
                                    field_info['data'].append(dict(action='_da_undefine', arguments=dict(variables=clean_list)))
                                    if command == 'recompute':
                                        field_info['data'].append(dict(action='_da_compute', arguments=dict(variables=clean_list)))
                                continue
                            if isinstance(the_saveas, dict) and len(the_saveas) == 2 and 'action' in the_saveas and 'arguments' in the_saveas:
                                if not isinstance(the_saveas['arguments'], dict):
                                    raise DAError("An arguments directive must refer to a dictionary.  " + repr(data))
                                field_info['data'].append(dict(action=the_saveas['action'], arguments=the_saveas['arguments']))
                            if not isinstance(the_saveas, string_types):
                                raise DAError("Invalid variable name " + repr(the_saveas) + " in fields." + self.idebug(data))
                            the_saveas = the_saveas.strip()
                            if invalid_variable_name(the_saveas):
                                raise DAError("Missing or invalid variable name " + repr(the_saveas) + " ." + self.idebug(data))
                            if the_saveas not in field_info['data']:
                                field_info['data'].append(the_saveas)
                            self.find_fields_in(the_saveas)
                        if 'action' in field:
                            field_info['action'] = dict(action=field['action'], arguments=dict())
                    elif key == 'label':
                        if 'field' not in field and 'fields' not in field:
                            raise DAError("If you use 'label' to label a field in a 'review' section, you must also include a 'field' or 'fields.'" + self.idebug(data))                                    
                        field_info['label'] = TextObject(definitions + interpret_label(field[key]), names_used=self.mako_names)
                    else:
                        field_info['label'] = TextObject(definitions + interpret_label(key), names_used=self.mako_names)
                        if not isinstance(field[key], list):
                            field_list = [field[key]]
                        else:
                            field_list = field[key]
                        field_info['data'] = []
                        for the_saveas in field_list:
                            if isinstance(the_saveas, dict) and len(the_saveas) == 1 and ('undefine' in the_saveas or 'recompute' in the_saveas):
                                if 'set' in the_saveas:
                                    if not isinstance(the_saveas['set'], list):
                                        raise DAError("The set statement must refer to a list." + self.idebug(data))
                                    clean_list = []
                                    for the_dict in the_saveas['set']:
                                        if not isinstance(the_dict, dict):
                                            raise DAError("A set command must refer to a list of dicts." + self.idebug(data))
                                        for the_var, the_val in the_dict.items():
                                            if not isinstance(the_var, string_types):
                                                raise DAError("A set command must refer to a list of dicts with keys as variable names." + self.idebug(data))
                                            the_var_stripped = the_var.strip()
                                        if invalid_variable_name(the_var_stripped):
                                            raise DAError("Missing or invalid variable name " + repr(the_var) + " ." + self.idebug(data))
                                        self.find_fields_in(the_var_stripped)
                                        clean_list.append([the_var_stripped, the_val])
                                    field_info['data'].append(dict(action='_da_set', arguments=dict(variables=clean_list)))
                                for command in ('undefine', 'recompute'):
                                    if command not in the_saveas:
                                        continue
                                    if not isinstance(the_saveas[command], list):
                                        raise DAError("The " + command + " statement must refer to a list." + self.idebug(data))
                                    clean_list = []
                                    for undef_var in the_saveas[command]:
                                        if not isinstance(undef_var, string_types):
                                            raise DAError("Invalid variable name " + repr(undef_var) + " in fields " + command + "." + self.idebug(data))
                                        undef_saveas = undef_var.strip()
                                        if invalid_variable_name(undef_saveas):
                                            raise DAError("Missing or invalid variable name " + repr(undef_saveas) + " ." + self.idebug(data))
                                        self.find_fields_in(undef_saveas)
                                        clean_list.append(undef_saveas)
                                    field_info['data'].append(dict(action='_da_undefine', arguments=dict(variables=clean_list)))
                                    if command == 'recompute':
                                        field_info['data'].append(dict(action='_da_compute', arguments=dict(variables=clean_list)))
                                continue
                            if not isinstance(the_saveas, string_types):
                                raise DAError("Invalid variable name " + repr(the_saveas) + " in fields." + self.idebug(data))
                            the_saveas = the_saveas.strip()
                            if invalid_variable_name(the_saveas):
                                raise DAError("Missing or invalid variable name " + repr(the_saveas) + " ." + self.idebug(data))
                            #if the_saveas not in field_info['data']:
                            field_info['data'].append(the_saveas)
                            self.find_fields_in(the_saveas)
                        if 'action' in field:
                            field_info['action'] = dict(action=field['action'], arguments=dict())
                    if 'type' in field_info and field_info['type'] in ('note', 'html') and 'label' in field_info:
                        del field_info['type']
                if len(field_info['data']):
                    if 'saveas_code' not in field_info:
                        field_info['saveas_code'] = []
                    field_info['saveas_code'].extend([(compile(y, '<expression>', 'eval'), False) for y in field_info['data'] if isinstance(y, string_types)])
                    if 'action' not in field_info:
                        if len(field_info['data']) == 1 and isinstance(field_info['data'][0], string_types):
                            field_info['action'] = dict(action=field_info['data'][0], arguments=dict())
                        else:
                            field_info['action'] = dict(action="_da_force_ask", arguments=dict(variables=field_info['data']))
                if len(field_info['data']) or ('type' in field_info and field_info['type'] in ('note', 'html')):
                    self.fields.append(Field(field_info))
                else:
                    raise DAError("A field in a review list was listed without indicating a label or a variable name, and the field was not a note or raw HTML." + self.idebug(field_info))
                field_number += 1
        if not hasattr(self, 'question_type'):
            if len(self.attachments) and len(self.fields_used) and not hasattr(self, 'content'):
                self.question_type = 'attachments'
            elif hasattr(self, 'content'):
                self.question_type = 'deadend'
        if should_append:
            if not hasattr(self, 'question_type'):
                raise DAError("No question type could be determined for this section." + self.idebug(data))
            if main_list:
                self.interview.questions_list.append(self)
            self.number = self.interview.next_number()
            #self.number = len(self.interview.questions_list) - 1
            if hasattr(self, 'id'):
                self.name = "ID " + self.id
                # if self.name in self.interview.questions_by_name:
                #     raise DAError("Question ID " + text_type(self.id) + " results in duplicate question name")
            else:
                self.name = "Question_" + str(self.number)
        # if hasattr(self, 'id'):
        #     try:
        #         self.interview.questions_by_id[self.id].append(self)
        #     except:
        #         self.interview.questions_by_id[self.id] = [self]
        if self.name is not None:
            self.interview.questions_by_name[self.name] = self
        foundmatch = False
        for field_name in self.fields_used:
            if re.search(r'\[', field_name):
                foundmatch = True
                break
        while foundmatch:
            foundmatch = False
            vars_to_add = set()
            for field_name in self.fields_used:
                for m in re.finditer(r'^(.*?)\[\'([^\'\"]*)\'\](.*)', field_name):
                    new_var = m.group(1) + "[u'" + m.group(2) + "']" + m.group(3)
                    if new_var not in self.fields_used:
                        foundmatch = True
                        #logmessage("Adding " + new_var)
                        vars_to_add.add(new_var)
                    # new_var = m.group(1) + '["' + m.group(2) + '"]' + m.group(3)
                    # if new_var not in self.fields_used:
                    #     foundmatch = True
                    #     logmessage("Adding " + new_var)
                    #     vars_to_add.add(new_var)
                for m in re.finditer(r'^(.*?)\[\"([^\"\']*)\"\](.*)', field_name):
                    new_var = m.group(1) + "[u'" + m.group(2) + "']" + m.group(3)
                    if new_var not in self.fields_used:
                        foundmatch = True
                        #logmessage("Adding " + new_var)
                        vars_to_add.add(new_var)
                    new_var = m.group(1) + "['" + m.group(2) + "']" + m.group(3)
                    if new_var not in self.fields_used:
                        foundmatch = True
                        #logmessage("Adding " + new_var)
                        vars_to_add.add(new_var)
                for m in re.finditer(r'^(.*?)\[u\'([^\'\"]*)\'\](.*)', field_name):
                    new_var = m.group(1) + "['" + m.group(2) + "']" + m.group(3)
                    if new_var not in self.fields_used:
                        foundmatch = True
                        #logmessage("Adding " + new_var)
                        vars_to_add.add(new_var)
                    # new_var = m.group(1) + '["' + m.group(2) + '"]' + m.group(3)
                    # if new_var not in self.fields_used:
                    #     foundmatch = True
                    #     logmessage("Adding " + new_var)
                    #     vars_to_add.add(new_var)
            for new_var in vars_to_add:
                #logmessage("Really adding " + new_var)
                self.fields_used.add(new_var)
        for field_name in self.fields_used:
            if field_name not in self.interview.questions:
                self.interview.questions[field_name] = dict()
            if self.language not in self.interview.questions[field_name]:
                self.interview.questions[field_name][self.language] = list()
            self.interview.questions[field_name][self.language].append(register_target)
            if self.is_generic:
                if self.generic_object not in self.interview.generic_questions:
                    self.interview.generic_questions[self.generic_object] = dict()
                if field_name not in self.interview.generic_questions[self.generic_object]:
                    self.interview.generic_questions[self.generic_object][field_name] = dict()
                if self.language not in self.interview.generic_questions[self.generic_object][field_name]:
                    self.interview.generic_questions[self.generic_object][field_name][self.language] = list()
                self.interview.generic_questions[self.generic_object][field_name][self.language].append(register_target)
        if len(self.attachments):
            indexno = 0
            for att in self.attachments:
                att['question_name'] = self.name
                att['indexno'] = indexno
                indexno += 1
        self.data_for_debug = data
    def exec_setup(self, is_generic, the_x, iterators, the_user_dict):
        if is_generic:
            if the_x != 'None':
                exec("x = " + the_x, the_user_dict)
        if len(iterators):
            for indexno in range(len(iterators)):
                exec(list_of_indices[indexno] + " = " + iterators[indexno], the_user_dict)
        for the_field in self.undefine:
            docassemble.base.functions.undefine(the_field)
        if len(self.reconsider) > 0:
            docassemble.base.functions.reconsider(*self.reconsider)
        if self.need is not None:
            for need_code in self.need:
                exec(need_code, the_user_dict)
    def recursive_data_from_code(self, target):
        if isinstance(target, dict) or (hasattr(target, 'elements') and isinstance(target.elements, dict)):
            new_dict = dict()
            for key, val in target.items():
                new_dict[key] = self.recursive_data_from_code(val)
            return new_dict
        if isinstance(target, list) or (hasattr(target, 'elements') and isinstance(target.elements, list)):
            new_list = list()
            for val in target.__iter__():
                new_list.append(self.recursive_data_from_code(val))
            return new_list
        if isinstance(target, set) or (hasattr(target, 'elements') and isinstance(target.elements, set)):
            new_set = set()
            for val in target.__iter__():
                new_set.add(self.recursive_data_from_code(val))
            return new_set
        if isinstance(target, (bool, float, int, NoneType)):
            return target
        self.find_fields_in(target)
        return compile(target, '<expression>', 'eval')
    def recursive_dataobject(self, target):
        if isinstance(target, dict) or (hasattr(target, 'elements') and isinstance(target.elements, dict)):
            new_dict = dict()
            for key, val in target.items():
                new_dict[key] = self.recursive_dataobject(val)
            return new_dict
        if isinstance(target, list) or (hasattr(target, 'elements') and isinstance(target.elements, list)):
            new_list = list()
            for val in target.__iter__():
                new_list.append(self.recursive_dataobject(val))
            return new_list
        if isinstance(target, set) or (hasattr(target, 'elements') and isinstance(target.elements, set)):
            new_set = set()
            for val in target.__iter__():
                new_set.add(self.recursive_dataobject(val, self.mako_names))
            return new_set
        if isinstance(target, (bool, float, int, NoneType)):
            return target
        return TextObject(text_type(target), names_used=self.mako_names)
        
    def find_fields_in(self, code):
        myvisitor = myvisitnode()
        t = ast.parse(text_type(code))
        myvisitor.visit(t)
        predefines = set(globals().keys()) | set(locals().keys())
        if self.scan_for_variables:
            for item in myvisitor.targets.keys():
                if item not in predefines:
                    self.fields_used.add(item)
        definables = set(predefines) | set(myvisitor.targets.keys())
        for item in myvisitor.names.keys():
            if item not in definables:
                self.names_used.add(item)
    def yes(self):
        return word("Yes")
    def no(self):
        return word("No")
    def maybe(self):
        return word("I don't know")
    def back(self):
        return word("Back")
    def help(self):
        return word("Help")
    def process_attachment_code(self, sourcecode):
        try:
            self.compute_attachment = compile(sourcecode, '<expression>', 'eval')
            self.find_fields_in(sourcecode)
            self.sourcecode = sourcecode
        except:
            logmessage("Question: compile error in code:\n" + text_type(sourcecode) + "\n" + str(sys.exc_info()[0]))
            raise
    def process_attachment_list(self, target):
        if isinstance(target, list):
            att_list = list(map((lambda x: self.process_attachment(x)), target))
            return att_list
        else:
            return([self.process_attachment(target)])
    def process_attachment(self, orig_target):
        metadata = dict()
        variable_name = str()
        defs = list()
        options = dict()
        if isinstance(orig_target, dict):
            target = dict()
            for key, value in orig_target.items():
                target[key.lower()] = value
            if 'language' in target:
                options['language'] = target['language']
            if 'name' not in target:
                target['name'] = word("Document")
            if 'filename' not in target:
                #target['filename'] = docassemble.base.functions.space_to_underscore(target['name'])
                target['filename'] = ''
            if 'description' not in target:
                target['description'] = ''
            if 'redact' in target:
                if isinstance(target['redact'], bool) or isinstance(target['redact'], NoneType):
                    options['redact'] = target['redact']
                else:
                    options['redact'] = compile(target['redact'], '<expression>', 'eval')
                    self.find_fields_in(target['redact'])
            if 'checkbox export value' in target and 'pdf template file' in target:
                if not isinstance(target['checkbox export value'], string_types):
                    raise DAError("A checkbox export value must be a string." + self.idebug(target))
                options['checkbox_export_value'] = TextObject(target['checkbox export value'])
            if 'decimal places' in target and 'pdf template file' in target:
                if not isinstance(target['decimal places'], (string_types, int)):
                    raise DAError("A decimal places directive must be an integer or string." + self.idebug(target))
                options['decimal_places'] = TextObject(text_type(target['decimal places']))
            if 'initial yaml' in target:
                if not isinstance(target['initial yaml'], list):
                    target['initial yaml'] = [target['initial yaml']]
                options['initial_yaml'] = list()
                for yaml_file in target['initial yaml']:
                    if not isinstance(yaml_file, string_types):
                        raise DAError('An initial yaml file must be a string.' + self.idebug(target))
                    options['initial_yaml'].append(FileInPackage(yaml_file, 'template', self.package))
            if 'additional yaml' in target:
                if not isinstance(target['additional yaml'], list):
                    target['additional yaml'] = [target['additional yaml']]
                options['additional_yaml'] = list()
                for yaml_file in target['additional yaml']:
                    if not isinstance(yaml_file, string_types):
                        raise DAError('An additional yaml file must be a string.' + self.idebug(target))
                    options['additional_yaml'].append(FileInPackage(yaml_file, 'template', self.package))
            if 'template file' in target:
                if not isinstance(target['template file'], string_types):
                    raise DAError('The template file must be a string.' + self.idebug(target))
                options['template_file'] = FileInPackage(target['template file'], 'template', self.package)
            if 'rtf template file' in target:
                if not isinstance(target['rtf template file'], string_types):
                    raise DAError('The rtf template file must be a string.' + self.idebug(target))
                options['rtf_template_file'] = FileInPackage(target['rtf template file'], 'template', self.package)
            if 'docx reference file' in target:
                if not isinstance(target['docx reference file'], string_types):
                    raise DAError('The docx reference file must be a string.' + self.idebug(target))
                options['docx_reference_file'] = FileInPackage(target['docx reference file'], 'template', self.package)
            if 'usedefs' in target:
                if isinstance(target['usedefs'], string_types):
                    the_list = [target['usedefs']]
                elif isinstance(target['usedefs'], list):
                    the_list = target['usedefs']
                else:
                    raise DAError('The usedefs included in an attachment must be specified as a list of strings or a single string.' + self.idebug(target))
                for def_key in the_list:
                    if not isinstance(def_key, string_types):
                        raise DAError('The defs in an attachment must be strings.' + self.idebug(target))
                    if def_key not in self.interview.defs:
                        raise DAError('Referred to a non-existent def "' + def_key + '."  All defs must be defined before they are used.' + self.idebug(target))
                    defs.extend(self.interview.defs[def_key])
            if 'variable name' in target:
                variable_name = target['variable name']
                if self.scan_for_variables:
                    self.fields_used.add(target['variable name'])
            else:
                variable_name = "_internal['docvar'][" + str(self.interview.next_attachment_number()) + "]"
            if 'metadata' in target:
                if not isinstance(target['metadata'], dict):
                    raise DAError('Unknown data type ' + str(type(target['metadata'])) + ' in attachment metadata.' + self.idebug(target))
                for key in target['metadata']:
                    data = target['metadata'][key]
                    if data is list:
                        for sub_data in data:
                            if sub_data is not str:
                                raise DAError('Unknown data type ' + str(type(sub_data)) + ' in list in attachment metadata' + self.idebug(target))
                        newdata = list(map((lambda x: TextObject(x, names_used=self.mako_names)), data))
                        metadata[key] = newdata
                    elif isinstance(data, string_types):
                        metadata[key] = TextObject(data, names_used=self.mako_names)
                    elif isinstance(data, bool):
                        metadata[key] = data
                    else:
                        raise DAError('Unknown data type ' + str(type(data)) + ' in key in attachment metadata' + self.idebug(target))
            if 'content file' in target:
                if not isinstance(target['content file'], list):
                    target['content file'] = [target['content file']]
                target['content'] = ''
                for content_file in target['content file']:
                    if not isinstance(content_file, string_types):
                        raise DAError('A content file must be specified as text or a list of text filenames' + self.idebug(target))
                    file_to_read = docassemble.base.functions.package_template_filename(content_file, package=self.package)
                    if file_to_read is not None and os.path.isfile(file_to_read) and os.access(file_to_read, os.R_OK):
                        with open(file_to_read, 'rU', encoding='utf-8') as the_file:
                            target['content'] += the_file.read()
                    else:
                        raise DAError('Unable to read content file ' + str(content_file) + ' after trying to find it at ' + str(file_to_read) + self.idebug(target))
            if 'pdf template file' in target and ('code' in target or 'field variables' in target or 'field code' in target or 'raw field variables' in target) and 'fields' not in target:
                target['fields'] = dict()
                field_mode = 'manual'
            elif 'docx template file' in target:
                if 'update references' in target:
                    if isinstance(target['update references'], bool):
                        options['update_references'] = target['update references']
                    elif isinstance(target['update references'], string_types):
                        options['update_references'] = compile(target['update references'], '<expression>', 'eval')
                        self.find_fields_in(target['update references'])
                    else:
                        raise DAError('Unknown data type in attachment "update references".' + self.idebug(target))
                if 'fields' in target:
                    field_mode = 'manual'
                else:
                    target['fields'] = dict()
                    if 'code' in target or 'field variables' in target or 'field code' in target or 'raw field variables' in target:
                        field_mode = 'manual'
                    else:
                        field_mode = 'auto'
            else:
                field_mode = 'manual'
            if 'fields' in target:
                if 'pdf template file' not in target and 'docx template file' not in target:
                    raise DAError('Fields supplied to attachment but no pdf template file or docx template file supplied' + self.idebug(target))
                if 'pdf template file' in target and 'docx template file' in target:
                    raise DAError('You cannot use a pdf template file and a docx template file at the same time' + self.idebug(target))
                if 'pdf template file' in target:
                    template_type = 'pdf'
                    target['valid formats'] = ['pdf']
                    if 'editable' in target:
                        options['editable'] = compile(text_type(target['editable']), '<editable expression>', 'eval')
                elif 'docx template file' in target:
                    template_type = 'docx'
                    if 'valid formats' in target:
                        if isinstance(target['valid formats'], string_types):
                            target['valid formats'] = [target['valid formats']]
                        elif not isinstance(target['valid formats'], list):
                            raise DAError('Unknown data type in attachment valid formats.' + self.idebug(target))
                        if 'rtf to docx' in target['valid formats']:
                            raise DAError('Valid formats cannot include "rtf to docx" when "docx template file" is used' + self.idebug(target))
                    else:
                        target['valid formats'] = ['docx', 'pdf']
                if not isinstance(target[template_type + ' template file'], (string_types, dict)):
                    raise DAError(template_type + ' template file supplied to attachment must be a string or a dict' + self.idebug(target))
                if field_mode == 'auto':
                    options['fields'] = 'auto'
                elif not isinstance(target['fields'], (list, dict)):
                    raise DAError('fields supplied to attachment must be a list or dictionary' + self.idebug(target))
                target['content'] = ''
                options[template_type + '_template_file'] = FileInPackage(target[template_type + ' template file'], 'template', package=self.package)
                if template_type == 'docx' and isinstance(target[template_type + ' template file'], string_types):
                    the_docx_path = options['docx_template_file'].path()
                    if not os.path.isfile(the_docx_path):
                        raise DAError("Missing docx template file " + os.path.basename(the_docx_path))
                    try:
                        docx_template = docassemble.base.file_docx.DocxTemplate(the_docx_path)
                        the_env = custom_jinja_env()
                        the_xml = docx_template.get_xml()
                        the_xml = re.sub(r'<w:p>', '\n<w:p>', the_xml)
                        the_xml = re.sub(r'({[\%\{].*?[\%\}]})', fix_quotes, the_xml)
                        the_xml = docx_template.patch_xml(the_xml)
                        parsed_content = the_env.parse(the_xml)
                    except TemplateError as the_error:
                        if the_error.filename is None:
                            try:
                                the_error.filename = os.path.basename(options['docx_template_file'].path())
                            except:
                                pass
                        if hasattr(the_error, 'lineno') and the_error.lineno is not None:
                            line_number = max(the_error.lineno - 4, 0)
                            the_error.docx_context = map(lambda x: re.sub(r'<[^>]+>', '', x), the_xml.splitlines()[line_number:(line_number + 7)])
                        raise the_error
                    for key in jinja2meta.find_undeclared_variables(parsed_content):
                        if not key.startswith('_'):
                            self.mako_names.add(key)
                if field_mode == 'manual':
                    options['fields'] = recursive_textobject(target['fields'], self.mako_names)
                    if 'code' in target:
                        if isinstance(target['code'], string_types):
                            options['code'] = compile(target['code'], '<expression>', 'eval')
                            self.find_fields_in(target['code'])
                    if 'field variables' in target:
                        if not isinstance(target['field variables'], list):
                            raise DAError('The field variables must be expressed in the form of a list' + self.idebug(target))
                        if 'code dict' not in options:
                            options['code dict'] = dict()
                        for varname in target['field variables']:
                            if not valid_variable_match.match(str(varname)):
                                raise DAError('The variable ' + str(varname) + " cannot be used in a code list" + self.idebug(target))
                            options['code dict'][varname] = compile(varname, '<expression>', 'eval')
                            self.find_fields_in(varname)
                    if 'raw field variables' in target:
                        if not isinstance(target['raw field variables'], list):
                            raise DAError('The raw field variables must be expressed in the form of a list' + self.idebug(target))
                        if 'raw code dict' not in options:
                            options['raw code dict'] = dict()
                        for varname in target['raw field variables']:
                            if not valid_variable_match.match(str(varname)):
                                raise DAError('The variable ' + str(varname) + " cannot be used in a code list" + self.idebug(target))
                            options['raw code dict'][varname] = compile(varname, '<expression>', 'eval')
                            self.find_fields_in(varname)
                    if 'field code' in target:
                        if 'code dict' not in options:
                            options['code dict'] = dict()
                        if not isinstance(target['field code'], list):
                            target['field code'] = [target['field code']]
                        for item in target['field code']:
                            if not isinstance(item, dict):
                                raise DAError('The field code must be expressed in the form of a dictionary' + self.idebug(target))
                            for key, val in item.items():
                                options['code dict'][key] = compile(val, '<expression>', 'eval')
                                self.find_fields_in(val)
            if 'valid formats' in target:
                if isinstance(target['valid formats'], string_types):
                    target['valid formats'] = [target['valid formats']]
                elif not isinstance(target['valid formats'], list):
                    raise DAError('Unknown data type in attachment valid formats.' + self.idebug(target))
                if 'rtf to docx' in target['valid formats'] and 'docx' in target['valid formats']:
                    raise DAError('Valid formats cannot include both "rtf to docx" and "docx."' + self.idebug(target))
            else:
                target['valid formats'] = ['*']
            if 'password' in target:
                options['password'] = TextObject(target['password'])
            if 'template password' in target:
                options['template_password'] = TextObject(target['template password'])
            if 'pdf/a' in target:
                if isinstance(target['pdf/a'], bool):
                    options['pdf_a'] = target['pdf/a']
                elif isinstance(target['pdf/a'], string_types):
                    options['pdf_a'] = compile(target['pdf/a'], '<pdfa expression>', 'eval')
                    self.find_fields_in(target['pdf/a'])
                else:
                    raise DAError('Unknown data type in attachment pdf/a.' + self.idebug(target))
            if 'tagged pdf' in target:
                if isinstance(target['tagged pdf'], bool):
                    options['tagged_pdf'] = target['tagged pdf']
                elif isinstance(target['tagged pdf'], string_types):
                    options['tagged_pdf'] = compile(target['tagged pdf'], '<tagged pdf expression>', 'eval')
                    self.find_fields_in(target['tagged pdf'])
                else:
                    raise DAError('Unknown data type in attachment tagged pdf.' + self.idebug(target))
            if 'content' not in target:
                raise DAError("No content provided in attachment")
            #logmessage("The content is " + str(target['content']))
            return({'name': TextObject(target['name'], names_used=self.mako_names), 'filename': TextObject(target['filename'], names_used=self.mako_names), 'description': TextObject(target['description'], names_used=self.mako_names), 'content': TextObject("\n".join(defs) + "\n" + target['content'], names_used=self.mako_names), 'valid_formats': target['valid formats'], 'metadata': metadata, 'variable_name': variable_name, 'options': options})
        elif isinstance(orig_target, string_types):
            return({'name': TextObject('Document'), 'filename': TextObject('Document'), 'description': TextObject(''), 'content': TextObject(orig_target, names_used=self.mako_names), 'valid_formats': ['*'], 'metadata': metadata, 'variable_name': variable_name, 'options': options})
        else:
            raise DAError("Unknown data type in attachment")

    def ask(self, user_dict, old_user_dict, the_x, iterators, sought, orig_sought):
        #logmessage("ask: orig_sought is " + text_type(orig_sought) + " and q is " + self.name)
        docassemble.base.functions.this_thread.current_question = self
        if the_x != 'None':
            exec("x = " + the_x, user_dict)
        if len(iterators):
            for indexno in range(len(iterators)):
                #logmessage("Running " + list_of_indices[indexno] + " = " + iterators[indexno])
                exec(list_of_indices[indexno] + " = " + iterators[indexno], user_dict)
        if self.need is not None:
            for need_code in self.need:
                exec(need_code, user_dict)
        for the_field in self.undefine:
            docassemble.base.functions.undefine(the_field)
        if len(self.reconsider) > 0:
            docassemble.base.functions.reconsider(*self.reconsider)
        question_text = self.content.text(user_dict)
        #logmessage("Asking " + str(question_text))
        #sys.stderr.write("Asking " + str(question_text) + "\n")
        if self.subcontent is not None:
            subquestion = self.subcontent.text(user_dict)
        else:
            subquestion = None
        the_default_titles = dict()
        if self.language in self.interview.default_title:
            the_default_titles.update(self.interview.default_title[self.language])
        for key, val in self.interview.default_title['*'].items():
            if key not in the_default_titles:
                the_default_titles[key] = val
        extras = dict()
        if hasattr(self, 'undertext') and self.undertext is not None:
            extras['underText'] = self.undertext.text(user_dict)
        elif 'under' in user_dict['_internal'] and user_dict['_internal']['under'] is not None:
            extras['underText'] = user_dict['_internal']['under']
        elif self.language in self.interview.default_screen_parts and 'under' in self.interview.default_screen_parts[self.language]:
            extras['underText'] = self.interview.default_screen_parts[self.language]['under'].text(user_dict)
        elif 'under' in the_default_titles:
            extras['underText'] = the_default_titles['under']
        if hasattr(self, 'righttext') and self.righttext is not None:
            extras['rightText'] = self.righttext.text(user_dict)
        elif 'right' in user_dict['_internal'] and user_dict['_internal']['right'] is not None:
            extras['rightText'] = user_dict['_internal']['right']
        elif self.language in self.interview.default_screen_parts and 'right' in self.interview.default_screen_parts[self.language]:
            extras['rightText'] = self.interview.default_screen_parts[self.language]['right'].text(user_dict)
        elif 'right' in the_default_titles:
            extras['rightText'] = the_default_titles['right']
        for screen_part in ('pre', 'post', 'submit', 'exit link', 'exit label', 'full', 'logo', 'title', 'subtitle', 'tab title', 'short title', 'logo'):
            if screen_part in user_dict['_internal'] and user_dict['_internal'][screen_part] is not None:
                extras[screen_part + ' text'] = user_dict['_internal'][screen_part]
        if self.language in self.interview.default_screen_parts:
            for screen_part in self.interview.default_screen_parts[self.language]:
                if screen_part in ('pre', 'post', 'submit', 'exit link', 'exit label', 'full', 'logo', 'title', 'subtitle', 'tab title', 'short title', 'logo') and (screen_part + ' text') not in extras:
                    extras[screen_part + ' text'] = self.interview.default_screen_parts[self.language][screen_part].text(user_dict)
        for key, val in the_default_titles.items():
            if key in ('pre', 'post', 'submit', 'exit link', 'exit label', 'full', 'logo', 'title', 'subtitle', 'tab title', 'short title', 'logo') and (key + ' text') not in extras:
                extras[key + ' text'] = val
        if len(self.terms):
            extras['terms'] = dict()
            for termitem, definition in self.terms.items():
                extras['terms'][termitem] = dict(definition=definition['definition'].text(user_dict))
        if len(self.autoterms):
            extras['autoterms'] = dict()
            for termitem, definition in self.autoterms.items():
                extras['autoterms'][termitem] = dict(definition=definition['definition'].text(user_dict))
        if self.css is not None:
            extras['css'] = self.css.text(user_dict)
        if self.script is not None:
            extras['script'] = self.script.text(user_dict)
        if self.continuelabel is not None:
            continuelabel = self.continuelabel.text(user_dict)
        elif self.question_type == 'review':
            if 'resume button label' in user_dict['_internal'] and user_dict['_internal']['resume button label'] is not None:
                continuelabel = user_dict['_internal']['resume button label']
            elif self.language in self.interview.default_screen_parts and 'resume button label' in self.interview.default_screen_parts[self.language]:
                continuelabel = self.interview.default_screen_parts[self.language]['resume button label'].text(user_dict)
            elif 'resume button label' in the_default_titles:
                continuelabel = the_default_titles['resume button label']
            else:
                continuelabel = None
        else:
            if 'continue button label' in user_dict['_internal'] and user_dict['_internal']['continue button label'] is not None:
                continuelabel = user_dict['_internal']['continue button label']
            elif self.language in self.interview.default_screen_parts and 'continue button label' in self.interview.default_screen_parts[self.language]:
                continuelabel = self.interview.default_screen_parts[self.language]['continue button label'].text(user_dict)
            elif 'continue button label' in the_default_titles:
                continuelabel = the_default_titles['continue button label']
            else:
                continuelabel = None
        if self.backbuttonlabel is not None:
            extras['back button label text'] = self.backbuttonlabel.text(user_dict)
        elif 'back button label' in user_dict['_internal'] and user_dict['_internal']['back button label'] is not None:
            extras['back button label text'] = user_dict['_internal']['back button label']
        elif self.language in self.interview.default_screen_parts and 'back button label' in self.interview.default_screen_parts[self.language]:
            extras['back button label text'] = self.interview.default_screen_parts[self.language]['back button label'].text(user_dict)
        elif 'back button label' in the_default_titles:
            extras['back button label text'] = the_default_titles['back button label']
        else:
            extras['back button label text'] = None
        if self.helptext is not None:
            if self.helplabel is not None:
                helplabel = self.helplabel.text(user_dict)
            elif 'help label' in user_dict['_internal'] and user_dict['_internal']['help label'] is not None:
                helplabel = user_dict['_internal']['help label']
            elif self.language in self.interview.default_screen_parts and 'help label' in self.interview.default_screen_parts[self.language]:
                helplabel = self.interview.default_screen_parts[self.language]['help label'].text(user_dict)
            elif 'help label' in the_default_titles:
                helplabel = the_default_titles['help label']
            else:
                helplabel = None
            if self.audiovideo is not None and 'help' in self.audiovideo:
                the_audio_video = process_audio_video_list(self.audiovideo['help'], user_dict)
            else:
                the_audio_video = None
            help_content = self.helptext.text(user_dict)
            if re.search(r'[^\s]', help_content) or the_audio_video is not None:
                help_text_list = [{'heading': None, 'content': help_content, 'audiovideo': the_audio_video, 'label': helplabel, 'from': 'question'}]
            else:
                help_text_list = list()
        else:
            help_text_list = list()
            if self.language in self.interview.default_screen_parts and 'help label' in self.interview.default_screen_parts[self.language]:
                extras['help label text'] = self.interview.default_screen_parts[self.language]['help label'].text(user_dict)
            elif 'help label' in the_default_titles:
                extras['help label text'] = the_default_titles['help label']
        interview_help_text_list = self.interview.processed_helptext(user_dict, self.language)
        if len(interview_help_text_list) > 0:
            help_text_list.extend(interview_help_text_list)
        if self.audiovideo is not None and 'question' in self.audiovideo:
            audiovideo = process_audio_video_list(self.audiovideo['question'], user_dict)
        else:
            audiovideo = None
        if self.decorations is not None:
            decorations = list()
            for decoration_item in self.decorations:
                processed_item = dict()
                for key, value in decoration_item.items():
                    processed_item[key] = value.text(user_dict).strip()
                decorations.append(processed_item)
        else:
            decorations = None
        selectcompute = dict()
        defaults = dict()
        defined = dict()
        hints = dict()
        helptexts = dict()
        labels = dict()
        extras['required'] = dict()
        if hasattr(self, 'back_button'):
            if isinstance(self.back_button, (bool, NoneType)):
                extras['back_button'] = self.back_button
            else:
                extras['back_button'] = eval(self.back_button, user_dict)
        if self.reload_after is not None:
            number = str(self.reload_after.text(user_dict))
            if number not in ("False", "false", "Null", "None", "none", "null"):
                if number in ("True", "true"):
                    number = "10"
                if number:
                    number = re.sub(r'[^0-9]', r'', number)
                else:
                    number = "10"
                if int(number) < 4:
                    number = "4"                
                extras['reload_after'] = number
        if hasattr(self, 'allow_downloading'):
            if isinstance(self.allow_downloading, bool):
                extras['allow_downloading'] = self.allow_downloading
            else:
                extras['allow_downloading'] = eval(self.allow_downloading, user_dict)
        if hasattr(self, 'allow_emailing'):
            if isinstance(self.allow_emailing, bool):
                extras['allow_emailing'] = self.allow_emailing
            else:
                extras['allow_emailing'] = eval(self.allow_emailing, user_dict)
        if hasattr(self, 'zip_filename'):
            extras['zip_filename'] = docassemble.base.functions.single_paragraph(self.zip_filename.text(user_dict))
        if self.question_type == 'response':
            extras['content_type'] = self.content_type.text(user_dict)
            # if hasattr(self, 'binaryresponse'):
            #     extras['binaryresponse'] = self.binaryresponse
        elif self.question_type == 'sendfile':
            # if self.response_file:
            #     extras['response_filename'] = self.response_file.path()
            # else:
            #     extras['response_filename'] = None
            extras['content_type'] = self.content_type.text(user_dict)
        elif self.question_type == 'review':
            if hasattr(self, 'skip_undefined') and not self.skip_undefined:
                skip_undefined = False
            else:
                skip_undefined = True
            extras['ok'] = dict()
            for field in self.fields:
                docassemble.base.functions.this_thread.misc['current_field'] = field.number
                extras['ok'][field.number] = False
                if hasattr(field, 'saveas_code'):
                    failed = False
                    for (expression, is_showif) in field.saveas_code:
                        if skip_undefined:
                            try:
                                the_val = eval(expression, user_dict)
                            except LazyNameError:
                                raise
                            except Exception as err:
                                if self.interview.debug:
                                    logmessage("Exception in review block: " + err.__class__.__name__ + ": " + text_type(err))
                                failed = True
                                break
                            if is_showif and not the_val:
                                failed = True
                                break
                        else:
                            the_val = eval(expression, user_dict)
                            if is_showif and not the_val:
                                failed = True
                                break
                    if failed:
                        continue
                if hasattr(field, 'extras'):
                    for key in ('note', 'html', 'min', 'max', 'minlength', 'maxlength', 'step', 'scale', 'inline width'): # 'script', 'css', 
                        if key in field.extras:
                            if key not in extras:
                                extras[key] = dict()
                            if skip_undefined:
                                try:
                                    extras[key][field.number] = field.extras[key].text(user_dict)
                                except LazyNameError:
                                    raise
                                except Exception as err:
                                    if self.interview.debug:
                                        logmessage("Exception in review block: " + err.__class__.__name__ + ": " + text_type(err))
                                    continue
                            else:
                                extras[key][field.number] = field.extras[key].text(user_dict)
                if hasattr(field, 'helptext'):
                    if skip_undefined:
                        try:
                            helptexts[field.number] = field.helptext.text(user_dict)
                        except LazyNameError:
                            raise
                        except Exception as err:
                            if self.interview.debug:
                                logmessage("Exception in review block: " + err.__class__.__name__ + ": " + text_type(err))
                            continue
                    else:
                        helptexts[field.number] = field.helptext.text(user_dict)
                if hasattr(field, 'label'):
                    if skip_undefined:
                        try:
                            labels[field.number] = field.label.text(user_dict)
                        except LazyNameError:
                            raise
                        except Exception as err:
                            if self.interview.debug:
                                logmessage("Exception in review block: " + err.__class__.__name__ + ": " + text_type(err))
                            continue
                    else:
                        labels[field.number] = field.label.text(user_dict)
                extras['ok'][field.number] = True
            if 'current_field' in docassemble.base.functions.this_thread.misc:
                del docassemble.base.functions.this_thread.misc['current_field']
        else:
            only_empty_fields_exist = True
            commands_to_run = list()
            for field in self.fields:
                docassemble.base.functions.this_thread.misc['current_field'] = field.number
                if hasattr(field, 'has_code') and field.has_code:
                    # standalone multiple-choice questions
                    selectcompute[field.number] = list()
                    for choice in field.choices:
                        if 'compute' in choice and isinstance(choice['compute'], CodeType):
                            selectcompute[field.number].extend(process_selections(eval(choice['compute'], user_dict)))
                        else:
                            new_item = dict()
                            if 'image' in choice:
                                new_item['image'] = choice['image']
                            if 'help' in choice:
                                new_item['help'] = choice['help'].text(user_dict)
                            if 'default' in choice:
                                new_item['default'] = choice['default']
                            new_item['key'] = choice['key'].text(user_dict)
                            new_item['label'] = choice['label'].text(user_dict)
                            selectcompute[field.number].append(new_item)
                    if len(selectcompute[field.number]) > 0:
                        only_empty_fields_exist = False
                    else:
                        if hasattr(field, 'datatype') and field.datatype in ('checkboxes', 'object_checkboxes'):
                            ensure_object_exists(from_safeid(field.saveas), field.datatype, user_dict, commands=commands_to_run)
                            commands_to_run.append(from_safeid(field.saveas) + ".gathered = True")
                        else:
                            commands_to_run.append(from_safeid(field.saveas) + ' = None')
                elif hasattr(field, 'choicetype') and field.choicetype == 'compute':
                    # multiple choice field in choices
                    if hasattr(field, 'datatype') and field.datatype in ('object', 'object_radio', 'object_checkboxes', 'checkboxes'):
                        exec("import docassemble.base.core", user_dict)
                    if hasattr(field, 'object_labeler'):
                        labeler_func = eval(field.object_labeler['compute'], user_dict)
                        if not isinstance(labeler_func, types.FunctionType):
                            raise DAError("The object labeler was not a function")
                        user_dict['_DAOBJECTLABELER'] = labeler_func
                    else:
                        labeler_func = None
                    to_compute = field.selections['compute']
                    if field.datatype == 'object_checkboxes':
                        default_exists = False
                        #logmessage("Testing for " + from_safeid(field.saveas))
                        try:
                            eval(from_safeid(field.saveas), user_dict)
                            default_to_use = from_safeid(field.saveas)
                        except:
                            default_to_use = 'None'
                        #logmessage("Running " + '_DAOBJECTDEFAULTDA = ' + default_to_use)
                        exec('_DAOBJECTDEFAULTDA = ' + default_to_use, user_dict)
                    if 'exclude' in field.selections:
                        exclude_list = list()
                        for x in field.selections['exclude']:
                            exclude_list.append(eval(x, user_dict))
                        selectcompute[field.number] = process_selections(eval(to_compute, user_dict), exclude=exclude_list)
                    else:
                        #logmessage("Doing " + field.selections.get('sourcecode', "No source code"))
                        selectcompute[field.number] = process_selections(eval(to_compute, user_dict))
                    if field.datatype == 'object_checkboxes' and '_DAOBJECTDEFAULTDA' in user_dict:
                        del user_dict['_DAOBJECTDEFAULTDA']
                    if labeler_func is not None:
                        del user_dict['_DAOBJECTLABELER']
                    if len(selectcompute[field.number]) > 0:
                        only_empty_fields_exist = False
                    else:
                        if hasattr(field, 'datatype') and field.datatype in ('checkboxes', 'object_checkboxes'):
                            ensure_object_exists(from_safeid(field.saveas), field.datatype, user_dict, commands=commands_to_run)
                            commands_to_run.append(from_safeid(field.saveas) + '.gathered = True')
                        else:
                            commands_to_run.append(from_safeid(field.saveas) + ' = None')
                elif hasattr(field, 'choicetype') and field.choicetype == 'manual':
                    if 'exclude' in field.selections:
                        to_exclude = list()
                        for x in field.selections['exclude']:
                            to_exclude.append(eval(x, user_dict))
                        to_exclude = unpack_list(to_exclude)
                        selectcompute[field.number] = list()
                        for candidate in field.selections['values']:
                            new_item = dict(key=candidate['key'].text(user_dict), label=candidate['label'].text(user_dict))
                            if 'image' in candidate:
                                new_item['image'] = candidate['image']
                            if 'help' in candidate:
                                new_item['help'] = candidate['help'].text(user_dict)
                            if 'default' in candidate:
                                new_item['default'] = candidate['default']
                            if new_item['key'] not in to_exclude:
                                selectcompute[field.number].append(new_item)
                    else:
                        selectcompute[field.number] = list()
                        for item in field.selections['values']:
                            new_item = dict(key=item['key'].text(user_dict), label=item['label'].text(user_dict))
                            if 'image' in item:
                                new_item['image'] = item['image']
                            if 'help' in item:
                                new_item['help'] = item['help'].text(user_dict)
                            if 'default' in item:
                                new_item['default'] = item['default']
                            selectcompute[field.number].append(new_item)
                    if len(selectcompute[field.number]) > 0:
                        only_empty_fields_exist = False
                    else:
                        commands_to_run.append(from_safeid(field.saveas) + ' = None')
                elif hasattr(field, 'saveas') and self.question_type == "multiple_choice":
                    selectcompute[field.number] = list()
                    for item in field.choices:
                        new_item = dict()
                        if 'image' in item:
                            new_item['image'] = item['image']
                        if 'help' in item:
                            new_item['help'] = item['help'].text(user_dict)
                        if 'default' in item:
                            new_item['default'] = item['default']
                        new_item['key'] = item['key'].text(user_dict)
                        new_item['label'] = item['label'].text(user_dict)
                        selectcompute[field.number].append(new_item)
                    if len(selectcompute[field.number]) > 0:
                        only_empty_fields_exist = False
                    else:
                        commands_to_run.append(from_safeid(field.saveas) + ' = None')
                elif self.question_type == "multiple_choice":
                    selectcompute[field.number] = list()
                    for item in field.choices:
                        new_item = dict()
                        if 'image' in item:
                            new_item['image'] = item['image']
                        if 'help' in item:
                            new_item['help'] = item['help'].text(user_dict)
                        if 'default' in item:
                            new_item['default'] = item['default']
                        new_item['label'] = item['label'].text(user_dict)
                        new_item['key'] = item['key']
                        selectcompute[field.number].append(new_item)
                    only_empty_fields_exist = False
                else:
                    only_empty_fields_exist = False
            if len(self.fields) > 0 and only_empty_fields_exist:
                assumed_objects = set()
                for field in self.fields:
                    if hasattr(field, 'saveas'):
                        parse_result = parse_var_name(from_safeid(field.saveas))
                        if not parse_result['valid']:
                            raise DAError("Variable name " + from_safeid(field.saveas) + " is invalid: " + parse_result['reason'])
                        if len(parse_result['objects']):
                            assumed_objects.add(parse_result['objects'][-1])
                        if len(parse_result['bracket_objects']):
                            assumed_objects.add(parse_result['bracket_objects'][-1])
                for var in assumed_objects:
                    if complications.search(var) or var not in user_dict:
                        eval(var, user_dict)
                raise CodeExecute(commands_to_run, self)
            if 'current_field' in docassemble.base.functions.this_thread.misc:
                del docassemble.base.functions.this_thread.misc['current_field']
            extras['ok'] = dict()
            for field in self.fields:
                docassemble.base.functions.this_thread.misc['current_field'] = field.number
                if hasattr(field, 'showif_code'):
                    result = eval(field.showif_code, user_dict)
                    if hasattr(field, 'extras') and 'show_if_sign' in field.extras and field.extras['show_if_sign'] == 0:
                        if result:
                            extras['ok'][field.number] = False
                            continue
                    else:
                        if not result:
                            extras['ok'][field.number] = False
                            continue
                extras['ok'][field.number] = True
                if hasattr(field, 'nota'):
                    if 'nota' not in extras:
                        extras['nota'] = dict()
                    if isinstance(field.nota, bool):
                        extras['nota'][field.number] = field.nota
                    else:
                        extras['nota'][field.number] = field.nota.text(user_dict)
                if isinstance(field.required, bool):
                    extras['required'][field.number] = field.required
                else:
                    extras['required'][field.number] = eval(field.required['compute'], user_dict)
                if hasattr(field, 'max_image_size') and hasattr(field, 'datatype') and field.datatype in ('file', 'files', 'camera', 'user', 'environment'):
                    extras['max_image_size'] = eval(field.max_image_size['compute'], user_dict)
                if hasattr(field, 'accept') and hasattr(field, 'datatype') and field.datatype in ('file', 'files', 'camera', 'user', 'environment'):
                    if 'accept' not in extras:
                        extras['accept'] = dict()
                    extras['accept'][field.number] = eval(field.accept['compute'], user_dict)
                if hasattr(field, 'rows') and hasattr(field, 'datatype') and field.datatype == 'area':
                    if 'rows' not in extras:
                        extras['rows'] = dict()
                    extras['rows'][field.number] = eval(field.rows['compute'], user_dict)
                if hasattr(field, 'validation_messages'):
                    if 'validation messages' not in extras:
                        extras['validation messages'] = dict()
                    extras['validation messages'][field.number] = dict()
                    for validation_key, validation_message_template in field.validation_messages.items():
                        extras['validation messages'][field.number][validation_key] = validation_message_template.text(user_dict)
                if hasattr(field, 'validate'):
                    the_func = eval(field.validate['compute'], user_dict)
                    try:
                        if hasattr(field, 'datatype'):
                            if field.datatype in ('number', 'integer', 'currency', 'range'):
                                the_func(0)
                            elif field.datatype in ('text', 'area', 'password', 'email', 'radio'):
                                the_func('')
                            elif field.datatype == 'date':
                                the_func('01/01/1970')
                            elif field.datatype == 'time':
                                the_func('12:00 AM')
                            elif field.datatype == 'datetime':
                                the_func('01/01/1970 12:00 AM')
                            elif field.datatype.startswith('yesno') or field.datatype.startswith('noyes'):
                                the_func(True)
                        else:
                            the_func('')
                    except DAValidationError as err:
                        pass
                if hasattr(field, 'datatype') and field.datatype in ('object', 'object_radio', 'object_checkboxes'):
                    if field.number not in selectcompute:
                        raise DAError("datatype was set to object but no code or selections was provided")
                    string = "_internal['objselections'][" + repr(from_safeid(field.saveas)) + "] = dict()"
                    # logmessage("Doing " + string)
                    try:
                        exec(string, user_dict)
                        for selection in selectcompute[field.number]:
                            key = selection['key']
                            #logmessage("key is " + str(key))
                            real_key = codecs.decode(bytearray(key, encoding='utf-8'), 'base64').decode('utf8')
                            string = "_internal['objselections'][" + repr(from_safeid(field.saveas)) + "][" + repr(key) + "] = " + real_key
                            #logmessage("Doing " + string)
                            exec(string, user_dict)
                    except Exception as err:
                        raise DAError("Failure while processing field with datatype of object: " + str(err))
                if hasattr(field, 'label'):
                    labels[field.number] = field.label.text(user_dict)
                if hasattr(field, 'extras'):
                    if 'fields_code' in field.extras:
                        field_list = eval(field.extras['fields_code'], user_dict)
                        if not isinstance(field_list, list):
                            raise DAError("A code directive that defines items in fields must return a list")
                        new_interview_source = InterviewSourceString(content='')
                        new_interview = new_interview_source.get_interview()
                        reproduce_basics(self.interview, new_interview)
                        the_question = Question(dict(question='n/a', fields=field_list), new_interview, source=new_interview_source, package=self.package)
                        ask_result = the_question.ask(user_dict, old_user_dict, the_x, iterators, sought, orig_sought)
                        for key in ('selectcompute', 'defaults', 'hints', 'helptexts', 'labels'):
                            for field_num, val in ask_result[key].items():
                                if key == 'selectcompute':
                                    selectcompute[str(field.number) + '_' + str(field_num)] = val
                                elif key == 'defaults':
                                    defaults[str(field.number) + '_' + str(field_num)] = val
                                elif key == 'hints':
                                    hints[str(field.number) + '_' + str(field_num)] = val
                                elif key == 'helptexts':
                                    helptexts[str(field.number) + '_' + str(field_num)] = val
                                elif key == 'labels':
                                    labels[str(field.number) + '_' + str(field_num)] = val
                        for key, possible_dict in ask_result['extras'].items():
                            #logmessage(repr("key is " + str(key) + " and possible dict is " + repr(possible_dict)))
                            if isinstance(possible_dict, dict):
                                #logmessage("key points to a dict")
                                if key not in extras:
                                    extras[key] = dict()
                                for field_num, val in possible_dict.items():
                                    #logmessage("Setting " + str(field.number) + '_' + str(field_num))
                                    extras[key][str(field.number) + '_' + str(field_num)] = val
                        for sub_field in the_question.fields:
                            sub_field.number = str(field.number) + '_' + str(sub_field.number)
                        if 'sub_fields' not in extras:
                            extras['sub_fields'] = dict()
                        extras['sub_fields'][field.number] = the_question.fields
                    for key in ('note', 'html', 'min', 'max', 'minlength', 'maxlength', 'show_if_val', 'step', 'scale', 'inline width', 'ml_group'): # , 'textresponse', 'content_type' #'script', 'css', 
                        if key in field.extras:
                            if key not in extras:
                                extras[key] = dict()
                            extras[key][field.number] = field.extras[key].text(user_dict)
                    for key in ('ml_train',):
                        if key in field.extras:
                            if key not in extras:
                                extras[key] = dict()
                            if isinstance(field.extras[key], bool):
                                extras[key][field.number] = field.extras[key]
                            else:
                                extras[key][field.number] = eval(field.extras[key]['compute'], user_dict)
                if hasattr(field, 'saveas'):
                    try:
                        if old_user_dict is not None:
                            try:
                                defaults[field.number] = eval(from_safeid(field.saveas), old_user_dict)
                            except:
                                defaults[field.number] = eval(from_safeid(field.saveas), user_dict)
                        else:
                            defaults[field.number] = eval(from_safeid(field.saveas), user_dict)
                    except:
                        if hasattr(field, 'default'):
                            if isinstance(field.default, TextObject):
                                defaults[field.number] = field.default.text(user_dict).strip()
                            else:
                                defaults[field.number] = field.default
                        elif hasattr(field, 'extras') and 'default' in field.extras:
                            defaults[field.number] = eval(field.extras['default']['compute'], user_dict)
                    if hasattr(field, 'helptext'):
                        helptexts[field.number] = field.helptext.text(user_dict)
                    if hasattr(field, 'hint'):
                        hints[field.number] = field.hint.text(user_dict)
            if 'current_field' in docassemble.base.functions.this_thread.misc:
                del docassemble.base.functions.this_thread.misc['current_field']
        if len(self.attachments) or self.compute_attachment is not None:
            attachment_text = self.processed_attachments(user_dict) # , the_x=the_x, iterators=iterators
        else:
            attachment_text = []
        assumed_objects = set()
        for field in self.fields:
            docassemble.base.functions.this_thread.misc['current_field'] = field.number
            if hasattr(field, 'saveas'):
                # m = re.match(r'(.*)\.[^\.]+', from_safeid(field.saveas))
                # if m and m.group(1) != 'x':
                #     assumed_objects.add(m.group(1))
                parse_result = parse_var_name(from_safeid(field.saveas))
                if not parse_result['valid']:
                    raise DAError("Variable name " + from_safeid(field.saveas) + " is invalid: " + parse_result['reason'])
                if len(parse_result['objects']):
                    assumed_objects.add(parse_result['objects'][-1])
                if len(parse_result['bracket_objects']):
                    assumed_objects.add(parse_result['bracket_objects'][-1])
        if 'current_field' in docassemble.base.functions.this_thread.misc:
            del docassemble.base.functions.this_thread.misc['current_field']
        for var in assumed_objects:
            if complications.search(var) or var not in user_dict:
                eval(var, user_dict)
        if 'menu_items' in user_dict:
            extras['menu_items'] = user_dict['menu_items']
        if 'track_location' in user_dict:
            extras['track_location'] = user_dict['track_location']
        if 'speak_text' in user_dict:
            extras['speak_text'] = user_dict['speak_text']
        if 'role' in user_dict:
            current_role = user_dict['role']
            if len(self.role) > 0:
                if current_role not in self.role and 'role_event' not in self.fields_used and self.question_type not in ('exit', 'logout', 'exit_logout', 'continue', 'restart', 'leave', 'refresh', 'signin', 'register', 'new_session'):
                    # logmessage("Calling role_event with " + ", ".join(self.fields_used))
                    user_dict['role_needed'] = self.role
                    raise NameError("name 'role_event' is not defined")
            elif self.interview.default_role is not None and current_role not in self.interview.default_role and 'role_event' not in self.fields_used and self.question_type not in ('exit', 'logout', 'exit_logout', 'continue', 'restart', 'leave', 'refresh', 'signin', 'register', 'new_session'):
                # logmessage("Calling role_event with " + ", ".join(self.fields_used))
                user_dict['role_needed'] = self.interview.default_role
                raise NameError("name 'role_event' is not defined")
        if self.question_type == 'review' and sought is not None:
            if 'event_stack' not in user_dict['_internal']:
                user_dict['_internal']['event_stack'] = dict()
            session_uid = docassemble.base.functions.this_thread.current_info['user']['session_uid']
            if session_uid not in user_dict['_internal']['event_stack']:
                user_dict['_internal']['event_stack'][session_uid] = list()
            already_there = False
            for event_item in user_dict['_internal']['event_stack'][session_uid]:
                if event_item['action'] in (sought, orig_sought):
                    already_there = True
                    break
            if not already_there:
                user_dict['_internal']['event_stack'][session_uid].insert(0, dict(action=orig_sought, arguments=dict()))
        return({'type': 'question', 'question_text': question_text, 'subquestion_text': subquestion, 'continue_label': continuelabel, 'audiovideo': audiovideo, 'decorations': decorations, 'help_text': help_text_list, 'attachments': attachment_text, 'question': self, 'selectcompute': selectcompute, 'defaults': defaults, 'hints': hints, 'helptexts': helptexts, 'extras': extras, 'labels': labels, 'sought': sought, 'orig_sought': orig_sought}) #'defined': defined, 
    def processed_attachments(self, the_user_dict, **kwargs):
        use_cache = kwargs.get('use_cache', True)
        if self.compute_attachment is not None:
            use_cache = False
        seeking_var = kwargs.get('seeking_var', '__novar')
        steps = the_user_dict['_internal'].get('steps', -1)
        #logmessage("processed_attachments: steps is " + str(steps))
        if use_cache and self.interview.cache_documents and hasattr(self, 'name') and self.name + '__SEEKING__' + seeking_var in the_user_dict['_internal']['doc_cache']:
            if steps in the_user_dict['_internal']['doc_cache'][self.name + '__SEEKING__' + seeking_var]:
                #logmessage("processed_attachments: result was in document cache")
                return the_user_dict['_internal']['doc_cache'][self.name + '__SEEKING__' + seeking_var][steps]
            the_user_dict['_internal']['doc_cache'][self.name + '__SEEKING__' + seeking_var].clear()
        result_list = list()
        items = list()
        for x in self.attachments:
            items.append([x, self.prepare_attachment(x, the_user_dict, **kwargs), None])
        for item in items:
            result_list.append(self.finalize_attachment(item[0], item[1], the_user_dict))
        if self.compute_attachment is not None:
            computed_attachment_list = eval(self.compute_attachment, the_user_dict)
            if not isinstance(computed_attachment_list, list):
                computed_attachment_list = [computed_attachment_list]
            for the_att in computed_attachment_list:
                if the_att.__class__.__name__ == 'DAFileCollection':
                    file_dict = dict()
                    for doc_format in ('pdf', 'rtf', 'docx', 'rtf to docx', 'tex', 'html'):
                        if hasattr(the_att, doc_format):
                            the_dafile = getattr(the_att, doc_format)
                            if hasattr(the_dafile, 'number'):
                                file_dict[doc_format] = the_dafile.number
                    if 'formats' not in the_att.info:
                        the_att.info['formats'] = file_dict.keys()
                        if 'valid_formats' not in the_att.info:
                            the_att.info['valid_formats'] = file_dict.keys()
                    result_list.append({'name': the_att.info['name'], 'filename': the_att.info['filename'], 'description': the_att.info['description'], 'valid_formats': the_att.info.get('valid_formats', ['*']), 'formats_to_use': the_att.info['formats'], 'markdown': the_att.info.get('markdown', dict()), 'content': the_att.info.get('content', dict()), 'extension': the_att.info.get('extension', dict()), 'mimetype': the_att.info.get('mimetype', dict()), 'file': file_dict, 'metadata': the_att.info.get('metadata', dict()), 'variable_name': str()})
                    #convert_to_pdf_a
                    #file is dict of file numbers
                # if the_att.__class__.__name__ == 'DAFileCollection' and 'attachment' in the_att.info and isinstance(the_att.info, dict) and 'name' in the_att.info['attachment'] and 'number' in the_att.info['attachment'] and len(self.interview.questions_by_name[the_att.info['attachment']['name']].attachments) > the_att.info['attachment']['number']:
                #     attachment = self.interview.questions_by_name[the_att.info['attachment']['name']].attachments[the_att.info['attachment']['number']]
                #     items.append([attachment, self.prepare_attachment(attachment, the_user_dict, **kwargs)])
        if self.interview.cache_documents and hasattr(self, 'name'):
            if self.name + '__SEEKING__' + seeking_var not in the_user_dict['_internal']['doc_cache']:
                the_user_dict['_internal']['doc_cache'][self.name + '__SEEKING__' + seeking_var] = dict()
            the_user_dict['_internal']['doc_cache'][self.name + '__SEEKING__' + seeking_var][steps] = result_list
        return result_list
        #return(list(map((lambda x: self.make_attachment(x, the_user_dict, **kwargs)), self.attachments)))
    def parse_fields(self, the_list, register_target, uses_field):
        result_list = list()
        has_code = False
        if isinstance(the_list, dict):
            new_list = list()
            for key, value in the_list.items():
                new_item = dict()
                new_item[key] = value
                new_list.append(new_item)
            the_list = new_list
        if not isinstance(the_list, list):
            raise DAError("Multiple choices need to be provided in list form.  " + self.idebug(the_list))
        for the_dict in the_list:
            if not isinstance(the_dict, (dict, list)):
                the_dict = {text_type(the_dict): the_dict}
            elif not isinstance(the_dict, dict):
                raise DAError("Unknown data type for the_dict in parse_fields.  " + self.idebug(the_list))
            result_dict = dict()
            for key, value in the_dict.items():
                if len(the_dict) > 1:
                    if key == 'image':
                        result_dict['image'] = value
                        continue
                    if key == 'help':
                        result_dict['help'] = TextObject(value)
                        continue
                    if key == 'default':
                        result_dict['default'] = value
                        continue
                if uses_field:
                    if key == 'code':
                        has_code = True
                        result_dict['compute'] = compile(value, '<expression>', 'eval')
                        self.find_fields_in(value)
                    else:
                        result_dict['label'] = TextObject(key)
                        result_dict['key'] = TextObject(value)
                elif isinstance(value, dict):
                    result_dict['label'] = TextObject(key)
                    self.embeds = True
                    if PY3:
                        result_dict['key'] = Question(value, self.interview, register_target=register_target, source=self.from_source, package=self.package, source_code=codecs.decode(bytearray(yaml.safe_dump(value, default_flow_style=False, default_style = '|', allow_unicode=True), encoding='utf-8'), 'utf-8'))
                    else:
                        result_dict['key'] = Question(value, self.interview, register_target=register_target, source=self.from_source, package=self.package, source_code=codecs.decode(yaml.safe_dump(value, default_flow_style=False, default_style = '|', allow_unicode=True), 'utf-8'))
                elif isinstance(value, string_types):
                    if value in ('exit', 'logout', 'exit_logout', 'leave') and 'url' in the_dict:
                        self.embeds = True
                        result_dict['label'] = TextObject(key)
                        result_dict['key'] = Question({'command': value, 'url': the_dict['url']}, self.interview, register_target=register_target, source=self.from_source, package=self.package)
                    elif value in ('continue', 'restart', 'refresh', 'signin', 'register', 'exit', 'logout', 'exit_logout', 'leave', 'new_session'):
                        self.embeds = True
                        result_dict['label'] = TextObject(key)
                        result_dict['key'] = Question({'command': value}, self.interview, register_target=register_target, source=self.from_source, package=self.package)
                    elif key == 'url':
                        pass
                    else:
                        result_dict['label'] = TextObject(key)
                        result_dict['key'] = value
                elif isinstance(value, bool):
                    result_dict['label'] = TextObject(key)
                    result_dict['key'] = value
                else:
                    raise DAError("Unknown data type in parse_fields:" + str(type(value)) + ".  " + self.idebug(the_list))
            result_list.append(result_dict)
        return(has_code, result_list)
    def mark_as_answered(self, the_user_dict):
        if self.is_mandatory or self.mandatory_code is not None:
            the_user_dict['_internal']['answered'].add(self.name)
    def sub_fields_used(self):
        all_fields_used = set()
        for var_name in self.fields_used:
            all_fields_used.add(var_name)
        if len(self.fields) > 0 and hasattr(self.fields[0], 'choices'):
            for choice in self.fields[0].choices:
                if isinstance(choice['key'], Question):
                    all_fields_used.update(choice['key'].sub_fields_used())
        return all_fields_used
    def extended_question_name(self, the_user_dict):
        if not self.name:
            return self.name
        the_name = self.name
        uses = set()
        for var_name in self.sub_fields_used():
            if re.search(r'^x\b', var_name):
                uses.add('x')
            for iterator in re.findall(r'\[([ijklmn])\]', var_name):
                uses.add(iterator)
        if len(uses) > 0:
            ok_to_use_extra = True
            for var_name in uses:
                if var_name not in the_user_dict:
                    ok_to_use_extra = False
            if ok_to_use_extra and 'x' in uses and not hasattr(the_user_dict['x'], 'instanceName'):
                ok_to_use_extra = False
            if ok_to_use_extra:
                extras = []
                if 'x' in uses:
                    extras.append(the_user_dict['x'].instanceName)
                for var_name in ['i', 'j', 'k', 'l', 'm', 'n']:
                    if var_name in uses:
                        extras.append(text_type(the_user_dict[var_name]))
                the_name += "|WITH|" + '|'.join(extras)
        return the_name
    def follow_multiple_choice(self, the_user_dict, interview_status, is_generic, the_x, iterators):
        if not self.embeds:
            return(self)
        if is_generic:
            if the_x != 'None':
                exec("x = " + the_x, the_user_dict)
        if len(iterators):
            for indexno in range(len(iterators)):
                exec(list_of_indices[indexno] + " = " + iterators[indexno], the_user_dict)
        the_name = self.extended_question_name(the_user_dict)
        if the_name and the_name in the_user_dict['_internal']['answers']:
            interview_status.followed_mc = True
            interview_status.tentatively_answered.add(self)
            qtarget = self.fields[0].choices[the_user_dict['_internal']['answers'][the_name]].get('key', False)
            if isinstance(qtarget, Question):
                return(qtarget.follow_multiple_choice(the_user_dict, interview_status, is_generic, the_x, iterators))
        return(self)
    def finalize_attachment(self, attachment, result, the_user_dict):
        if self.interview.cache_documents and attachment['variable_name']:
            try:
                existing_object = eval(attachment['variable_name'], the_user_dict)
                for doc_format in ('pdf', 'rtf', 'docx', 'rtf to docx', 'tex', 'html'):
                    if hasattr(existing_object, doc_format):
                        the_file = getattr(existing_object, doc_format)
                        for key in ('extension', 'mimetype', 'content', 'markdown'):
                            if hasattr(the_file, key):
                                result[key][doc_format] = getattr(the_file, key)
                        if hasattr(the_file, 'number'):
                            result['file'][doc_format] = the_file.number
                #logmessage("finalize_attachment: returning " + attachment['variable_name'] + " from cache")
                for key in ('template', 'field_data', 'images', 'data_strings', 'convert_to_pdf_a', 'convert_to_tagged_pdf', 'password', 'template_password', 'update_references'):
                    if key in result:
                        del result[key]
                return result
            except:
                pass
            #logmessage("finalize_attachment: " + attachment['variable_name'] + " was not in cache")
        #logmessage("In finalize where redact is " + repr(result['redact']))
        docassemble.base.functions.this_thread.misc['redact'] = result['redact']
        for doc_format in result['formats_to_use']:
            if doc_format in ('pdf', 'rtf', 'rtf to docx', 'tex', 'docx'):
                if 'fields' in attachment['options']:
                    if doc_format == 'pdf' and 'pdf_template_file' in attachment['options']:
                        docassemble.base.functions.set_context('pdf')
                        the_pdf_file = docassemble.base.pdftk.fill_template(attachment['options']['pdf_template_file'].path(the_user_dict=the_user_dict), data_strings=result['data_strings'], images=result['images'], editable=result['editable'], pdfa=result['convert_to_pdf_a'], password=result['password'], template_password=result['template_password'])
                        result['file'][doc_format], result['extension'][doc_format], result['mimetype'][doc_format] = docassemble.base.functions.server.save_numbered_file(result['filename'] + '.' + extension_of_doc_format[doc_format], the_pdf_file, yaml_file_name=self.interview.source.path)
                        for key in ('images', 'data_strings', 'convert_to_pdf_a', 'convert_to_tagged_pdf', 'password', 'template_password', 'update_references'):
                            if key in result:
                                del result[key]
                        docassemble.base.functions.reset_context()
                    elif (doc_format == 'docx' or (doc_format == 'pdf' and 'docx' not in result['formats_to_use'])) and 'docx_template_file' in attachment['options']:
                        #logmessage("field_data is " + str(result['field_data']))
                        docassemble.base.functions.set_context('docx', template=result['template'])
                        try:
                            the_template = result['template']
                            while True:
                                old_count = docassemble.base.functions.this_thread.misc.get('docx_include_count', 0)
                                the_template.render(result['field_data'], jinja_env=custom_jinja_env())
                                if docassemble.base.functions.this_thread.misc.get('docx_include_count', 0) > old_count and old_count < 10:
                                    new_template_file = tempfile.NamedTemporaryFile(prefix="datemp", mode="wb", suffix=".docx", delete=False)
                                    the_template.save(new_template_file.name)
                                    the_template = docassemble.base.file_docx.DocxTemplate(new_template_file.name)
                                    docassemble.base.functions.this_thread.misc['docx_template'] = the_template
                                else:
                                    break
                        except TemplateError as the_error:
                            if (not hasattr(the_error, 'filename')) or the_error.filename is None:
                                the_error.filename = os.path.basename(attachment['options']['docx_template_file'].path(the_user_dict=the_user_dict))
                            #logmessage("TemplateError:\n" + traceback.format_exc())
                            raise the_error
                        docassemble.base.functions.reset_context()
                        docx_file = tempfile.NamedTemporaryFile(prefix="datemp", mode="wb", suffix=".docx", delete=False)
                        the_template.save(docx_file.name)
                        if result['update_references']:
                            docassemble.base.pandoc.update_references(docx_file.name)
                        if 'docx' in result['formats_to_use']:
                            result['file']['docx'], result['extension']['docx'], result['mimetype']['docx'] = docassemble.base.functions.server.save_numbered_file(result['filename'] + '.docx', docx_file.name, yaml_file_name=self.interview.source.path)
                        if 'pdf' in result['formats_to_use']:
                            pdf_file = tempfile.NamedTemporaryFile(prefix="datemp", mode="wb", suffix=".pdf", delete=False)
                            docassemble.base.pandoc.word_to_pdf(docx_file.name, 'docx', pdf_file.name, pdfa=result['convert_to_pdf_a'], password=result['password'], update_refs=result['update_references'], tagged=result['convert_to_tagged_pdf'])
                            result['file']['pdf'], result['extension']['pdf'], result['mimetype']['pdf'] = docassemble.base.functions.server.save_numbered_file(result['filename'] + '.pdf', pdf_file.name, yaml_file_name=self.interview.source.path)
                        for key in ['template', 'field_data', 'images', 'data_strings', 'convert_to_pdf_a', 'convert_to_tagged_pdf', 'password', 'template_password', 'update_references']:
                            if key in result:
                                del result[key]
                else:
                    converter = MyPandoc(pdfa=result['convert_to_pdf_a'], password=result['password'])
                    converter.output_format = doc_format
                    converter.input_content = result['markdown'][doc_format]
                    if 'initial_yaml' in attachment['options']:
                        converter.initial_yaml = [x.path(the_user_dict=the_user_dict) for x in attachment['options']['initial_yaml']]
                    elif 'initial_yaml' in self.interview.attachment_options:
                        converter.initial_yaml = [x.path(the_user_dict=the_user_dict) for x in self.interview.attachment_options['initial_yaml']]
                    if 'additional_yaml' in attachment['options']:
                        converter.additional_yaml = [x.path(the_user_dict=the_user_dict) for x in attachment['options']['additional_yaml']]
                    elif 'additional_yaml' in self.interview.attachment_options:
                        converter.additional_yaml = [x.path(the_user_dict=the_user_dict) for x in self.interview.attachment_options['additional_yaml']]
                    if doc_format in ('rtf', 'rtf to docx'):
                        if 'rtf_template_file' in attachment['options']:
                            converter.template_file = attachment['options']['rtf_template_file'].path(the_user_dict=the_user_dict)
                        elif 'rtf_template_file' in self.interview.attachment_options:
                            converter.template_file = self.interview.attachment_options['rtf_template_file'].path(the_user_dict=the_user_dict)
                    elif doc_format == 'docx':
                        if 'docx_reference_file' in attachment['options']:
                            converter.reference_file = attachment['options']['docx_reference_file'].path(the_user_dict=the_user_dict)
                        elif 'docx_reference_file' in self.interview.attachment_options:
                            converter.reference_file = self.interview.attachment_options['docx_reference_file'].path(the_user_dict=the_user_dict)
                    else:
                        if 'template_file' in attachment['options']:
                            converter.template_file = attachment['options']['template_file'].path(the_user_dict=the_user_dict)
                        elif 'template_file' in self.interview.attachment_options:
                            converter.template_file = self.interview.attachment_options['template_file'].path(the_user_dict=the_user_dict)
                    converter.metadata = result['metadata']
                    converter.convert(self)
                    result['file'][doc_format], result['extension'][doc_format], result['mimetype'][doc_format] = docassemble.base.functions.server.save_numbered_file(result['filename'] + '.' + extension_of_doc_format[doc_format], converter.output_filename, yaml_file_name=self.interview.source.path)
                    result['content'][doc_format] = result['markdown'][doc_format]
            elif doc_format in ['html']:
                result['content'][doc_format] = docassemble.base.filter.markdown_to_html(result['markdown'][doc_format], use_pandoc=True, question=self)
        if attachment['variable_name']:
            string = "import docassemble.base.core"
            exec(string, the_user_dict)
            variable_name = attachment['variable_name']
            m = re.search(r'^(.*)\.([A-Za-z0-9\_]+)$', attachment['variable_name'])
            if m:
                base_var = m.group(1)
                attrib = m.group(2)
                the_var = eval(base_var, the_user_dict)
                if hasattr(the_var, 'instanceName'):
                    variable_name = the_var.instanceName + '.' + attrib
            string = variable_name + " = docassemble.base.core.DAFileCollection(" + repr(variable_name) + ")"
            # logmessage("Executing " + string + "\n")
            exec(string, the_user_dict)
            the_name = attachment['name'].text(the_user_dict).strip()
            the_filename = attachment['filename'].text(the_user_dict).strip()
            if the_filename == '':
                the_filename = docassemble.base.functions.space_to_underscore(the_name)
            the_user_dict['_attachment_info'] = dict(name=the_name, filename=the_filename, description=attachment['description'].text(the_user_dict), valid_formats=result['valid_formats'], formats=result['formats_to_use'], attachment=dict(name=attachment['question_name'], number=attachment['indexno']), extension=result.get('extension', dict()), mimetype=result.get('mimetype', dict()), content=result.get('content', dict()), markdown=result.get('markdown', dict()), metadata=result.get('metadata', dict()), convert_to_pdf_a=result.get('convert_to_pdf_a', False), convert_to_tagged_pdf=result.get('convert_to_tagged_pdf', False))
            exec(variable_name + '.info = _attachment_info', the_user_dict)
            del the_user_dict['_attachment_info']
            for doc_format in result['file']:
                variable_string = variable_name + '.' + extension_of_doc_format[doc_format]
                # filename = result['filename'] + '.' + doc_format
                # file_number, extension, mimetype = docassemble.base.functions.server.save_numbered_file(filename, result['file'][doc_format], yaml_file_name=self.interview.source.path)
                if result['file'][doc_format] is None:
                    raise Exception("Could not save numbered file")
                if 'content' in result and doc_format in result['content']:
                    content_string = ', content=' + repr(result['content'][doc_format])
                else:
                    content_string = ''
                if 'markdown' in result and doc_format in result['markdown']:
                    markdown_string = ', markdown=' + repr(result['markdown'][doc_format])
                else:
                    markdown_string = ''
                string = variable_string + " = docassemble.base.core.DAFile(" + repr(variable_string) + ", filename=" + repr(str(result['filename']) + '.' + extension_of_doc_format[doc_format]) + ", number=" + str(result['file'][doc_format]) + ", mimetype='" + str(result['mimetype'][doc_format]) + "', extension='" + str(result['extension'][doc_format]) + "'" + content_string + markdown_string + ")"
                #logmessage("Executing " + string + "\n")
                exec(string, the_user_dict)
            for doc_format in result['content']:
                # logmessage("Considering " + doc_format)
                if doc_format not in result['file']:
                    variable_string = variable_name + '.' + extension_of_doc_format[doc_format]
                    # logmessage("Setting " + variable_string)
                    string = variable_string + " = docassemble.base.core.DAFile(" + repr(variable_string) + ', markdown=' + repr(result['markdown'][doc_format]) + ', content=' + repr(result['content'][doc_format]) + ")"
                    exec(string, the_user_dict)
        return(result)
    def prepare_attachment(self, attachment, the_user_dict, **kwargs):
        if 'language' in attachment['options']:
            old_language = docassemble.base.functions.get_language()
            docassemble.base.functions.set_language(attachment['options']['language'])
        else:
            old_language = None
        the_name = attachment['name'].text(the_user_dict).strip()
        the_filename = attachment['filename'].text(the_user_dict).strip()
        if the_filename == '':
            the_filename = docassemble.base.functions.space_to_underscore(the_name)
        result = {'name': the_name, 'filename': the_filename, 'description': attachment['description'].text(the_user_dict), 'valid_formats': attachment['valid_formats']}
        if 'redact' in attachment['options']:
            if isinstance(attachment['options']['redact'], CodeType):
                result['redact'] = eval(attachment['options']['redact'], the_user_dict)
            else:
                result['redact'] = attachment['options']['redact']
        else:
            result['redact'] = True
        if 'editable' in attachment['options']:
            result['editable'] = eval(attachment['options']['editable'], the_user_dict)
        else:
            result['editable'] = True
        docassemble.base.functions.this_thread.misc['redact'] = result['redact']
        result['markdown'] = dict();
        result['content'] = dict();
        result['extension'] = dict();
        result['mimetype'] = dict();
        result['file'] = dict();
        if '*' in attachment['valid_formats']:
            result['formats_to_use'] = ['pdf', 'rtf', 'html']
        else:
            result['formats_to_use'] = attachment['valid_formats']
        result['metadata'] = dict()
        if len(attachment['metadata']) > 0:
            for key in attachment['metadata']:
                data = attachment['metadata'][key]
                if isinstance(data, bool):
                    result['metadata'][key] = data
                elif isinstance(data, list):
                    result['metadata'][key] = textify(data, the_user_dict)
                else:
                    result['metadata'][key] = data.text(the_user_dict)
        if 'pdf_a' in attachment['options']:
            if isinstance(attachment['options']['pdf_a'], bool):
                result['convert_to_pdf_a'] = attachment['options']['pdf_a']
            else:
                result['convert_to_pdf_a'] = eval(attachment['options']['pdf_a'], the_user_dict)
        else:
            result['convert_to_pdf_a'] = self.interview.use_pdf_a
        if 'tagged_pdf' in attachment['options']:
            if isinstance(attachment['options']['tagged_pdf'], bool):
                result['convert_to_tagged_pdf'] = attachment['options']['tagged_pdf']
            else:
                result['convert_to_tagged_pdf'] = eval(attachment['options']['tagged_pdf'], the_user_dict)
        else:
            result['convert_to_tagged_pdf'] = self.interview.use_tagged_pdf
        if 'update_references' in attachment['options']:
            if isinstance(attachment['options']['update_references'], bool):
                result['update_references'] = attachment['options']['update_references']
            else:
                result['update_references'] = eval(attachment['options']['update_references'], the_user_dict)
        else:
            result['update_references'] = False
        if 'password' in attachment['options']:
            result['password'] = attachment['options']['password'].text(the_user_dict)
        else:
            result['password'] = None
        if 'template_password' in attachment['options']:
            result['template_password'] = attachment['options']['template_password'].text(the_user_dict)
        else:
            result['template_password'] = None
        for doc_format in result['formats_to_use']:
            if doc_format in ['pdf', 'rtf', 'rtf to docx', 'tex', 'docx']:
                if 'decimal_places' in attachment['options']:
                    try:
                        float_formatter = '%.' + str(int(attachment['options']['decimal_places'].text(the_user_dict).strip())) + 'f'
                    except:
                        logmessage("prepare_attachment: error in float_formatter")
                        float_formatter = None
                else:
                    float_formatter = None
                if 'fields' in attachment['options'] and 'docx_template_file' in attachment['options']:
                    if doc_format == 'docx' or ('docx' not in result['formats_to_use'] and doc_format == 'pdf'):
                        result['template'] = docassemble.base.file_docx.DocxTemplate(attachment['options']['docx_template_file'].path(the_user_dict=the_user_dict))
                        docassemble.base.functions.set_context('docx', template=result['template'])
                        if isinstance(attachment['options']['fields'], string_types):
                            result['field_data'] = the_user_dict
                        else:
                            the_field_data = recursive_eval_textobject(attachment['options']['fields'], the_user_dict, self, result['template'])
                            new_field_data = dict()
                            if isinstance(the_field_data, list):
                                for item in the_field_data:
                                    if isinstance(item, dict):
                                        new_field_data.update(item)
                                the_field_data = new_field_data
                            result['field_data'] = the_field_data
                        result['field_data']['_codecs'] = codecs
                        result['field_data']['_array'] = array
                        if 'code' in attachment['options']:
                            additional_dict = eval(attachment['options']['code'], the_user_dict)
                            if isinstance(additional_dict, dict):
                                for key, val in additional_dict.items():
                                    if isinstance(val, float) and float_formatter is not None:
                                        result['field_data'][key] = float_formatter % val
                                    elif isinstance(val, RawValue):
                                        result['field_data'][key] = val.value
                                    else:
                                        result['field_data'][key] = docassemble.base.file_docx.transform_for_docx(val, self, result['template'])
                            else:
                                raise DAError("code in an attachment returned something other than a dictionary")
                        if 'raw code dict' in attachment['options']:
                            for varname, var_code in attachment['options']['raw code dict'].items():
                                val = eval(var_code, the_user_dict)
                                if isinstance(val, float) and float_formatter is not None:
                                    result['field_data'][varname] = float_formatter % val
                                else:
                                    result['field_data'][varname] = val
                        if 'code dict' in attachment['options']:
                            for varname, var_code in attachment['options']['code dict'].items():
                                val = eval(var_code, the_user_dict)
                                if isinstance(val, float) and float_formatter is not None:
                                    result['field_data'][varname] = float_formatter % val
                                elif isinstance(val, RawValue):
                                    result['field_data'][varname] = val.value
                                else:
                                    result['field_data'][varname] = docassemble.base.file_docx.transform_for_docx(val, self, result['template'])
                        docassemble.base.functions.reset_context()
                elif doc_format == 'pdf' and 'fields' in attachment['options'] and 'pdf_template_file' in attachment['options']:
                    docassemble.base.functions.set_context('pdf')
                    result['data_strings'] = []
                    result['images'] = []
                    if isinstance(attachment['options']['fields'], dict):
                        the_fields = [attachment['options']['fields']]
                    else:
                        the_fields = attachment['options']['fields']
                    if 'checkbox_export_value' in attachment['options']:
                        yes_value = attachment['options']['checkbox_export_value'].text(the_user_dict).strip()
                    else:
                        yes_value = 'Yes'
                    docassemble.base.functions.this_thread.misc['checkbox_export_value'] = yes_value
                    for item in the_fields:
                        for key, val in item.items():
                            answer = val.text(the_user_dict).rstrip()
                            if answer == 'True':
                                answer = yes_value
                            elif answer == 'False':
                                answer = 'No'
                            elif answer == 'None':
                                answer = ''
                            answer = re.sub(r'\[(NEWLINE|BR)\]', r'\n', answer)
                            answer = re.sub(r'\[(BORDER|NOINDENT|FLUSHLEFT|FLUSHRIGHT|BOLDCENTER|CENTER)\]', r'', answer)
                            #logmessage("Found a " + str(key) + " with a |" + str(answer) + '|')
                            m = re.search(r'\[FILE ([^\]]+)\]', answer)
                            if m:
                                file_reference = re.sub(r'[ ,].*', '', m.group(1))
                                file_info = docassemble.base.functions.server.file_finder(file_reference, convert={'svg': 'png'})
                                result['images'].append((key, file_info))
                            else:
                                result['data_strings'].append((key, answer))
                    if 'code' in attachment['options']:
                        additional_fields = eval(attachment['options']['code'], the_user_dict)
                        if not isinstance(additional_fields, list):
                            additional_fields = [additional_fields]
                        for item in additional_fields:
                            if not isinstance(item, dict):
                                raise DAError("code in an attachment returned something other than a dictionary or a list of dictionaries")
                            for key, val in item.items():
                                if val is True:
                                    val = yes_value
                                elif val is False:
                                    val = 'No'
                                elif val is None:
                                    val = ''
                                elif isinstance(val, float) and float_formatter is not None:
                                    val = float_formatter % val
                                else:
                                    val = text_type(val)
                                val = re.sub(r'\s*\[(NEWLINE|BR)\]\s*', r'\n', val)
                                val = re.sub(r'\s*\[(BORDER|NOINDENT|FLUSHLEFT|FLUSHRIGHT|BOLDCENTER|CENTER)\]\s*', r'', val)
                                m = re.search(r'\[FILE ([^\]]+)\]', val)
                                if m:
                                    file_reference = re.sub(r'[ ,].*', '', m.group(1))
                                    file_info = docassemble.base.functions.server.file_finder(file_reference, convert={'svg': 'png'})
                                    result['images'].append((key, file_info))
                                else:
                                    result['data_strings'].append((key, val))
                    if 'code dict' in attachment['options']:
                        additional_fields = attachment['options']['code dict']
                        if not isinstance(additional_fields, list):
                            additional_fields = [additional_fields]
                        for item in additional_fields:
                            if not isinstance(item, dict):
                                raise DAError("code dict in an attachment returned something other than a dictionary or a list of dictionaries")
                            for key, var_code in item.items():
                                val = eval(var_code, the_user_dict)
                                if val is True:
                                    val = yes_value
                                elif val is False:
                                    val = 'No'
                                elif val is None:
                                    val = ''
                                elif isinstance(val, float) and float_formatter is not None:
                                    val = float_formatter % val
                                else:
                                    val = text_type(val)
                                val = re.sub(r'\[(NEWLINE|BR)\]', r'\n', val)
                                val = re.sub(r'\[(BORDER|NOINDENT|FLUSHLEFT|FLUSHRIGHT|BOLDCENTER|CENTER)\]', r'', val)
                                m = re.search(r'\[FILE ([^\]]+)\]', val)
                                if m:
                                    file_reference = re.sub(r'[ ,].*', '', m.group(1))
                                    file_info = docassemble.base.functions.server.file_finder(file_reference, convert={'svg': 'png'})
                                    result['images'].append((key, file_info))
                                else:
                                    result['data_strings'].append((key, val))
                    if 'raw code dict' in attachment['options']:
                        additional_fields = attachment['options']['raw code dict']
                        if not isinstance(additional_fields, list):
                            additional_fields = [additional_fields]
                        for item in additional_fields:
                            if not isinstance(item, dict):
                                raise DAError("raw code dict in an attachment returned something other than a dictionary or a list of dictionaries")
                            for key, var_code in item.items():
                                val = eval(var_code, the_user_dict)
                                if val is True:
                                    val = yes_value
                                elif val is False:
                                    val = 'No'
                                elif isinstance(val, float) and float_formatter is not None:
                                    val = float_formatter % val
                                elif val is None:
                                    val = ''
                                val = re.sub(r'\[(NEWLINE|BR)\]', r'\n', val)
                                val = re.sub(r'\[(BORDER|NOINDENT|FLUSHLEFT|FLUSHRIGHT|BOLDCENTER|CENTER)\]', r'', val)
                                m = re.search(r'\[FILE ([^\]]+)\]', val)
                                if m:
                                    file_reference = re.sub(r'[ ,].*', '', m.group(1))
                                    file_info = docassemble.base.functions.server.file_finder(file_reference, convert={'svg': 'png'})
                                    result['images'].append((key, file_info))
                                else:
                                    result['data_strings'].append((key, val))
                    docassemble.base.functions.reset_context()
                else:
                    the_markdown = u""
                    if len(result['metadata']):
                        modified_metadata = dict()
                        for key, data in result['metadata'].items():
                            if re.search(r'Footer|Header', key) and 'Lines' not in key:
                                #modified_metadata[key] = docassemble.base.filter.metadata_filter(data, doc_format) + text_type('[END]')
                                modified_metadata[key] = data + text_type('[END]')
                            else:
                                modified_metadata[key] = data
                        if PY3:
                            the_markdown += u'---\n' + codecs.decode(bytearray(yaml.safe_dump(modified_metadata, default_flow_style=False, default_style = '|', allow_unicode=False), encoding='utf-8'), 'utf-8') + u"...\n"
                        else:
                            the_markdown += u'---\n' + codecs.decode(yaml.safe_dump(modified_metadata, default_flow_style=False, default_style = '|', allow_unicode=False), 'utf-8') + u"...\n"
                    the_markdown += attachment['content'].text(the_user_dict)
                    #logmessage("Markdown is:\n" + repr(the_markdown) + "END")
                    if emoji_match.search(the_markdown) and len(self.interview.images) > 0:
                        the_markdown = emoji_match.sub(emoji_matcher_insert(self), the_markdown)
                    result['markdown'][doc_format] = the_markdown
            elif doc_format in ['html']:
                result['markdown'][doc_format] = attachment['content'].text(the_user_dict)
                if emoji_match.search(result['markdown'][doc_format]) and len(self.interview.images) > 0:
                    result['markdown'][doc_format] = emoji_match.sub(emoji_matcher_html(self), result['markdown'][doc_format])
                #logmessage("output was:\n" + repr(result['content'][doc_format]))
        if old_language is not None:
            docassemble.base.functions.set_language(old_language)
        return(result)

def emoji_matcher_insert(obj):
    return (lambda x: docassemble.base.filter.emoji_insert(x.group(1), images=obj.interview.images))

def emoji_matcher_html(obj):
    return (lambda x: docassemble.base.filter.emoji_html(x.group(1), images=obj.interview.images))

def interview_source_from_string(path, **kwargs):
    if path is None:
        raise DAError("Passed None to interview_source_from_string")
    if re.search(r'^https*://', path):
        new_source = InterviewSourceURL(path=path)
        if new_source.update():
            return new_source
    context_interview = kwargs.get('context_interview', None)
    if context_interview is not None:
        new_source = context_interview.source.append(path)
        if new_source is not None:
            return new_source
    #sys.stderr.write("Trying to find it\n")
    for the_filename in [docassemble.base.functions.package_question_filename(path), docassemble.base.functions.standard_question_filename(path), docassemble.base.functions.server.absolute_filename(path)]:
        #sys.stderr.write("Trying " + str(the_filename) + " with path " + str(path) + "\n")
        if the_filename is not None:
            new_source = InterviewSourceFile(filepath=the_filename, path=path)
            if new_source.update():
                return(new_source)
    raise DAError("YAML file " + str(path) + " not found", code=404)

def is_boolean(field_data):
    if 'choices' not in field_data:
        return False
    if 'has_code' in field_data:
        return False
    for entry in field_data['choices']:
        if 'key' in entry and 'label' in entry:
            if not isinstance(entry['key'].original_text, bool):
                return False
    return True

def is_threestate(field_data):
    if 'choices' not in field_data:
        return False
    if 'has_code' in field_data:
        return False
    for entry in field_data['choices']:
        if 'key' in entry and 'label' in entry:
            if not isinstance(entry['key'].original_text, (bool, NoneType)):
                return False
    return True

class TableInfo(object):
    pass

class Interview:
    def __init__(self, **kwargs):
        self.source = None
        self.questions = dict()
        self.generic_questions = dict()
        self.questions_by_id = dict()
        self.questions_by_name = dict()
        self.questions_list = list()
        self.progress_points = set()
        self.ids_in_use = set()
        self.id_orderings = list()
        self.orderings = list()
        self.orderings_by_question = dict()
        self.images = dict()
        self.metadata = list()
        self.helptext = dict()
        self.defs = dict()
        self.terms = dict()
        self.mlfields = dict()
        self.autoterms = dict()
        self.includes = set()
        self.reconsider = set()
        self.reconsider_generic = dict()
        self.question_index = 0
        self.default_role = None
        self.default_validation_messages = dict()
        self.default_screen_parts = dict()
        self.title = None
        self.debug = get_config('debug', True)
        self.use_progress_bar = False
        self.question_back_button = False
        self.question_help_button = False
        self.navigation_back_button = True
        self.force_fullscreen = False
        self.use_pdf_a = get_config('pdf/a', False)
        self.use_tagged_pdf = get_config('tagged pdf', False)
        self.loop_limit = get_config('loop limit', 500)
        self.recursion_limit = get_config('recursion limit', 500)
        self.cache_documents = True
        self.use_navigation = False
        self.flush_left = False
        self.max_image_size = get_config('maximum image size', None)
        self.bootstrap_theme = get_config('bootstrap theme', None)
        self.sections = dict()
        self.names_used = set()
        self.attachment_options = dict()
        self.attachment_index = 0
        self.external_files = dict()
        self.options = dict()
        self.calls_process_action = False
        self.uses_action = False
        self.imports_util = False
        self.table_width = 65
        self.success = True
        self.scan_for_emojis = False
        self.consolidated_metadata = dict()
        if 'source' in kwargs:
            self.read_from(kwargs['source'])
    def ordered(self, the_list):
        if len(the_list) <= 1:
            return the_list
    def get_ml_store(self):
        if hasattr(self, 'ml_store'):
            return self.ml_store
        else:
            return self.standard_ml_store()
    def set_ml_store(self, ml_store):
        self.ml_store = ml_store
    def standard_ml_store(self):
        if self.source is None:
            ml_store = None
        else:
            ml_store = self.source.get_package()
        if ml_store is None:
            ml_store = ''
        else:
            ml_store += ':data/sources/'
        if self.source and self.source.path is not None:
            ml_store += 'ml-' + re.sub(r'\..*', '', re.sub(r'.*[/:]', '', self.source.path)) + '.json'
        else:
            ml_store += 'ml-default.json'
        return ml_store
    def get_bootstrap_theme(self):
        if self.bootstrap_theme is None:
            return None
        result = docassemble.base.functions.server.url_finder(self.bootstrap_theme, _package=self.source.package)
        return result
    def get_tags(self, the_user_dict):
        if 'tags' in the_user_dict['_internal']:
            return the_user_dict['_internal']['tags']
        else:
            tags = set()
            for metadata in self.metadata:
                if 'tags' in metadata and isinstance(metadata['tags'], list):
                    for tag in metadata['tags']:
                        tags.add(tag)
            return tags
    def get_title(self, the_user_dict, status=None, converter=None):
        if converter is None:
            converter = lambda y: y
        mapping = (('title', 'full'), ('logo', 'logo'), ('short title', 'short'), ('tab title', 'tab'), ('subtitle', 'sub'), ('exit link', 'exit link'), ('exit label', 'exit label'), ('submit', 'submit'), ('pre', 'pre'), ('post', 'post'), ('continue button label', 'continue button label'), ('resume button label', 'resume button label'), ('under', 'under'), ('right', 'right'), ('logo', 'logo'))
        title = dict()
        for title_name, title_abb in mapping:
            if '_internal' in the_user_dict and title_name in the_user_dict['_internal'] and the_user_dict['_internal'][title_name] is not None:
                title[title_abb] = text_type(the_user_dict['_internal'][title_name]).strip()
            elif status is not None and (title_name + ' text') in status.extras and status.extras[title_name + ' text'] is not None:
                if title_name == 'exit link':
                    title[title_abb] = status.extras[title_name + ' text']
                else:
                    title[title_abb] = converter(status.extras[title_name + ' text'], title_name)
                the_user_dict['_internal'][title_name + ' default'] = title[title_abb]
            elif status is None and (title_name + ' default') in the_user_dict['_internal'] and the_user_dict['_internal'][title_name + ' default'] is not None:
                title[title_abb] = the_user_dict['_internal'][title_name + ' default']
        if status is not None:
            base_lang = status.question.language
        else:
            base_lang = get_language()
        if base_lang in self.default_title:
            for key, val in self.default_title[base_lang].items():
                if key not in title:
                    title[key] = val
        if '*' in self.default_title:
            for key, val in self.default_title['*'].items():
                if key not in title:
                    title[key] = val
        return title
    def allowed_to_access(self, is_anonymous=False, has_roles=None):
        roles = set()
        for metadata in self.metadata:
            if 'required privileges' in metadata:
                roles = set()
                privs = metadata['required privileges']
                if isinstance(privs, list) or (hasattr(privs, 'instanceName') and hasattr(privs, 'elements') and isinstance(privs.elements, list)):
                    for priv in privs:
                        roles.add(priv)
                elif isinstance(privs, string_types):
                    roles.add(privs)
        if len(roles):
            if is_anonymous:
                if 'anonymous' in roles:
                    return True
                return False
            if has_roles is not None:
                return len(set(roles).intersection(set(has_roles))) > 0
        return True

    def is_unlisted(self):
        unlisted = False
        for metadata in self.metadata:
            if 'unlisted' in metadata:
                unlisted = metadata['unlisted']
        return unlisted
    def next_attachment_number(self):
        self.attachment_index += 1
        return(self.attachment_index - 1)
    def next_number(self):
        self.question_index += 1
        return(self.question_index - 1)
    def read_from(self, source):
        if self.source is None:
            self.source = source
            #self.firstPath = source.path
            #self.rootDirectory = source.directory
        if hasattr(source, 'package') and source.package:
            source_package = source.package
            if source_package.startswith('docassemble.playground'):
                self.debug = True
        else:
            source_package = None
        if hasattr(source, 'path'):
            if source.path in self.includes:
                logmessage("Interview: source " + text_type(source.path) + " has already been included.  Skipping.")
                return
            self.includes.add(source.path)
        #for document in yaml.safe_load_all(source.content):
        for source_code in document_match.split(source.content):
            source_code = remove_trailing_dots.sub('', source_code)
            source_code = fix_tabs.sub('  ', source_code)
            if source.testing:
                try:
                    #logmessage("Package is " + str(source_package))
                    document = yaml.safe_load(source_code)
                    if document is not None:
                        question = Question(document, self, source=source, package=source_package, source_code=source_code)
                        self.names_used.update(question.fields_used)
                except Exception as errMess:
                    #sys.stderr.write(text_type(source_code) + "\n")
                    try:
                        logmessage('Interview: error reading YAML file ' + text_type(source.path) + '\n\nDocument source code was:\n\n---\n' + text_type(source_code) + '---\n\nError was:\n\n' + text_type(errMess))
                    except:
                        try:
                            logmessage('Interview: error reading YAML file ' + text_type(source.path) + '. Error was:\n\n' + text_type(errMess))
                        except:
                            if isinstance(errMess, yaml.error.MarkedYAMLError):
                                logmessage('Interview: error reading YAML file ' + text_type(source.path) + '. Error type was:\n\n' + errMess.problem)
                            else:
                                logmessage('Interview: error reading YAML file ' + text_type(source.path) + '. Error type was:\n\n' + errMess.__class__.__name__)
                    self.success = False
                    pass
            else:
                try:
                    document = yaml.safe_load(source_code)
                except Exception as errMess:
                    self.success = False
                    #sys.stderr.write("Error: " + text_type(source_code) + "\n")
                    #text_type(source_code)
                    try:
                        raise DAError('Error reading YAML file ' + text_type(source.path) + '\n\nDocument source code was:\n\n---\n' + text_type(source_code) + '---\n\nError was:\n\n' + text_type(errMess))
                    except:
                        raise DAError('Error reading YAML file ' + text_type(source.path) + '\n\nDocument source code was:\n\n---\n' + text_type(source_code) + '---\n\nError was:\n\n' + text_type(errMess.__class__.__name__))
                if document is not None:
                    try:
                        question = Question(document, self, source=source, package=source_package, source_code=source_code)
                        self.names_used.update(question.fields_used)
                    except SyntaxException as qError:
                        self.success = False
                        raise Exception("Syntax Exception: " + text_type(qError) + "\n\nIn file " + text_type(source.path) + " from package " + text_type(source_package) + ":\n" + text_type(source_code))
                    except CompileException as qError:
                        self.success = False
                        raise Exception("Compile Exception: " + text_type(qError) + "\n\nIn file " + text_type(source.path) + " from package " + text_type(source_package) + ":\n" + text_type(source_code))
                    except SyntaxError as qError:
                        self.success = False
                        raise Exception("Syntax Error: " + text_type(qError) + "\n\nIn file " + text_type(source.path) + " from package " + text_type(source_package) + ":\n" + text_type(source_code))
        for ordering in self.id_orderings:
            if ordering['type'] == 'supersedes':
                new_list = [ordering['question'].number]
                for question_id in ordering['supersedes']:
                    if question_id in self.questions_by_id:
                        new_list.append(self.questions_by_id[question_id].number)
                    else:
                        logmessage("warning: reference in a supersedes directive to an id " + question_id + " that does not exist in interview")
            elif ordering['type'] == 'order':
                new_list = list()
                for question_id in ordering['order']:
                    if question_id in self.questions_by_id:
                        new_list.append(self.questions_by_id[question_id].number)
                    else:
                        logmessage("warning: reference in an order directive to id " + question_id + " that does not exist in interview")
            self.orderings.append(new_list)
        for ordering in self.orderings:
            for question_a in ordering:
                mode = 1
                for question_b in ordering:
                    if question_a == question_b:
                        mode = -1
                        continue
                    if question_b not in self.orderings_by_question:
                        self.orderings_by_question[question_b] = dict()
                    self.orderings_by_question[question_b][question_a] = mode
        #logmessage(repr(self.orderings_by_question))
        self.sorter = self.make_sorter()
        if len(self.images) > 0 or get_config('default icons', 'font awesome') in ('material icons', 'font awesome'):
            self.scan_for_emojis = True
        for metadata in self.metadata:
            for key, val in metadata.items():
                self.consolidated_metadata[key] = val
        mapping = (('title', 'full'), ('logo', 'logo'), ('short title', 'short'), ('tab title', 'tab'), ('subtitle', 'sub'), ('exit link', 'exit link'), ('exit label', 'exit label'), ('submit', 'submit'), ('pre', 'pre'), ('post', 'post'), ('help label', 'help label'), ('continue button label', 'continue button label'), ('resume button label', 'resume button label'), ('back button label', 'back button label'), ('right', 'right'), ('under', 'under'), ('submit', 'submit'))
        self.default_title = {'*': dict()}
        for metadata in self.metadata:
            for title_name, title_abb in mapping:
                if metadata.get(title_name, None) is not None:
                    if isinstance(metadata[title_name], dict):
                        for lang, val in metadata[title_name].items():
                            if lang not in self.default_title:
                                self.default_title[lang] = dict()
                            self.default_title[lang][title_abb] = text_type(val).strip()
                    else:
                        self.default_title['*'][title_abb] = text_type(metadata[title_name]).strip()
        for lang, parts in docassemble.base.functions.server.main_page_parts.items():
            if lang not in self.default_title:
                self.default_title[lang] = dict()
            for title_name, title_abb in mapping:
                if title_abb in self.default_title[lang]:
                    continue
                if parts.get('main page ' + title_name, '') != '':
                    self.default_title[lang][title_abb] = parts['main page ' + title_name]
    def make_sorter(self):
        lookup_dict = self.orderings_by_question
        class K(object):
            def __init__(self, obj, *args):
                self.obj = obj.number
                self.lookup = lookup_dict
            def __lt__(self, other):
                if self.obj == other.obj:
                    return False
                if self.obj in self.lookup and other.obj in self.lookup[self.obj] and self.lookup[self.obj][other.obj] == -1:
                    return True
                return False
            def __gt__(self, other):
                if self.obj == other.obj:
                    return False
                if self.obj in self.lookup and other.obj in self.lookup[self.obj] and self.lookup[self.obj][other.obj] == 1:
                    return True
                return False
            def __eq__(self, other):
                if self.obj == other.obj or self.obj not in self.lookup or other.obj not in self.lookup:
                    return True
                return False
            def __le__(self, other):
                if self.obj == other.obj or self.obj not in self.lookup or other.obj not in self.lookup:
                    return True
                if self.lookup[self.obj][other.obj] == -1:
                    return True
                return False
            def __ge__(self, other):
                if self.obj == other.obj or self.obj not in self.lookup or other.obj not in self.lookup:
                    return True
                if self.lookup[self.obj][other.obj] == 1:
                    return True
                return False
            def __ne__(self, other):
                if self.obj == other.obj or self.obj not in self.lookup or other.obj not in self.lookup:
                    return False
                return True
        return K
    def sort_with_orderings(self, the_list):
        if len(the_list) <= 1:
            return the_list
        result = sorted(the_list, key=self.sorter)
        # logmessage(repr([y for y in reversed([x.number for x in result])]))
        return reversed(result)
    def processed_helptext(self, the_user_dict, language):
        result = list()
        if language in self.helptext:
            for source in self.helptext[language]:
                help_item = dict()
                help_item['from'] = source['from']
                if source['label'] is None:
                    help_item['label'] = None
                else:
                    help_item['label'] = source['label'].text(the_user_dict)
                if source['heading'] is None:
                    help_item['heading'] = None
                else:
                    help_item['heading'] = source['heading'].text(the_user_dict)
                if source['audiovideo'] is None:
                    help_item['audiovideo'] = None
                else:
                    help_item['audiovideo'] = process_audio_video_list(source['audiovideo'], the_user_dict)
                help_item['content'] = source['content'].text(the_user_dict)
                result.append(help_item)
        return result
    def assemble(self, user_dict, interview_status=None, old_user_dict=None):
        #sys.stderr.write("assemble\n")
        user_dict['_internal']['tracker'] += 1
        if interview_status is None:
            interview_status = InterviewStatus()
        if 'docvar' not in user_dict['_internal']: # waste of CPU cycles; eventually take out!
            user_dict['_internal']['docvar'] = dict()
        if 'doc_cache' not in user_dict['_internal']: # waste of CPU cycles; eventually take out!
            user_dict['_internal']['doc_cache'] = dict()
        if interview_status.current_info['url'] is not None:
            user_dict['_internal']['url'] = interview_status.current_info['url']
        interview_status.set_tracker(user_dict['_internal']['tracker'])
        #docassemble.base.functions.reset_local_variables()
        interview_status.current_info.update({'default_role': self.default_role})
        docassemble.base.functions.this_thread.current_package = self.source.package
        docassemble.base.functions.this_thread.current_info = interview_status.current_info
        docassemble.base.functions.this_thread.interview = self
        docassemble.base.functions.this_thread.interview_status = interview_status
        docassemble.base.functions.this_thread.internal = user_dict['_internal']
        if user_dict['nav'].sections is None:
            user_dict['nav'].sections = self.sections
            if hasattr(self, 'sections_progressive'):
                user_dict['nav'].progressive = self.sections_progressive
        for question in self.questions_list:
            if question.question_type == 'imports':
                for module_name in question.module_list:
                    if module_name.startswith('.'):
                        exec('import ' + str(self.source.package) + module_name, user_dict)
                    else:
                        exec('import ' + module_name, user_dict)
            if question.question_type == 'modules':
                for module_name in question.module_list:
                    if module_name.startswith('.'):
                        exec('from ' + str(self.source.package) + module_name + ' import *', user_dict)
                    else:
                        exec('from ' + module_name + ' import *', user_dict)
            if question.question_type == 'reset': #, 'template', 'table'
                for var in question.reset_list:
                    if complications.search(var):
                        try:
                            exec('del ' + str(var), user_dict)
                        except:
                            pass
                    elif var in user_dict:
                        del user_dict[var]
        if 'x' in user_dict and user_dict['x'].__class__.__name__ in self.reconsider_generic:
            for var in self.reconsider_generic[user_dict['x'].__class__.__name__]:
                try:
                    exec('del ' + str(var), user_dict)
                except:
                    pass
        for var in self.reconsider:
            if complications.search(var):
                try:
                    exec('del ' + str(var), user_dict)
                except:
                    pass
            elif var in user_dict:
                del user_dict[var]
        number_loops = 0
        variables_sought = set()
        try:
            while True:
                number_loops += 1
                if number_loops > self.loop_limit:
                    docassemble.base.functions.wrap_up(user_dict)
                    raise DAError("There appears to be a circularity.  Variables involved: " + ", ".join(variables_sought) + ".")
                docassemble.base.functions.reset_gathering_mode()
                if 'action' in interview_status.current_info:
                    #logmessage("assemble: there is an action in the current_info: " + repr(interview_status.current_info['action']))
                    if interview_status.current_info['action'] in ('_da_list_remove', '_da_list_add', '_da_list_complete'):
                        for the_key in ('list', 'item', 'items'):
                            if the_key in interview_status.current_info['arguments']:
                                interview_status.current_info['action_' + the_key] = eval(interview_status.current_info['arguments'][the_key], user_dict)
                    if interview_status.current_info['action'] in ('_da_dict_remove', '_da_dict_add', '_da_dict_complete'):
                        for the_key in ('dict', 'item', 'items'):
                            if the_key in interview_status.current_info['arguments']:
                                interview_status.current_info['action_' + the_key] = eval(interview_status.current_info['arguments'][the_key], user_dict)
                #else:
                #    logmessage("assemble: there is no action in the current_info")
                try:
                    if not self.imports_util:
                        if self.consolidated_metadata.get('suppress loading util', False):
                            exec(import_process_action, user_dict)
                        else:
                            exec(import_util, user_dict)
                    if not self.calls_process_action:
                        exec(run_process_action, user_dict)
                    for question in self.questions_list:
                        if question.question_type == 'code' and (question.is_initial or (question.initial_code is not None and eval(question.initial_code, user_dict))):
                            #logmessage("Running some initial code:\n\n" + question.sourcecode)
                            if self.debug:
                                interview_status.seeking.append({'question': question, 'reason': 'initial', 'time': time.time()})
                            docassemble.base.functions.this_thread.current_question = question
                            exec_with_trap(question, user_dict)
                            continue
                        if question.name and question.name in user_dict['_internal']['answered']:
                            #logmessage("Skipping " + question.name + " because answered")
                            continue
                        if question.question_type == "objects_from_file":
                            for keyvalue in question.objects_from_file:
                                for variable, the_file in keyvalue.items():
                                    exec(import_core, user_dict)
                                    command = variable + ' = docassemble.base.core.objects_from_file("' + str(the_file) + '", name=' + repr(variable) + ')'
                                    #logmessage("Running " + command)
                                    exec(command, user_dict)
                            question.mark_as_answered(user_dict)
                        if question.is_mandatory or (question.mandatory_code is not None and eval(question.mandatory_code, user_dict)):
                            if question.question_type == "data":
                                string = from_safeid(question.fields[0].saveas) + ' = ' + repr(recursive_eval_dataobject(question.fields[0].data, user_dict))
                                exec(string, user_dict)
                                question.mark_as_answered(user_dict)
                            if question.question_type == "data_from_code":
                                string = from_safeid(question.fields[0].saveas) + ' = ' + repr(recursive_eval_data_from_code(question.fields[0].data, user_dict))
                                exec(string, user_dict)
                                question.mark_as_answered(user_dict)
                            if question.question_type == "objects":
                                #logmessage("Going into objects")
                                for keyvalue in question.objects:
                                    for variable in keyvalue:
                                        object_type_name = keyvalue[variable]
                                        user_dict["__object_type"] = eval(object_type_name, user_dict)
                                        if False and re.search(r"\.", variable):
                                            m = re.search(r"(.*)\.(.*)", variable)
                                            variable = m.group(1)
                                            attribute = m.group(2)
                                            command = variable + ".initializeAttribute(" + repr(attribute) + ", __object_type)"
                                            #command = variable + "." + attribute + " = " + object_type + "()"
                                            #logmessage("Running " + command)
                                            exec(command, user_dict)
                                        else:
                                            if user_dict["__object_type"].__class__.__name__ == 'DAObjectPlusParameters':
                                                command = variable + ' = __object_type.object_type(' + repr(variable) + ', **__object_type.parameters)'
                                            else:
                                                command = variable + ' = __object_type(' + repr(variable) + ')'
                                            # command = variable + ' = ' + object_type + '(' + repr(variable) + ')'
                                            #logmessage("Running " + command)
                                            exec(command, user_dict)
                                        if "__object_type" in user_dict:
                                            del user_dict["__object_type"]
                                question.mark_as_answered(user_dict)
                            if question.question_type == 'code':
                                if self.debug:
                                    interview_status.seeking.append({'question': question, 'reason': 'mandatory code', 'time': time.time()})
                                #logmessage("Running some code:\n\n" + question.sourcecode)
                                #logmessage("Question name is " + question.name)
                                docassemble.base.functions.this_thread.current_question = question
                                exec_with_trap(question, user_dict)
                                #logmessage("Code completed")
                                if question.name:
                                    user_dict['_internal']['answered'].add(question.name)
                                    #logmessage("Question " + str(question.name) + " marked as answered")
                            elif hasattr(question, 'content') and question.name:
                                if self.debug:
                                    interview_status.seeking.append({'question': question, 'reason': 'mandatory question', 'time': time.time()})
                                if question.name and question.name in user_dict['_internal']['answers']:
                                    the_question = question.follow_multiple_choice(user_dict, interview_status, False, 'None', [])
                                    if the_question.question_type in ["code", "event_code"]:
                                        docassemble.base.functions.this_thread.current_question = the_question
                                        exec_with_trap(the_question, user_dict)
                                        interview_status.mark_tentative_as_answered(user_dict)
                                        continue
                                    elif hasattr(the_question, 'content'):
                                        interview_status.populate(the_question.ask(user_dict, old_user_dict, 'None', [], None, None))
                                        interview_status.mark_tentative_as_answered(user_dict)
                                    else:
                                        raise DAError("An embedded question can only be a code block or a regular question block.  The question type was " + getattr(the_question, 'question_type', 'unknown'))
                                else:
                                    interview_status.populate(question.ask(user_dict, old_user_dict, 'None', [], None, None))
                                if interview_status.question.question_type == 'continue':
                                    user_dict['_internal']['answered'].add(question.name)
                                else:
                                    raise MandatoryQuestion()
                except ForcedReRun as the_exception:
                    continue
                except (NameError, DAAttributeError, DAIndexError) as the_exception:
                    if 'pending_error' in docassemble.base.functions.this_thread.misc:
                        del docassemble.base.functions.this_thread.misc['pending_error']
                    #logmessage("Error in " + the_exception.__class__.__name__ + " is " + str(the_exception))
                    if self.debug and docassemble.base.functions.this_thread.evaluation_context is not None:
                        logmessage("NameError exception during document assembly: " + text_type(the_exception))
                    docassemble.base.functions.reset_context()
                    seeking_question = False
                    if isinstance(the_exception, ForcedNameError):
                        #logmessage("assemble: got a ForcedNameError for " + text_type(the_exception.name))
                        follow_mc = False
                        seeking_question = True
                        #logmessage("next action is " + repr(the_exception.next_action))
                        if the_exception.next_action is not None and not interview_status.checkin:
                            if 'event_stack' not in user_dict['_internal']:
                                user_dict['_internal']['event_stack'] = dict()
                            session_uid = interview_status.current_info['user']['session_uid']
                            if session_uid not in user_dict['_internal']['event_stack']:
                                user_dict['_internal']['event_stack'][session_uid] = list()
                            new_items = list()
                            for new_item in the_exception.next_action:
                                already_there = False
                                for event_item in user_dict['_internal']['event_stack'][session_uid]:
                                    if event_item['action'] == new_item:
                                        already_there = True
                                        break
                                if not already_there:
                                    new_items.append(new_item)
                            if len(new_items):
                                #logmessage("adding a new item to event_stack: " + repr(new_items))
                                user_dict['_internal']['event_stack'][session_uid] = new_items + user_dict['_internal']['event_stack'][session_uid]
                            #interview_status.next_action.extend(the_exception.next_action)
                            if the_exception.name.startswith('_da_'):
                                continue
                        if the_exception.arguments is not None:
                            docassemble.base.functions.this_thread.current_info.update(dict(action=the_exception.name, arguments=the_exception.arguments))
                        missingVariable = the_exception.name
                    else:
                        follow_mc = True
                        missingVariable = extract_missing_name(the_exception)
                    variables_sought.add(missingVariable)
                    question_result = self.askfor(missingVariable, user_dict, old_user_dict, interview_status, seeking=interview_status.seeking, follow_mc=follow_mc, seeking_question=seeking_question)
                    if question_result['type'] == 'continue':
                        continue
                    elif question_result['type'] == 'refresh':
                        pass
                    else:
                        interview_status.populate(question_result)
                        break
                except UndefinedError as the_exception:
                    #logmessage("UndefinedError")
                    if self.debug and docassemble.base.functions.this_thread.evaluation_context is not None:
                        logmessage(the_exception.__class__.__name__ + " exception during document assembly: " + text_type(the_exception) + "\n" + traceback.format_exc())
                    docassemble.base.functions.reset_context()
                    missingVariable = extract_missing_name(the_exception)
                    #logmessage("extracted " + missingVariable)
                    variables_sought.add(missingVariable)
                    question_result = self.askfor(missingVariable, user_dict, old_user_dict, interview_status, seeking=interview_status.seeking, follow_mc=True)
                    if question_result['type'] == 'continue':
                        continue
                    elif question_result['type'] == 'refresh':
                        pass
                    else:
                        interview_status.populate(question_result)
                        break
                except CommandError as qError:
                    #logmessage("CommandError")
                    docassemble.base.functions.reset_context()
                    question_data = dict(command=qError.return_type, url=qError.url)
                    new_interview_source = InterviewSourceString(content='')
                    new_interview = new_interview_source.get_interview()
                    reproduce_basics(self, new_interview)
                    new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                    new_question.name = "Question_Temp"
                    interview_status.populate(new_question.ask(user_dict, old_user_dict, 'None', [], None, None))
                    break
                except ResponseError as qError:
                    docassemble.base.functions.reset_context()
                    #logmessage("Trapped ResponseError")
                    question_data = dict(extras=dict())
                    if hasattr(qError, 'response') and qError.response is not None:
                        question_data['response'] = qError.response
                    elif hasattr(qError, 'binaryresponse') and qError.binaryresponse is not None:
                        question_data['binaryresponse'] = qError.binaryresponse
                    elif hasattr(qError, 'filename') and qError.filename is not None:
                        question_data['response filename'] = qError.filename
                    elif hasattr(qError, 'url') and qError.url is not None:
                        question_data['redirect url'] = qError.url
                    elif hasattr(qError, 'all_variables') and qError.all_variables:
                        if hasattr(qError, 'include_internal'):
                            question_data['include_internal'] = qError.include_internal
                        question_data['content type'] = 'application/json'
                        question_data['all_variables'] = True
                    elif hasattr(qError, 'nullresponse') and qError.nullresponse:
                        question_data['null response'] = qError.nullresponse
                    if hasattr(qError, 'content_type') and qError.content_type:
                        question_data['content type'] = qError.content_type
                    # new_interview = copy.deepcopy(self)
                    # if self.source is None:
                    #     new_interview_source = InterviewSourceString(content='')
                    # else:
                    #     new_interview_source = self.source
                    new_interview_source = InterviewSourceString(content='')
                    new_interview = new_interview_source.get_interview()
                    reproduce_basics(self, new_interview)
                    new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                    new_question.name = "Question_Temp"
                    #the_question = new_question.follow_multiple_choice(user_dict)
                    interview_status.populate(new_question.ask(user_dict, old_user_dict, 'None', [], None, None))
                    break
                except BackgroundResponseError as qError:
                    docassemble.base.functions.reset_context()
                    #logmessage("Trapped BackgroundResponseError")
                    question_data = dict(extras=dict())
                    if hasattr(qError, 'backgroundresponse'):
                        question_data['backgroundresponse'] = qError.backgroundresponse
                    new_interview_source = InterviewSourceString(content='')
                    new_interview = new_interview_source.get_interview()
                    reproduce_basics(self, new_interview)
                    new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                    new_question.name = "Question_Temp"
                    interview_status.populate(new_question.ask(user_dict, old_user_dict, 'None', [], None, None))
                    break
                except BackgroundResponseActionError as qError:
                    docassemble.base.functions.reset_context()
                    #logmessage("Trapped BackgroundResponseActionError")
                    question_data = dict(extras=dict())
                    if hasattr(qError, 'action'):
                        question_data['action'] = qError.action
                    new_interview_source = InterviewSourceString(content='')
                    new_interview = new_interview_source.get_interview()
                    reproduce_basics(self, new_interview)
                    new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                    new_question.name = "Question_Temp"
                    interview_status.populate(new_question.ask(user_dict, old_user_dict, 'None', [], None, None))
                    break
                # except SendFileError as qError:
                #     #logmessage("Trapped SendFileError")
                #     question_data = dict(extras=dict())
                #     if hasattr(qError, 'filename') and qError.filename is not None:
                #         question_data['response filename'] = qError.filename
                #     if hasattr(qError, 'content_type') and qError.content_type:
                #         question_data['content type'] = qError.content_type
                #     new_interview_source = InterviewSourceString(content='')
                #     new_interview = new_interview_source.get_interview()
                #     new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                #     new_question.name = "Question_Temp"
                #     interview_status.populate(new_question.ask(user_dict, old_user_dict, 'None', [], None))
                #     break
                except QuestionError as qError:
                    #logmessage("QuestionError")
                    docassemble.base.functions.reset_context()
                    question_data = dict()
                    if qError.question:
                        question_data['question'] = qError.question
                    if qError.subquestion:
                        question_data['subquestion'] = qError.subquestion
                    if qError.dead_end:
                        pass
                    elif qError.buttons:
                        question_data['buttons'] = qError.buttons
                    else:
                        buttons = list()
                        if qError.show_exit is not False and not (qError.show_leave is True and qError.show_exit is None):
                            exit_button = {word('Exit'): 'exit'}
                            if qError.url:
                                exit_button.update(dict(url=qError.url))
                            buttons.append(exit_button)
                        if qError.show_leave:
                            leave_button = {word('Leave'): 'leave'}
                            if qError.url:
                                leave_button.update(dict(url=qError.url))
                            buttons.append(leave_button)
                        if qError.show_restart is not False:
                            buttons.append({word('Restart'): 'restart'})
                        if len(buttons):
                            question_data['buttons'] = buttons
                    new_interview_source = InterviewSourceString(content='')
                    new_interview = new_interview_source.get_interview()
                    reproduce_basics(self, new_interview)
                    new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                    new_question.name = "Question_Temp"
                    # will this be a problem?  Maybe, since the question name can vary by thread.
                    #the_question = new_question.follow_multiple_choice(user_dict)
                    interview_status.populate(new_question.ask(user_dict, old_user_dict, 'None', [], None, None))
                    break
                except AttributeError as the_error:
                    #logmessage("Regular attributeerror")
                    docassemble.base.functions.reset_context()
                    #logmessage(str(the_error.args))
                    docassemble.base.functions.wrap_up(user_dict)
                    raise DAError('Got error ' + str(the_error) + " " + traceback.format_exc() + "\nHistory was " + pprint.pformat(interview_status.seeking))
                except MandatoryQuestion:
                    #logmessage("MandatoryQuestion")
                    docassemble.base.functions.reset_context()
                    break
                except CodeExecute as code_error:
                    #logmessage("CodeExecute")
                    docassemble.base.functions.reset_context()
                    #if self.debug:
                    #    interview_status.seeking.append({'question': question, 'reason': 'mandatory code'})
                    exec(code_error.compute, user_dict)
                    code_error.question.mark_as_answered(user_dict)
                except SyntaxException as qError:
                    #logmessage("SyntaxException")
                    docassemble.base.functions.reset_context()
                    the_question = None
                    try:
                        the_question = question
                    except:
                        pass
                    docassemble.base.functions.wrap_up(user_dict)
                    if the_question is not None:
                        raise DAError(str(qError) + "\n\n" + str(self.idebug(self.data_for_debug)))
                    raise DAError("no question available: " + str(qError))
                except CompileException as qError:
                    #logmessage("CompileException")
                    docassemble.base.functions.reset_context()
                    the_question = None
                    try:
                        the_question = question
                    except:
                        pass
                    docassemble.base.functions.wrap_up(user_dict)
                    if the_question is not None:
                        raise DAError(str(qError) + "\n\n" + str(self.idebug(self.data_for_debug)))
                    raise DAError("no question available: " + str(qError))
                else:
                    docassemble.base.functions.wrap_up(user_dict)
                    raise DAErrorNoEndpoint('Docassemble has finished executing all code blocks marked as initial or mandatory, and finished asking all questions marked as mandatory (if any).  It is a best practice to end your interview with a question that says goodbye and offers an Exit button.')
        except Exception as the_error:
            #logmessage("Untrapped exception")
            if self.debug:
                the_error.interview = self
                the_error.interview_status = interview_status
                the_error.user_dict = docassemble.base.functions.serializable_dict(user_dict)
                if PY2 and not hasattr(the_error, 'traceback'):
                    the_error.traceback = the_error.__class__.__name__ + ': ' + traceback.format_exc()
                if PY3 and not hasattr(the_error, '__traceback__'):
                    cl, exc, tb = sys.exc_info()
                    the_error.__traceback__ = tb
                    del cl
                    del exc
                    del tb
            raise the_error
        if docassemble.base.functions.this_thread.prevent_going_back:
            interview_status.can_go_back = False
        docassemble.base.functions.wrap_up(user_dict)
        if self.debug:
            interview_status.seeking.append({'done': True, 'time': time.time()})
        #return(pickleable_objects(user_dict))
    def askfor(self, missingVariable, user_dict, old_user_dict, interview_status, **kwargs):
        seeking_question = kwargs.get('seeking_question', False)
        variable_stack = kwargs.get('variable_stack', set())
        questions_tried = kwargs.get('questions_tried', dict())
        recursion_depth = kwargs.get('recursion_depth', 0)
        recursion_depth += 1
        language = get_language()
        current_question = None
        follow_mc = kwargs.get('follow_mc', True)
        seeking = kwargs.get('seeking', list())
        if self.debug:
            seeking.append({'variable': missingVariable, 'time': time.time()})
        if recursion_depth > self.recursion_limit:
            raise DAError("There appears to be an infinite loop.  Variables in stack are " + ", ".join(sorted(variable_stack)) + ".")
        #logmessage("askfor: I don't have " + str(missingVariable) + " for language " + str(language))
        #sys.stderr.write("I don't have " + str(missingVariable) + " for language " + str(language) + "\n")
        origMissingVariable = missingVariable
        docassemble.base.functions.set_current_variable(origMissingVariable)
        # if missingVariable in variable_stack:
        #     raise DAError("Infinite loop: " + missingVariable + " already looked for, where stack is " + str(variable_stack))
        # variable_stack.add(missingVariable)
        found_generic = False
        realMissingVariable = missingVariable
        totry = list()
        variants = list()
        level_dict = dict()
        generic_dict = dict()
        expression_as_list = [x for x in match_brackets_or_dot.split(missingVariable) if x != '']
        expression_as_list.append('')
        recurse_indices(expression_as_list, list_of_indices, [], variants, level_dict, [], generic_dict, [])
        #logmessage(repr(variants))
        for variant in variants:
            totry.append({'real': missingVariable, 'vari': variant, 'iterators': level_dict[variant], 'generic': generic_dict[variant], 'is_generic': 0 if generic_dict[variant] == '' else 1, 'num_dots': variant.count('.'), 'num_iterators': variant.count('[')})
        totry = sorted(sorted(sorted(sorted(totry, key=lambda x: len(x['iterators'])), key=lambda x: x['num_iterators'], reverse=True), key=lambda x: x['num_dots'], reverse=True), key=lambda x: x['is_generic'])
        #logmessage("ask_for: totry is " + "\n".join([x['vari'] for x in totry]))
        questions_to_try = list()
        for mv in totry:
            realMissingVariable = mv['real']
            missingVariable = mv['vari']
            #logmessage("Trying missingVariable " + missingVariable + " and realMissingVariable " + realMissingVariable)
            if mv['is_generic']:
                #logmessage("Testing out generic " + mv['generic'])
                try:
                    root_evaluated = eval(mv['generic'], user_dict)
                    #logmessage("Root was evaluated")
                    classes_to_look_for = [type(root_evaluated).__name__]
                    for cl in type(root_evaluated).__bases__:
                        classes_to_look_for.append(cl.__name__)
                    for generic_object in classes_to_look_for:
                        #logmessage("Looking for generic object " + generic_object + " for " + missingVariable)
                        if generic_object in self.generic_questions and missingVariable in self.generic_questions[generic_object] and (language in self.generic_questions[generic_object][missingVariable] or '*' in self.generic_questions[generic_object][missingVariable]):
                            for lang in [language, '*']:
                                if lang in self.generic_questions[generic_object][missingVariable]:
                                    for the_question_to_use in self.sort_with_orderings(self.generic_questions[generic_object][missingVariable][lang]):
                                        questions_to_try.append((the_question_to_use, True, mv['generic'], mv['iterators'], missingVariable, generic_object))
                except:
                    pass
                continue
            # logmessage("askfor: questions to try is " + str(questions_to_try))
            if missingVariable in self.questions:
                for lang in [language, '*']:
                    # logmessage("lang is " + lang)
                    if lang in self.questions[missingVariable]:
                        for the_question in self.sort_with_orderings(self.questions[missingVariable][lang]):
                            questions_to_try.append((the_question, False, 'None', mv['iterators'], missingVariable, None))
        # logmessage("askfor: questions to try is " + str(questions_to_try))
        num_cycles = 0
        missing_var = "_unknown"
        while True:
            num_cycles += 1
            if num_cycles > self.loop_limit:
                raise DAError("Infinite loop detected while looking for " + missing_var)
            a_question_was_skipped = False
            docassemble.base.functions.reset_gathering_mode(origMissingVariable)
            #logmessage("Starting the while loop")
            try:
                for the_question, is_generic, the_x, iterators, missing_var, generic_object in questions_to_try:
                    #logmessage("In for loop with question " + the_question.name)
                    if missing_var in questions_tried and the_question in questions_tried[missing_var]:
                        a_question_was_skipped = True
                        # logmessage("Skipping question " + the_question.name)
                        continue
                    current_question = the_question
                    if self.debug:
                        seeking.append({'question': the_question, 'reason': 'considering', 'time': time.time()})
                    question = current_question
                    if len(question.condition) > 0:
                        if is_generic:
                            if the_x != 'None':
                                exec("x = " + the_x, user_dict)
                        if len(iterators):
                            for indexno in range(len(iterators)):
                                exec(list_of_indices[indexno] + " = " + iterators[indexno], user_dict)
                        condition_success = True
                        for condition in question.condition:
                            if not eval(condition, user_dict):
                                condition_success = False
                                break
                        if not condition_success:
                            continue
                    if follow_mc:
                        question = the_question.follow_multiple_choice(user_dict, interview_status, is_generic, the_x, iterators)
                    else:
                        question = the_question
                    if question is not current_question:
                        if len(question.condition) > 0:
                            if is_generic:
                                if the_x != 'None':
                                    exec("x = " + the_x, user_dict)
                            if len(iterators):
                                for indexno in range(len(iterators)):
                                    exec(list_of_indices[indexno] + " = " + iterators[indexno], user_dict)
                            condition_success = True
                            for condition in question.condition:
                                if not eval(condition, user_dict):
                                    condition_success = False
                                    break
                            if not condition_success:
                                continue
                    if self.debug:
                        seeking.append({'question': question, 'reason': 'asking', 'time': time.time()})
                    if question.question_type == "data":
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        string = from_safeid(question.fields[0].saveas) + ' = ' + repr(recursive_eval_dataobject(question.fields[0].data, user_dict))
                        exec(string, user_dict)
                        docassemble.base.functions.pop_current_variable()
                        return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                    if question.question_type == "data_from_code":
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        string = from_safeid(question.fields[0].saveas) + ' = ' + repr(recursive_eval_data_from_code(question.fields[0].data, user_dict))
                        exec(string, user_dict)
                        docassemble.base.functions.pop_current_variable()
                        return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                    if question.question_type == "objects":
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        success = False
                        for keyvalue in question.objects:
                            # logmessage("In a for loop for keyvalue")
                            for variable, object_type_name in keyvalue.items():
                                if variable != missing_var:
                                    continue
                                was_defined = False
                                try:
                                    exec("__oldvariable__ = " + str(missing_var), user_dict)
                                    exec("del " + str(missing_var), user_dict)
                                    was_defined = True
                                except:
                                    pass
                                user_dict["__object_type"] = eval(object_type_name, user_dict)
                                if re.search(r"\.", variable):
                                    m = re.search(r"(.*)\.(.*)", variable)
                                    variable = m.group(1)
                                    attribute = m.group(2)
                                    # command = variable + "." + attribute + " = " + object_type + "()"
                                    command = variable + ".initializeAttribute(" + repr(attribute) + ", __object_type)"
                                    # logmessage("Running " + command)
                                    exec(command, user_dict)
                                else:
                                    if user_dict["__object_type"].__class__.__name__ == 'DAObjectPlusParameters':
                                        command = variable + ' = __object_type.object_type(' + repr(variable) + ', **__object_type.parameters)'
                                    else:
                                        command = variable + ' = __object_type(' + repr(variable) + ')'
                                    # logmessage("Running " + command)
                                    exec(command, user_dict)
                                if "__object_type" in user_dict:
                                    del user_dict["__object_type"]
                                if missing_var in variable_stack:
                                    variable_stack.remove(missing_var)
                                try:
                                    eval(missing_var, user_dict)
                                    success = True
                                    # logmessage("the variable was defined")
                                    break
                                except:
                                    # logmessage("the variable was not defined")
                                    if was_defined:
                                        try:
                                            exec(str(missing_var) + " = __oldvariable__", user_dict)
                                            #exec("__oldvariable__ = " + str(missing_var), user_dict)
                                            exec("del __oldvariable__", user_dict)
                                        except:
                                            pass
                                    continue
                            if success:
                                # logmessage("success, break")
                                break
                        # logmessage("testing for success")
                        if not success:
                            # logmessage("no success, continue")
                            continue
                        #question.mark_as_answered(user_dict)
                        # logmessage("pop current variable")
                        docassemble.base.functions.pop_current_variable()
                        # logmessage("Returning")
                        return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                    if question.question_type == "template":
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        temp_vars = dict()
                        if is_generic:
                            if the_x != 'None':
                                temp_vars['x'] = user_dict['x']
                        if len(iterators):
                            for indexno in range(len(iterators)):
                                temp_vars[list_of_indices[indexno]] = user_dict[list_of_indices[indexno]]
                        if question.target is not None:
                            return({'type': 'template', 'question_text': question.content.text(user_dict).rstrip(), 'subquestion_text': None, 'under_text': None, 'continue_label': None, 'audiovideo': None, 'decorations': None, 'help_text': None, 'attachments': None, 'question': question, 'selectcompute': dict(), 'defaults': dict(), 'hints': dict(), 'helptexts': dict(), 'extras': dict(), 'labels': dict(), 'sought': missing_var, 'orig_sought': origMissingVariable})
                        string = "import docassemble.base.core"
                        exec(string, user_dict)
                        if question.decorations is None:
                            decoration_list = []
                        else:
                            decoration_list = question.decorations
                        actual_saveas = substitute_vars(from_safeid(question.fields[0].saveas), is_generic, the_x, iterators)
                        #docassemble.base.functions.this_thread.template_vars.append(actual_saveas)
                        found_object = False
                        try:
                            the_object = eval(actual_saveas, user_dict)
                            if the_object.__class__.__name__ == 'DALazyTemplate':
                                found_object = True
                        except:
                            pass
                        if not found_object:
                            string = from_safeid(question.fields[0].saveas) + ' = docassemble.base.core.DALazyTemplate(' + repr(actual_saveas) + ')'
                            exec(string, user_dict)
                            the_object = eval(actual_saveas, user_dict)
                            if the_object.__class__.__name__ != 'DALazyTemplate':
                                raise DAError("askfor: failure to define template object")
                        the_object.source_content = question.content
                        the_object.source_subject = question.subcontent
                        the_object.source_decorations = [dec['image'] for dec in decoration_list]
                        the_object.userdict = user_dict
                        the_object.tempvars = temp_vars
                        docassemble.base.functions.pop_current_variable()
                        return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                    if question.question_type == "table":
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        temp_vars = dict()
                        if is_generic:
                            if the_x != 'None':
                                temp_vars['x'] = user_dict['x']
                        if len(iterators):
                            for indexno in range(len(iterators)):
                                temp_vars[list_of_indices[indexno]] = user_dict[list_of_indices[indexno]]
                        table_info = TableInfo()
                        table_info.header = question.fields[0].extras['header']
                        table_info.is_editable = question.fields[0].extras['is_editable']
                        table_info.is_reorderable = question.fields[0].extras['is_reorderable']
                        table_info.row = question.fields[0].extras['row']
                        table_info.column = question.fields[0].extras['column']
                        table_info.indent = " " * (4 * int(question.fields[0].extras['indent']))
                        table_info.table_width = self.table_width
                        table_info.empty_message = question.fields[0].extras['empty_message']
                        table_info.saveas = from_safeid(question.fields[0].saveas)
                        actual_saveas = substitute_vars(table_info.saveas, is_generic, the_x, iterators)
                        #docassemble.base.functions.this_thread.template_vars.append(actual_saveas)
                        string = "import docassemble.base.core"
                        exec(string, user_dict)
                        found_object = False
                        try:
                            the_object = eval(actual_saveas, user_dict)
                            if the_object.__class__.__name__ == 'DALazyTableTemplate':
                                found_object = True
                        except:
                            pass
                        if not found_object:
                            string = from_safeid(question.fields[0].saveas) + ' = docassemble.base.core.DALazyTableTemplate(' + repr(actual_saveas) + ')'
                            exec(string, user_dict)
                            the_object = eval(actual_saveas, user_dict)
                            if the_object.__class__.__name__ != 'DALazyTableTemplate':
                                raise DAError("askfor: failure to define template object")
                        the_object.table_info = table_info
                        the_object.userdict = user_dict
                        the_object.tempvars = temp_vars
                        #logmessage("Pop variable for table")
                        docassemble.base.functions.pop_current_variable()
                        return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                    if question.question_type == 'attachments':
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        #logmessage("original missing variable is " + origMissingVariable)
                        attachment_text = question.processed_attachments(user_dict, seeking_var=origMissingVariable, use_cache=False)
                        if missing_var in variable_stack:
                            variable_stack.remove(missing_var)
                        try:
                            eval(missing_var, user_dict)
                            #question.mark_as_answered(user_dict)
                            docassemble.base.functions.pop_current_variable()
                            return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                        except:
                            logmessage("Problem with attachments block: " + err.__class__.__name__ + ": " + str(err))
                            continue
                    if question.question_type in ["code", "event_code"]:
                        question.exec_setup(is_generic, the_x, iterators, user_dict)
                        was_defined = False
                        try:
                            exec("__oldvariable__ = " + str(missing_var), user_dict)
                            exec("del " + str(missing_var), user_dict)
                            was_defined = True
                        except:
                            pass
                        if question.question_type == 'event_code':
                            docassemble.base.functions.pop_event_stack(origMissingVariable)
                        exec_with_trap(question, user_dict)
                        interview_status.mark_tentative_as_answered(user_dict)
                        if missing_var in variable_stack:
                            variable_stack.remove(missing_var)
                        if question.question_type == 'event_code':
                            docassemble.base.functions.pop_current_variable()
                            docassemble.base.functions.pop_event_stack(origMissingVariable)
                            return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                        try:
                            eval(missing_var, user_dict)
                            if was_defined:
                                exec("del __oldvariable__", user_dict)
                            if seeking_question:
                                continue
                            #question.mark_as_answered(user_dict)
                            docassemble.base.functions.pop_current_variable()
                            docassemble.base.functions.pop_event_stack(origMissingVariable)
                            return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                        except:
                            if was_defined:
                                try:
                                    exec(str(missing_var) + " = __oldvariable__", user_dict)
                                    #exec("__oldvariable__ = " + str(missing_var), user_dict)
                                    exec("del __oldvariable__", user_dict)
                                except:
                                    pass
                            continue
                    else:
                        interview_status.mark_tentative_as_answered(user_dict)
                        if question.question_type == 'continue':
                            continue
                        return question.ask(user_dict, old_user_dict, the_x, iterators, missing_var, origMissingVariable)
                if a_question_was_skipped:
                    raise DAError("Infinite loop: " + missingVariable + " already looked for, where stack is " + str(variable_stack))
                if 'forgive_missing_question' in docassemble.base.functions.this_thread.misc and origMissingVariable in docassemble.base.functions.this_thread.misc['forgive_missing_question']:
                    #logmessage("Forgiving " + origMissingVariable)
                    docassemble.base.functions.pop_current_variable()
                    docassemble.base.functions.pop_event_stack(origMissingVariable)
                    return({'type': 'continue', 'sought': origMissingVariable, 'orig_sought': origMissingVariable})
                raise DAErrorMissingVariable("Interview has an error.  There was a reference to a variable '" + origMissingVariable + "' that could not be looked up in the question file (for language '" + str(language) + "') or in any of the files incorporated by reference into the question file.", variable=origMissingVariable)
            except ForcedReRun as the_exception:
                #logmessage("forcedrerun")
                continue
            except (NameError, DAAttributeError, DAIndexError) as the_exception:
                if 'pending_error' in docassemble.base.functions.this_thread.misc:
                    del docassemble.base.functions.this_thread.misc['pending_error']
                #logmessage("Error in " + the_exception.__class__.__name__ + " is " + str(the_exception))
                if self.debug and docassemble.base.functions.this_thread.evaluation_context is not None:
                    logmessage("NameError exception during document assembly: " + text_type(the_exception))
                docassemble.base.functions.reset_context()
                seeking_question = False
                if isinstance(the_exception, ForcedNameError):
                    #logmessage("askfor: got a ForcedNameError for " + text_type(the_exception.name))
                    follow_mc = False
                    seeking_question = True
                    #logmessage("Seeking question is True")
                    newMissingVariable = the_exception.name
                    #logmessage("next action is " + repr(the_exception.next_action))
                    if the_exception.next_action is not None and not interview_status.checkin:
                        if 'event_stack' not in user_dict['_internal']:
                            user_dict['_internal']['event_stack'] = dict()
                        session_uid = interview_status.current_info['user']['session_uid']
                        if session_uid not in user_dict['_internal']['event_stack']:
                            user_dict['_internal']['event_stack'][session_uid] = list()
                        new_items = list()
                        for new_item in the_exception.next_action:
                            already_there = False
                            for event_item in user_dict['_internal']['event_stack'][session_uid]:
                                if event_item['action'] == new_item:
                                    already_there = True
                                    break
                            if not already_there:
                                new_items.append(new_item)
                        if len(new_items):
                            #logmessage("adding a new item to event_stack: " + repr(new_items))
                            user_dict['_internal']['event_stack'][session_uid] = new_items + user_dict['_internal']['event_stack'][session_uid]
                        #interview_status.next_action.extend(the_exception.next_action)
                    if the_exception.arguments is not None:
                        docassemble.base.functions.this_thread.current_info.update(dict(action=the_exception.name, arguments=the_exception.arguments))
                    if the_exception.name.startswith('_da_'):
                        continue
                else:
                    #logmessage("regular nameerror")
                    follow_mc = True
                    newMissingVariable = extract_missing_name(the_exception)
                if newMissingVariable == 'file':
                    raise
                #newMissingVariable = str(the_exception).split("'")[1]
                #if newMissingVariable in questions_tried and newMissingVariable in variable_stack:
                #    raise DAError("Infinite loop: " + missingVariable + " already looked for, where stack is " + str(variable_stack))
                if newMissingVariable not in questions_tried:
                    questions_tried[newMissingVariable] = set()
                else:
                    variable_stack.add(missingVariable)
                questions_tried[newMissingVariable].add(current_question)
                question_result = self.askfor(newMissingVariable, user_dict, old_user_dict, interview_status, variable_stack=variable_stack, questions_tried=questions_tried, seeking=seeking, follow_mc=follow_mc, recursion_depth=recursion_depth, seeking_question=seeking_question)
                if question_result['type'] == 'continue' and missing_var != newMissingVariable:
                    # logmessage("Continuing after asking for newMissingVariable " + str(newMissingVariable))
                    continue
                docassemble.base.functions.pop_current_variable()
                return(question_result)
            except UndefinedError as the_exception:
                #logmessage("UndefinedError")
                if self.debug and docassemble.base.functions.this_thread.evaluation_context is not None:
                    #logmessage(the_exception.__class__.__name__ + " exception during document assembly: " + text_type(the_exception) + "\n" + traceback.format_exc())
                    logmessage(the_exception.__class__.__name__ + " exception during document assembly")
                docassemble.base.functions.reset_context()
                newMissingVariable = extract_missing_name(the_exception)
                if newMissingVariable not in questions_tried:
                    questions_tried[newMissingVariable] = set()
                else:
                    variable_stack.add(missingVariable)
                questions_tried[newMissingVariable].add(current_question)
                question_result = self.askfor(newMissingVariable, user_dict, old_user_dict, interview_status, variable_stack=variable_stack, questions_tried=questions_tried, seeking=seeking, follow_mc=True, recursion_depth=recursion_depth, seeking_question=seeking_question)
                if question_result['type'] == 'continue':
                    continue
                docassemble.base.functions.pop_current_variable()
                return(question_result)
            except CommandError as qError:
                #logmessage("CommandError: " + str(qError))
                docassemble.base.functions.reset_context()
                question_data = dict(command=qError.return_type, url=qError.url)
                new_interview_source = InterviewSourceString(content='')
                new_interview = new_interview_source.get_interview()
                reproduce_basics(self, new_interview)
                new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                new_question.name = "Question_Temp"
                return(new_question.ask(user_dict, old_user_dict, 'None', [], missing_var, origMissingVariable))
            except ResponseError as qError:
                #logmessage("ResponseError")
                docassemble.base.functions.reset_context()
                #logmessage("Trapped ResponseError2")
                question_data = dict(extras=dict())
                if hasattr(qError, 'response') and qError.response is not None:
                    question_data['response'] = qError.response
                elif hasattr(qError, 'binaryresponse') and qError.binaryresponse is not None:
                    question_data['binaryresponse'] = qError.binaryresponse
                elif hasattr(qError, 'filename') and qError.filename is not None:
                    question_data['response filename'] = qError.filename
                elif hasattr(qError, 'url') and qError.url is not None:
                    question_data['redirect url'] = qError.url
                elif hasattr(qError, 'all_variables') and qError.all_variables:
                    if hasattr(qError, 'include_internal'):
                        question_data['include_internal'] = qError.include_internal
                    question_data['content type'] = 'application/json'
                    question_data['all_variables'] = True
                elif hasattr(qError, 'nullresponse') and qError.nullresponse:
                    question_data['null response'] = qError.nullresponse
                if hasattr(qError, 'content_type') and qError.content_type:
                    question_data['content type'] = qError.content_type
                new_interview_source = InterviewSourceString(content='')
                new_interview = new_interview_source.get_interview()
                reproduce_basics(self, new_interview)
                new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                new_question.name = "Question_Temp"
                #the_question = new_question.follow_multiple_choice(user_dict)
                docassemble.base.functions.pop_event_stack(origMissingVariable)
                return(new_question.ask(user_dict, old_user_dict, 'None', [], missing_var, origMissingVariable))
            except BackgroundResponseError as qError:
                # logmessage("BackgroundResponseError")
                docassemble.base.functions.reset_context()
                #logmessage("Trapped BackgroundResponseError2")
                question_data = dict(extras=dict())
                if hasattr(qError, 'backgroundresponse'):
                    question_data['backgroundresponse'] = qError.backgroundresponse
                new_interview_source = InterviewSourceString(content='')
                new_interview = new_interview_source.get_interview()
                reproduce_basics(self, new_interview)
                new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                new_question.name = "Question_Temp"
                docassemble.base.functions.pop_event_stack(origMissingVariable)
                return(new_question.ask(user_dict, old_user_dict, 'None', [], missing_var, origMissingVariable))
            except BackgroundResponseActionError as qError:
                # logmessage("BackgroundResponseActionError")
                docassemble.base.functions.reset_context()
                #logmessage("Trapped BackgroundResponseActionError2")
                question_data = dict(extras=dict())
                if hasattr(qError, 'action'):
                    question_data['action'] = qError.action
                new_interview_source = InterviewSourceString(content='')
                new_interview = new_interview_source.get_interview()
                reproduce_basics(self, new_interview)
                new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                new_question.name = "Question_Temp"
                docassemble.base.functions.pop_event_stack(origMissingVariable)
                return(new_question.ask(user_dict, old_user_dict, 'None', [], missing_var, origMissingVariable))
            except QuestionError as qError:
                #logmessage("QuestionError")
                docassemble.base.functions.reset_context()
                #logmessage("Trapped QuestionError")
                question_data = dict()
                if qError.question:
                    question_data['question'] = qError.question
                if qError.subquestion:
                    question_data['subquestion'] = qError.subquestion
                if qError.dead_end:
                    pass
                elif qError.buttons:
                    question_data['buttons'] = qError.buttons
                else:
                    buttons = list()
                    if qError.show_exit is not False and not (qError.show_leave is True and qError.show_exit is None):
                        exit_button = {word('Exit'): 'exit'}
                        if qError.url:
                            exit_button.update(dict(url=qError.url))
                        buttons.append(exit_button)
                    if qError.show_leave:
                        leave_button = {word('Leave'): 'leave'}
                        if qError.url:
                            leave_button.update(dict(url=qError.url))
                        buttons.append(leave_button)
                    if qError.show_restart is not False:
                        buttons.append({word('Restart'): 'restart'})
                    if len(buttons):
                        question_data['buttons'] = buttons
                new_interview_source = InterviewSourceString(content='')
                new_interview = new_interview_source.get_interview()
                reproduce_basics(self, new_interview)
                new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
                new_question.name = "Question_Temp"
                # will this be a problem? yup
                # the_question = new_question.follow_multiple_choice(user_dict)
                return(new_question.ask(user_dict, old_user_dict, 'None', [], missing_var, origMissingVariable))
            except CodeExecute as code_error:
                #logmessage("CodeExecute")
                docassemble.base.functions.reset_context()
                #if self.debug:
                #    interview_status.seeking.append({'question': question, 'reason': 'mandatory code'})
                #logmessage("Going to execute " + str(code_error.compute) + " where missing_var is " + str(missing_var))
                exec(code_error.compute, user_dict)
                try:
                    eval(missing_var, user_dict)
                    code_error.question.mark_as_answered(user_dict)
                    #logmessage("Got here 1")
                    #logmessage("returning from running code")
                    docassemble.base.functions.pop_current_variable()
                    #logmessage("Got here 2")
                    return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
                except:
                    #raise DAError("Problem setting that variable")
                    continue
            except SyntaxException as qError:
                #logmessage("SyntaxException")
                docassemble.base.functions.reset_context()
                the_question = None
                try:
                    the_question = question
                except:
                    pass
                if the_question is not None:
                    raise DAError(str(qError) + "\n\n" + str(self.idebug(self.data_for_debug)))
                raise DAError("no question available in askfor: " + str(qError))
            except CompileException as qError:
                #logmessage("CompileException")
                docassemble.base.functions.reset_context()
                the_question = None
                try:
                    the_question = question
                except:
                    pass
                if the_question is not None:
                    raise DAError(str(qError) + "\n\n" + str(self.idebug(self.data_for_debug)))
                raise DAError("no question available in askfor: " + str(qError))
            # except SendFileError as qError:
            #     #logmessage("Trapped SendFileError2")
            #     question_data = dict(extras=dict())
            #     if hasattr(qError, 'filename') and qError.filename is not None:
            #         question_data['response filename'] = qError.filename
            #     if hasattr(qError, 'content_type') and qError.content_type:
            #         question_data['content type'] = qError.content_type
            #     new_interview_source = InterviewSourceString(content='')
            #     new_interview = new_interview_source.get_interview()
            #     new_question = Question(question_data, new_interview, source=new_interview_source, package=self.source.package)
            #     new_question.name = "Question_Temp"
            #     return(new_question.ask(user_dict, old_user_dict, 'None', [], None, None))
        if 'forgive_missing_question' in docassemble.base.functions.this_thread.misc and origMissingVariable in docassemble.base.functions.this_thread.misc['forgive_missing_question']:
            #logmessage("Forgiving " + missing_var + " and " + origMissingVariable)
            docassemble.base.functions.pop_current_variable()
            docassemble.base.functions.pop_event_stack(origMissingVariable)
            return({'type': 'continue', 'sought': missing_var, 'orig_sought': origMissingVariable})
        raise DAErrorMissingVariable("Interview has an error.  There was a reference to a variable '" + origMissingVariable + "' that could not be found in the question file (for language '" + str(language) + "') or in any of the files incorporated by reference into the question file.", variable=origMissingVariable)

def substitute_vars(var, is_generic, the_x, iterators):
    if is_generic:
        if the_x != 'None' and hasattr(the_x, 'instanceName'):
            var = re.sub(r'^x\b', the_x.instanceName, var)
    if len(iterators):
        for indexno in range(len(iterators)):
            #the_iterator = iterators[indexno]
            #if isinstance(the_iterator, string_types) and re.match(r'^-?[0-9]+$', the_iterator):
            #    the_iterator = int(the_iterator)
            #var = re.sub(r'\[' + list_of_indices[indexno] + r'\]', '[' + repr(the_iterator) + ']', var)
            var = re.sub(r'\[' + list_of_indices[indexno] + r'\]', '[' + text_type(iterators[indexno]) + ']', var)
    return var

def reproduce_basics(interview, new_interview):
    new_interview.metadata = interview.metadata
    new_interview.external_files = interview.external_files

def unpack_list(item, target_list=None):
    if target_list is None:
        target_list = list()
    if not isinstance(item, (list, dict)):
        target_list.append(item)
    else:
        for subitem in item:
            unpack_list(subitem, target_list)
    return target_list
            
def process_selections(data, manual=False, exclude=None):
    if exclude is None:
        to_exclude = list()
    else:
        to_exclude = unpack_list(exclude)
    result = []
    if (isinstance(data, abc.Iterable) and not isinstance(data, (string_types, dict))) or (hasattr(data, 'elements') and isinstance(data.elements, list)):
        for entry in data:
            if isinstance(entry, dict) or (hasattr(entry, 'elements') and isinstance(entry.elements, dict)):
                the_item = dict()
                for key in entry:
                    if len(entry) > 1:
                        if key in ['default', 'help', 'image']:
                            continue
                        if 'default' in entry:
                            the_item['default'] = entry['default']
                        if 'help' in entry:
                            the_item['help'] = entry['help']
                        if 'image' in entry:
                            if entry['image'].__class__.__name__ == 'DAFile':
                                entry['image'].retrieve()
                                if entry['image'].mimetype is not None and entry['image'].mimetype.startswith('image'):
                                    the_item['image'] = dict(type='url', value=entry['image'].url_for())
                            elif entry['image'].__class__.__name__ == 'DAFileList':
                                entry['image'][0].retrieve()
                                if entry['image'][0].mimetype is not None and entry['image'][0].mimetype.startswith('image'):
                                    the_item['image'] = dict(type='url', value=entry['image'][0].url_for())
                            elif entry['image'].__class__.__name__ == 'DAStaticFile':
                                the_item['image'] = dict(type='url', value=entry['image'].url_for())
                            else:
                                the_item['image'] = dict(type='decoration', value=entry['image'])
                    the_item['key'] = key
                    the_item['label'] = entry[key]
                    is_not_boolean = False
                    for val in entry.values():
                        if val not in (True, False):
                            is_not_boolean = True
                    if key not in to_exclude and (is_not_boolean or entry[key] is True):
                        result.append(the_item)
            if (isinstance(entry, list) or (hasattr(entry, 'elements') and isinstance(entry.elements, list))) and len(entry) > 0:
                if entry[0] not in to_exclude:
                    if len(entry) >= 4:
                        result.append(dict(key=entry[0], label=entry[1], default=entry[2], help=entry[3]))
                    elif len(entry) == 3:
                        result.append(dict(key=entry[0], label=entry[1], default=entry[2]))
                    elif len(entry) == 1:
                        result.append(dict(key=entry[0], label=entry[0]))
                    else:
                        result.append(dict(key=entry[0], label=entry[1]))
            elif isinstance(entry, (string_types, bool, int, float)):
                if entry not in to_exclude:
                    result.append(dict(key=entry, label=entry))
            elif hasattr(entry, 'instanceName'):
                if entry not in to_exclude:
                    result.append(dict(key=text_type(entry), label=text_type(entry)))
    elif isinstance(data, dict) or (hasattr(data, 'elements') and isinstance(data.elements, dict)):
        if isinstance(data, OrderedDict) or (hasattr(data, 'elements') and isinstance(data.elements, OrderedDict)):
            the_items = data.items()
        else:
            the_items = sorted(data.items(), key=operator.itemgetter(1))
        for key, value in the_items:
            if key not in to_exclude:
                if isinstance(value, (string_types, bool, int, float)):
                    result.append(dict(key=key, label=value))
                elif hasattr(value, 'instanceName'):
                    result.append(dict(key=key, label=text_type(value)))
                else:
                    logmessage("process_selections: non-label passed as label in dictionary")
    else:
        raise DAError("Unknown data type in choices selection: " + re.sub(r'[<>]', '', repr(data)))
    return(result)

def process_selections_manual(data):
    result = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                the_item = dict()
                for key in entry:
                    if len(entry) > 1:
                        if key in ['default', 'help', 'image']:
                            continue
                        if 'key' in entry and 'label' in entry and key != 'key':
                            continue
                        if 'default' in entry:
                            the_item['default'] = entry['default']
                        if 'help' in entry:
                            the_item['help'] = TextObject(entry['help'])
                        if 'image' in entry:
                            if entry['image'].__class__.__name__ == 'DAFile':
                                entry['image'].retrieve()
                                if entry['image'].mimetype is not None and entry['image'].mimetype.startswith('image'):
                                    the_item['image'] = dict(type='url', value=entry['image'].url_for())
                            elif entry['image'].__class__.__name__ == 'DAFileList':
                                entry['image'][0].retrieve()
                                if entry['image'][0].mimetype is not None and entry['image'][0].mimetype.startswith('image'):
                                    the_item['image'] = dict(type='url', value=entry['image'][0].url_for())
                            elif entry['image'].__class__.__name__ == 'DAStaticFile':
                                the_item['image'] = dict(type='url', value=entry['image'].url_for())
                            else:
                                the_item['image'] = dict(type='decoration', value=entry['image'])
                        if 'key' in entry and 'label' in entry:
                            the_item['key'] = TextObject(entry['key'])
                            the_item['label'] = TextObject(entry['label'])
                            result.append(the_item)
                            continue
                    the_item['key'] = TextObject(entry[key])
                    the_item['label'] = TextObject(key)
                    result.append(the_item)
            if isinstance(entry, list):
                result.append(dict(key=TextObject(entry[0]), label=TextObject(entry[1])))
            elif isinstance(entry, string_types):
                result.append(dict(key=TextObject(entry), label=TextObject(entry)))
            elif isinstance(entry, (int, float, bool, NoneType)):
                result.append(dict(key=TextObject(text_type(entry)), label=TextObject(text_type(entry))))
    elif isinstance(data, dict):
        for key, value in sorted(data.items(), key=operator.itemgetter(1)):
            result.append(dict(key=TextObject(value), label=TextObject(key)))
    else:
        raise DAError("Unknown data type in manual choices selection: " + re.sub(r'[<>]', '', repr(data)))
    return(result)

def extract_missing_name(the_error):
    #logmessage("extract_missing_name: string was " + str(string))
    m = nameerror_match.search(text_type(the_error))
    if m:
        return m.group(1)
    else:
        raise the_error

def auto_determine_type(field_info, the_value=None):
    types = dict()
    if 'selections' in field_info:
        for item in field_info['selections']:
            the_type = type(item[0]).__name__
            if the_type not in types:
                types[the_type] = 0
            types[the_type] += 1
    if the_value is not None:
        the_type = type(the_value).__name__
        if the_type not in types:
            types[the_type] = 0
        types[the_type] += 1
    if 'str' in types or 'unicode' in types:
        return
    if len(types) == 2:
        if 'int' in types and 'float' in types:
            field_info['type'] = 'float'
            return
    if len(types) > 1:
        return
    if 'bool' in types:
        field_info['type'] = 'boolean'
        return
    if 'int' in types:
        field_info['type'] = 'integer'
        return
    if 'float' in types:
        field_info['type'] = 'float'
        return
    return

def get_mimetype(filename):
    if filename is None:
        return 'text/plain; charset=utf-8'
    mimetype, encoding = mimetypes.guess_type(filename)
    extension = filename.lower()
    extension = re.sub('.*\.', '', extension)
    if extension == '3gpp':
        mimetype = 'audio/3gpp'
    if mimetype is None:
        mimetype = 'text/plain'    
    return mimetype

def interpret_label(text):
    if text is None:
        return u'no label'
    return text_type(text)

def recurse_indices(expression_array, variable_list, pre_part, final_list, var_subs_dict, var_subs, generic_dict, generic):
    if len(expression_array) == 0:
        return
    the_expr = "".join(pre_part) + "".join(expression_array)
    if the_expr not in final_list and the_expr != 'x':
        final_list.append(the_expr)
        var_subs_dict[the_expr] = var_subs
        generic_dict[the_expr] = "".join(generic)
    first_part = expression_array.pop(0)
    if match_brackets.match(first_part) and len(variable_list) > 0:
        new_var_subs = copy.copy(var_subs)
        new_var_subs.append(re.sub(r'^\[|\]$', r'', first_part))
        new_list_of_indices = copy.copy(variable_list)
        var_to_use = new_list_of_indices.pop(0)
        new_part = copy.copy(pre_part)
        new_part.append('[' + var_to_use + ']')
        recurse_indices(copy.copy(expression_array), new_list_of_indices, new_part, final_list, var_subs_dict, new_var_subs, generic_dict, generic)
        if len(new_var_subs) == 0 and len(generic) == 0:
            recurse_indices(copy.copy(expression_array), new_list_of_indices, ['x', '[' + var_to_use + ']'], final_list, var_subs_dict, new_var_subs, generic_dict, copy.copy(pre_part))
    pre_part.append(first_part)
    recurse_indices(copy.copy(expression_array), variable_list, copy.copy(pre_part), final_list, var_subs_dict, var_subs, generic_dict, copy.copy(generic))
    if len(var_subs) == 0 and len(generic) == 0:
        recurse_indices(copy.copy(expression_array), variable_list, ['x'], final_list, var_subs_dict, var_subs, generic_dict, copy.copy(pre_part))

def ensure_object_exists(saveas, datatype, the_user_dict, commands=None):
    # logmessage("ensure object exists: " + str(saveas))
    if commands is None:
        execute = True
        commands = list()
    else:
        execute = False
    already_there = False
    try:
        eval(saveas, the_user_dict)
        already_there = True
    except:
        pass
    if already_there:
        #logmessage("ensure object exists: already there")
        return
    use_initialize = False
    parse_result = parse_var_name(saveas)
    if not parse_result['valid']:
        raise DAError("Variable name " + saveas + " is invalid: " + parse_result['reason'])
    method = None
    if parse_result['final_parts'][1] != '':
        if parse_result['final_parts'][1][0] == '.':
            try:
                core_key = eval(parse_result['final_parts'][0], the_user_dict)
                if hasattr(core_key, 'instanceName'):
                    method = 'attribute'
            except:
                pass
        elif parse_result['final_parts'][1][0] == '[':
            try:
                core_key = eval(parse_result['final_parts'][0], the_user_dict)
                if hasattr(core_key, 'instanceName'):
                    method = 'index'
            except:
                pass
    if "import docassemble.base.core" not in commands:
        commands.append("import docassemble.base.core")
    if method == 'attribute':
        attribute_name = parse_result['final_parts'][1][1:]
        if datatype == 'checkboxes':
            commands.append(parse_result['final_parts'][0] + ".initializeAttribute(" + repr(attribute_name) + ", docassemble.base.core.DADict, auto_gather=False)")
        elif datatype == 'object_checkboxes':
            commands.append(parse_result['final_parts'][0] + ".initializeAttribute(" + repr(attribute_name) + ", docassemble.base.core.DAList, auto_gather=False)")
    elif method == 'index':
        index_name = parse_result['final_parts'][1][1:-1]
        if datatype == 'checkboxes':
            commands.append(parse_result['final_parts'][0] + ".initializeObject(" + repr(index_name) + ", docassemble.base.core.DADict, auto_gather=False)")
        elif datatype == 'object_checkboxes':
            commands.append(parse_result['final_parts'][0] + ".initializeObject(" + repr(index_name) + ", docassemble.base.core.DAList, auto_gather=False)")
    else:
        if datatype == 'checkboxes':
            commands.append(saveas + ' = docassemble.base.core.DADict(' + repr(saveas) + ', auto_gather=False)')
        elif datatype == 'object_checkboxes':
            commands.append(saveas + ' = docassemble.base.core.DAList(' + repr(saveas) + ', auto_gather=False)')
    if execute:
        for command in commands:
            #logmessage("Doing " + command)
            exec(command, the_user_dict)
    
def invalid_variable_name(varname):
    if not isinstance(varname, string_types):
        return True
    if re.search(r'[\n\r\(\)\{\}\*\^\#]', varname):
        return True
    varname = re.sub(r'[\.\[].*', '', varname)
    if not valid_variable_match.match(varname):
        return True 
    return False

def exec_with_trap(the_question, the_dict):
    try:
        exec(the_question.compute, the_dict)
    except (NameError, UndefinedError, CommandError, ResponseError, BackgroundResponseError, BackgroundResponseActionError, QuestionError, AttributeError, MandatoryQuestion, CodeExecute, SyntaxException, CompileException):
        raise
    except Exception as e:
        cl, exc, tb = sys.exc_info()
        exc.user_dict = docassemble.base.functions.serializable_dict(the_dict)
        if len(traceback.extract_tb(tb)) == 2:
            line_with_error = traceback.extract_tb(tb)[-1][1]
            if isinstance(line_with_error, int) and line_with_error > 0 and hasattr(the_question, 'sourcecode'):
                exc.da_line_with_error = the_question.sourcecode.splitlines()[line_with_error - 1]
                if PY2:
                    exc.traceback = traceback.format_exc()
                if PY3:
                    exc.__traceback__ = tb
        del cl
        del exc
        del tb
        raise

ok_outside_string = string.ascii_letters + string.digits + '.[]_'
ok_inside_string = string.ascii_letters + string.digits + string.punctuation + " "

def parse_var_name(var):
    var_len = len(var)
    cur_pos = 0
    in_bracket = 0
    in_quote = 0
    the_quote = None
    dots = list()
    brackets = list()
    while cur_pos < var_len:
        char = var[cur_pos]
        if char == '[':
            if cur_pos == 0:
                return dict(valid=False, reason='bracket at start')
            if var[cur_pos - 1] == '.':
                return dict(valid=False, reason='dot before bracket')
            if not in_quote:
                if in_bracket:
                    return dict(valid=False, reason='nested brackets')
                in_bracket = 1
                brackets.append(cur_pos)
        elif char == ']':
            if cur_pos == 0:
                return dict(valid=False)
            if var[cur_pos - 1] == '.':
                return dict(valid=False, reason='dot before bracket')
            if not in_quote:
                if in_bracket:
                    in_bracket = 0
                else:
                    return dict(valid=False, reason='unexpected end bracket')
        elif char in ("'", '"'):
            if cur_pos == 0 or not in_bracket:
                return dict(valid=False, reason='unexpected quote mark')
            if in_quote:
                if char == the_quote and var[cur_pos - 1] != "\\":
                    in_quote = 0
            else:
                in_quote = 1
                the_quote = char
        else:
            if not (in_quote or in_bracket):
                if char not in ok_outside_string:
                    return dict(valid=False, reason='invalid character in variable name')
            if cur_pos == 0:
                if char in string.digits or char == '.':
                    return dict(valid=False, reason='starts with digit or dot')
            else:
                if var[cur_pos - 1] == '.' and char in string.digits:
                    return dict(valid=False, reason='attribute starts with digit')
            if in_quote:
                if char not in ok_inside_string:
                    return dict(valid=False, reason='invalid character in string')
            else:
                if char == '.':
                    if in_bracket:
                        return dict(valid=False, reason="dot in bracket")
                    if cur_pos > 0 and var[cur_pos - 1] == '.':
                        return dict(valid=False, reason = 'two dots')
                    dots.append(cur_pos)
        cur_pos += 1
    if in_bracket:
        return dict(valid=False, reason='dangling bracket part')
    if in_quote:
        return dict(valid=False, reason='dangling quote part')
    objects = [var[0:dot_pos] for dot_pos in dots]
    bracket_objects = [var[0:bracket_pos] for bracket_pos in brackets]
    final_cut = 0
    if len(dots):
        final_cut = dots[-1]
    if len(brackets):
        if brackets[-1] > final_cut:
            final_cut = brackets[-1]
    if final_cut > 0:
        final_parts = (var[0:final_cut], var[final_cut:])
    else:
        final_parts = (var, '')
    return dict(valid=True, objects=objects, bracket_objects=bracket_objects, final_parts=final_parts)

class DAExtension(Extension):
    def filter_stream(self, stream):
        in_var = False
        met_pipe = False
        for token in stream:
            if token.type == 'variable_begin':
                in_var = True
                met_pipe = False
            if token.type == 'variable_end':
                in_var = False
                if not met_pipe:
                    yield Token(token.lineno, 'pipe', None)
                    yield Token(token.lineno, 'name', 'ampersand_filter')
            if in_var and token.type == 'pipe':
                met_pipe = True
            yield token

class DAEnvironment(Environment):
    def from_string(self, source, **kwargs):
        source = re.sub(r'({[\%\{].*?[\%\}]})', fix_quotes, source)
        return super(DAEnvironment, self).from_string(source, **kwargs)
    def getitem(self, obj, argument):
        """Get an item or attribute of an object but prefer the item."""
        try:
            return obj[argument]
        except (AttributeError, TypeError, LookupError):
            if isinstance(argument, string_types):
                try:
                    attr = str(argument)
                except Exception:
                    pass
                else:
                    try:
                        return getattr(obj, attr)
                    except AttributeError:
                        pass
            return self.undefined(obj=obj, name=argument, accesstype='item')

    def getattr(self, obj, attribute):
        """Get an item or attribute of an object but prefer the attribute.
        Unlike :meth:`getitem` the attribute *must* be a bytestring.
        """
        try:
            return getattr(obj, attribute)
        except AttributeError:
            pass
        try:
            return obj[attribute]
        except (TypeError, LookupError, AttributeError):
            return self.undefined(obj=obj, name=attribute, accesstype='attribute')

def ampersand_filter(value):
    if value.__class__.__name__ in ('DAFile', 'DALink'): #, 'InlineImage', 'RichText', 'Listing', 'Document', 'Subdoc'
        return value
    return re.sub(r'&(?!#\d{4};|amp;)', '&amp;', text_type(value))

class DAStrictUndefined(StrictUndefined):
    __slots__ = ('_undefined_type')
    def __init__(self, hint=None, obj=missing, name=None, exc=UndefinedError, accesstype=None):
        self._undefined_hint = hint
        self._undefined_obj = obj
        self._undefined_name = name
        self._undefined_exception = exc
        self._undefined_type = accesstype

    @internalcode
    def __getattr__(self, name):
        if name[:2] == '__':
            raise AttributeError(name)
        return self._fail_with_undefined_error(attribute=True)

    @internalcode
    def __getitem__(self, index):
        if name[:2] == '__':
            raise IndexError(name)
        return self._fail_with_undefined_error(item=True)

    @internalcode
    def _fail_with_undefined_error(self, *args, **kwargs):
        if True or self._undefined_hint is None:
            if self._undefined_obj is missing:
                hint = "'%s' is undefined" % self._undefined_name
            elif 'attribute' in kwargs or self._undefined_type == 'attribute':
                if hasattr(self._undefined_obj, 'instanceName'):
                    hint = "'%s.%s' is undefined" % (
                        self._undefined_obj.instanceName,
                        self._undefined_name
                    )
                else:
                    hint = '%r has got no attribute %r' % (
                        object_type_repr(self._undefined_obj),
                        self._undefined_name
                    )
            else:
                if hasattr(self._undefined_obj, 'instanceName'):
                    hint = "'%s[%r]' is undefined" % (
                        self._undefined_obj.instanceName,
                        self._undefined_name
                    )
                else:
                    hint = '%s has no element %r' % (
                        object_type_repr(self._undefined_obj),
                        self._undefined_name
                    )
        else:
            hint = self._undefined_hint
        raise self._undefined_exception(hint)
    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
        __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = __int__ = \
        __float__ = __complex__ = __pow__ = __rpow__ = __sub__ = \
        __rsub__= __iter__ = __str__ = __len__ = __nonzero__ = __eq__ = \
        __ne__ = __bool__ = __hash__ = __unicode__ = _fail_with_undefined_error

def custom_jinja_env():
    env = DAEnvironment(undefined=DAStrictUndefined, extensions=[DAExtension])
    env.filters['ampersand_filter'] = ampersand_filter
    env.filters['markdown'] = markdown_filter
    return env

def markdown_filter(text):
    return docassemble.base.file_docx.markdown_to_docx(text_type(text), docassemble.base.functions.this_thread.misc.get('docx_template', None))
