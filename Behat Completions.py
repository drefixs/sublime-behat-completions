import sublime
import sublime_plugin
import subprocess
import re

class BehatCompletionsCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view

        # Load settings
        self.settings = {}
        settings = sublime.load_settings('Behat Completions.sublime-settings')
        for setting in ['behat_executable_path', 'behat_config_path']:
            if settings.get(setting) == None:
                continue
            self.settings[setting] = settings.get(setting)

    def run(self, edit):
        args = [self.settings['behat_executable_path'], '-dl', '-c', self.settings['behat_config_path']]
        output = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
        self.snippets = sorted([self.create_snippet(step) for step in output.strip().split("\n")])

        steps = []
        for snippet in self.snippets:
            snippet = re.sub('\$\{\d+\}', '', snippet)
            snippet = re.sub('\$\{\d+:([\d|\w]+)\}', '\\1', snippet)
            steps.append(snippet)

        window = sublime.active_window()
        window.show_quick_panel(steps, self.on_quick_panel_done)

    def on_quick_panel_done(self, picked):
        if picked == -1:
            return
        self.view.run_command('insert_snippet', { 'contents': " " + self.snippets[picked] + "$0" })

    def create_snippet(self, step):
        step = step.strip()
        res = re.match(r'^(Given|When|Then)\s+\/(.*)\/', step)
        if res:
            # Trim start/end characters
            pattern = res.group(2).lstrip('^').rstrip('$')

            # Reset the snippet parameter index for each step
            self.snippet_parameter_index = 0

            # Remove (?:[^"]|\\")* puncutation matches
            pattern = re.sub('\(\?:\[\^"\]\|\\\\*"\)\*', '', pattern)

            # Fix (?:|I )
            pattern = re.sub('\(\?:\|?([\w\s]+)\)', '\\1', pattern)

            # Remove look-behind/aheads
            pattern = re.sub('\+\?\=', '', pattern)
            pattern = re.sub('\?:', '', pattern)
            pattern = re.sub('\?!', '', pattern)

            # Remove any left over groups after removing look-behind/aheads so the named group pattern matches
            pattern = re.sub('\(([\w\s]+)\)', '\\1', pattern)

            # Named groups that will eventually become snippet parameters, e.g. ${1:test}
            pattern = re.sub('\(\?P<(\w+)>[^\)]*\)', '{{\\1}}', pattern)

            # Default to the first word option, e.g. "I should (be|stay) on ..."
            pattern = re.sub('\((\w\s+)\|[\w\s\|]+\)', '\\1', pattern)

            # Remove optional characters, e.g. "I see an? something"
            pattern = re.sub('\w\?', '', pattern)

            # Remove optional groups
            pattern = re.sub('\?', '', pattern)

            # Remove nested groups
            pattern = ''.join(self.unbraced_chunks(pattern))

            # Fix empty parameters so that they become snippet parameters, e.g. I click on ""
            pattern = re.sub('""', '"{{}}"', pattern)

            # Replace placeholders with numbered snippet parameters
            pattern = re.sub('\{\{(\w*)\}\}', self.named_group_repl, pattern)

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
