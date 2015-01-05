import os
import sublime
import sublime_plugin
import subprocess
import re

diction_word_regions = []
diction_words = [] # line nos and diction text
os.environ['PATH'] += os.pathsep + '/usr/local/bin' # add this for OSX homebrew diction executable

class DictionMatchObject(object):
    ''' object for a single diction suggestion '''
    def __init__(self, lineno, conflicting_phrase='', suggestion='', surrounding_text='', surrounding_after=True):
        self.lineno = lineno
        self.conflicting_phrase = conflicting_phrase
        self.suggestion = suggestion
        self.surrounding_text = surrounding_text
        self.surrounding_after = surrounding_after

    def __str__(self):
        return 'lineno: ' + self.lineno + '\n' \
             + 'conflicting_phrase: ' + self.conflicting_phrase + '\n' \
             + 'suggestion: ' + self.suggestion + '\n' \
             + 'surrounding_after: ' + str(self.surrounding_after) + '  surrounding_text: ' + self.surrounding_text + '\n'

def mark_words(view, search_all=True):
    global settings, diction_word_regions

    def neighborhood(iterable):
        ''' generator function providing next and previous items for tokens '''
        iterator = iter(iterable)
        prev = None
        item = iterator.next()  # throws StopIteration if empty.
        for next in iterator:
            yield (prev,item,next)
            prev = item
            item = next
        yield (prev,item,None)

    def run_diction():
        ''' runs the diction executable and parses its output '''
        diction_words = []
        
        window = sublime.active_window()
        if window:
            view = window.active_view()
        if view:
            if settings.debug:
                print('\n\nDiction: running diction on file: ' + view.file_name())
            try:
                # add -s to get the suggestions from diction
                output = subprocess.Popen([settings.diction_executable, '-qs', view.file_name()], stdout=subprocess.PIPE).communicate()[0]
            except OSError:
                print('Diction: Error. diction does not seem to be installed or is not in the PATH.')

            prefiltered_output = output[:output.rfind('\n\n')]
            # needed regexes
            ex_brackets = re.compile('\[(.*?)\]')
            ex_arrows_before = re.compile('(.*)(?= ->)')
            ex_arrows_after = re.compile('-> (.*)')

            for l in prefiltered_output.split('\n'):
                if l.split(':') == ['']:
                    continue # empty lines of diction output
                diction_text_for_line = ''.join(l.split(': ')[1:]) # strip the line no
                
                

                print ex_brackets.split(diction_text_for_line)
                # find the conflicting phrases in this line
                prev_token = '' # in case there is no next token to align the text anymore (end of sentence, paragraph)
                for prev_token, token, next_token in neighborhood(ex_brackets.split(diction_text_for_line)):
                    print token
                    print '-'
                    if '->' in token: # suggestion by diction: a new conflict found
                        new_diction_match_object = DictionMatchObject(l.split(': ')[0], diction_text_for_line, '', '')
                        new_diction_match_object.conflicting_phrase = ex_arrows_before.search(token).group()
                        new_diction_match_object.suggestion = ex_arrows_after.search(token).group()[3:]

                        if next_token == None or next_token.strip() == '': 
                            print '!!!!NO NEXT TOKEN!!!'
                            new_diction_match_object.surrounding_text = prev_token
                            new_diction_match_object.surrounding_after = False
                        else:
                            new_diction_match_object.surrounding_text = next_token
                            new_diction_match_object.surrounding_after = True
                        
                        
                        diction_words.append(new_diction_match_object)

                if settings.debug:
                    print ('Diction word tokens found:\n')
                    for nd in diction_words:
                        print nd
                
            sublime.status_message('    Diction: ' + output[output.rfind('\n\n'):])
        else:
            print('Diction: could not get view. Abort') 
            return []
        return diction_words

    def find_words(pattern):
        if search_all:
            if settings.debug:
                print('Diction: searching whole document')
            found_regions = view.find_all(pattern, sublime.IGNORECASE, '', [])
        else:
            if settings.debug:
                print('Diction: searching around visible region')
            found_regions = []
            chunk_size = 2 * 10 ** 3

            visible_region = view.visible_region()
            begin = max(visible_region.begin() - chunk_size, 0)
            end = min(visible_region.end() + chunk_size, view.size())
            from_point = begin
            while True:
                region = view.find(pattern, from_point, sublime.IGNORECASE)
                if region:
                    found_regions.append(region)
                    rend = region.end()
                    if rend > end:
                        break
                    else:
                        from_point = rend
                else:
                    break
        return found_regions

    def lazy_mark_regions(new_regions, old_regions, style_key, color_scope_name, symbol_name, draw_style):
        if old_regions != new_regions or True:
            # print 'adding new regions'
            view.erase_regions(style_key)
            # name, regions, style, symbol in gutter, draw outlined
            view.add_regions(style_key, new_regions, color_scope_name, symbol_name, draw_style)
        return new_regions

    # run diction, find the bad phrases
    try:
        out_flags = sublime.DRAW_NO_FILL + sublime.DRAW_NO_OUTLINE + sublime.DRAW_STIPPLED_UNDERLINE
    except AttributeError:    # nothing of this is available in ST2
        out_flags = sublime.DRAW_OUTLINED
    
    words = run_diction()
    testwordpattern = 'testword'
    new_regions = find_words(testwordpattern)
    diction_word_regions = lazy_mark_regions(
        new_regions,
        diction_word_regions,
        'Diction',
        settings.color_scope_name,
        'comment',
        out_flags ) #


class DictionListener(sublime_plugin.EventListener):
    enabled = False

    @classmethod
    def disable(cls):
        ''' disable package, remove marks on ui '''
        cls.enabled = False
        window = sublime.active_window()
        if window:
            view = window.active_view()
            if view:
                view.erase_regions("Diction")

    def handle_event(self, view):
        """
        determines if the package status changed. marks words when turned on.
        """
        global settings

        # does settings enable package?
        if not settings.enabled:
            DictionListener.disable()
            return

        # check this file if either it's enabled or if the extensions list is empty
        file_name = view.file_name()

        ext = ''
        if file_name:
            # Use the extension if it exists, otherwise use the whole filename
            ext = os.path.splitext(file_name)
            if ext[1]:
                ext = ext[1]
            else:
                ext = os.path.split(file_name)[1]

        allowed_extensions = settings.get('extensions')
        if (not allowed_extensions) or ext in allowed_extensions:
            if not DictionListener.enabled:
                DictionListener.enabled = True

            mark_words(view)
            return

        DictionListener.disable()  # turn off for this file!

    def on_activated(self, view):
        if not view.is_loading():
            self.handle_event(view)

    def on_post_save(self, view):
        self.handle_event(view)

    def on_load(self, view):
        self.handle_event(view)

    def on_modified(self, view):
        if DictionListener.enabled:
            mark_words(view, search_all=False)


def load_settings():
    ''' process settings file on plugin reload '''
    settings = sublime.load_settings('Diction.sublime-settings')

    def process_settings(settings):
        ''' process settings from file '''

        setattr(settings, 'enabled', settings.get('enabled', True))
        setattr(settings, 'debug', settings.get('debug', True))
        setattr(settings, 'color_scope_name', settings.get('color_scope_name', 'comment'))
        setattr(settings, 'diction_executable', settings.get('diction_executable', 'diction'))

    process_settings(settings)
    if not settings.enabled:
        DictionListener.disable()

    # reload when package specific preferences changes
    settings.add_on_change('reload', lambda: process_settings(settings))

    return settings

settings = None
# only do this for ST2, use plugin_loaded for ST3.
if int(sublime.version()) < 3000:
    settings = load_settings()  # read settings as package loads.

def plugin_loaded():
    """
    Seems that in ST3, plugins should read settings in this method.
    See: http://www.sublimetext.com/forum/viewtopic.php?f=6&t=15160
    """
    global settings
    settings = load_settings()  # read settings as package loads.


class ToggleDiction(sublime_plugin.ApplicationCommand):
    ''' menu item that toggles the enabled status of this package '''
    
    def run(self):
        global settings
        settings.enabled = not settings.enabled
        if not settings.enabled:
            sublime.active_window().active_view().erase_regions("Diction")
        else:
            mark_words(sublime.active_window().active_view())

    def description(self):
        ''' determines the text of the menu item '''
        global settings
        return 'Disable' if settings.enabled else 'Enable'