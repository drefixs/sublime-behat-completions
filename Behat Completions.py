import sublime
import sublime_plugin
import subprocess
import re
import os
import time
from os.path import dirname, realpath
from xml.sax.saxutils import escape

BC_PLUGIN_PATH = dirname(realpath(__file__))

class BehatCompletionsCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view
        self.time_run_behat = 0
        self.steps = []

        # Load settings
        self.settings = {}
        settings = sublime.load_settings('Behat Completions.sublime-settings')
        for setting in ['behat_executable_path', 'behat_config_path', 'behat_steps_list_file']:      
            if settings.get(setting) == None:
                continue
            self.settings[setting] = settings.get(setting)

    def run(self, edit):
        if self.time_run_behat+30 < int(time.time()):
            self.time_run_behat = int(time.time())
            steps_list_file = open(sublime.packages_path()+"/Behat Completions/"+ self.settings['behat_steps_list_file'])
            output = steps_list_file.read()
            self.snippets = filter(None,sorted([self.create_snippet(step) for step in output.strip().splitlines()]))
            self.steps = [] 
            for snippet in self.snippets:
                self.steps.append(snippet)
            output = re.sub(r'.*(?:Given|When|Then|And)\s+(.*)','\\1', output)
            output = re.sub(re.compile('(^[^\/].*?)\:\w+', re.MULTILINE),'\\1"((?:[^"]|\\")*)"', output)
            output = re.sub(re.compile('(^[^\/].*?)\:\w+', re.MULTILINE),'\\1"((?:[^"]|\\")*)"', output)
            output = re.sub(re.compile('(^[^\/].*?)\:\w+', re.MULTILINE),'\\1"((?:[^"]|\\")*)"', output)
            output = re.sub(r'\/\^?(.*?)\$?\/','\\1', output)
            output = re.sub(r'\?\P\<(\w+)\>','', output)
            
            output = escape(output).strip()
            output = re.sub(r'(.*)','<dict>\n<key>match</key>\n<string>.*(Given|When|Then|And)\s\\1$</string>\n<key>captures</key>\n<dict>\n<key>1</key>\n<dict>\n<key>name</key>\n<string>entity.name.class.behat</string></dict></dict></dict>',output)
            
            behat_tmLanguage_t = open(BC_PLUGIN_PATH+"/Behat.tmLanguage.template")
            behat_tmLanguage_s = behat_tmLanguage_t.read()
            behat_tmLanguage_t.close()

            behat_tmLanguage_s = re.sub(r'\<dict\>\%ADDSTEPVALIDATION\%\<\/dict\>',output, behat_tmLanguage_s)

            behat_tmLanguage = open(sublime.packages_path()+"/Behat/Syntaxes/Behat.tmLanguage", 'w')
            behat_tmLanguage.write(behat_tmLanguage_s)
        window = sublime.active_window()
        window.show_quick_panel(self.steps, self.on_quick_panel_done)

    def on_quick_panel_done(self, picked):
        if picked == -1:
            return
        self.view.run_command('insert_snippet', { 'contents': " " + self.snippets[picked] + "$0" })

    def create_snippet(self, step):
        step = step.strip()
        res = re.search(r'(Given|When|Then)\s+(.*)', step)
        
        if res:
            # Trim start/end /
            pattern = res.group(2).strip('/').lstrip('^').rstrip('$')

            # Search for named sub-pattern
            pattern = re.sub(r'[\'\"]?\(\?P\<(\w+)\>[\'\"]?(\(.*?\))?[\'\"]?.*?\)[\'\"]?', ':\\1', pattern)

            # Search for named sub-pattern
            #pattern = re.sub('', ':string:', pattern)
           
            return pattern

        return False

    def named_group_repl(self, match):
        self.snippet_parameter_index += 1

        if match.group(1) == '':
            return '${%d}' % (self.snippet_parameter_index)

        return '${%d:%s}' % (self.snippet_parameter_index,match.group(1))

    def unbraced_chunks(self, pattern):
        chunk = ''
        depth = 0
        for char in pattern:
            if char == '(':
                if depth == 0:
                    yield chunk
                    chunk = ''
                depth = depth + 1
            elif char == ')' and depth > 0:
                depth = depth - 1
            elif depth == 0:
                chunk = chunk + char
        yield chunk
