import sublime
import sublime_plugin
import subprocess
import re
import os
import time

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
        if self.time_run_behat+60 < int(time.time()):
            self.time_run_behat = int(time.time())
            steps_list_file = open(self.settings['behat_steps_list_file'])
            output = steps_list_file.read()
            self.snippets = filter(None,sorted([self.create_snippet(step) for step in output.strip().splitlines()]))
            self.steps = [] 
            for snippet in self.snippets:
    	    
                #snippet = re.sub('\$\{\d+\}', '', snippet)
                #snippet = re.sub('\$\{\d+:([\d|\w]+)\}', '\\1', snippet)
                self.steps.append(snippet)

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
