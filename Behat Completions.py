import sublime
import sublime_plugin
import subprocess
import re
import os
import time
from os.path import dirname, realpath
from xml.sax.saxutils import escape
import hashlib
import pickle

BC_PLUGIN_PATH = dirname(realpath(__file__))

class BehatCompletionsCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.save_file = sublime.packages_path()+"/Behat Completions/"+"save.p"
        if not os.path.isfile(self.save_file):
            self.save = {'time_run_behat':0,'step_file_sha1':'','steps':{}}
        else:
            self.save = pickle.load( open(self.save_file , "rb" ) )
            self.steps = self.save['steps'].values();
        self.view = view
        # Load settings
        self.settings = {}
        settings = sublime.load_settings('Behat Completions.sublime-settings')
        for setting in ['behat_executable_path', 'behat_config_path', 'behat_steps_list_file']:      
            if settings.get(setting) == None:
                continue
            self.settings[setting] = settings.get(setting)
        self.update()

    def saveObj(self):
        pickle.dump( self.save, open( self.save_file, "wb" ) )

    def run(self, edit):
        self.update()   
        window = sublime.active_window()
        window.show_quick_panel(self.steps, self.on_quick_panel_done)
        
    def update(self):
        if self.save['time_run_behat']+30 < int(time.time()):
            self.save['time_run_behat'] = int(time.time())
            steps_list_file = open(sublime.packages_path()+"/Behat Completions/"+ self.settings['behat_steps_list_file'], "rb")
            output = steps_list_file.read().decode('ascii', 'ignore').encode('utf8', 'ignore')
            if self.file_change(output):
                return True
            steps_items = re.findall('([\s\S]+?(?:\n\n|$))', output)
            self.save['steps'] = {}
            syntax_out = ""
            re_step_valid = re.compile(r'(?:Given|When|Then|And|But)([\s\S]+?)\n[\s\S]*?ID\:\s{0,4}([\w._-]+)')
            re_if_regex_step =  re.compile(r'^\/\^?(.*?)\$?\/$')
            re_p_name_delete = re.compile(r'[\'\"]?\(\?P\<(\w+?)\>[\'\"]?(\(.*?\))?[\'\"]?.*?\)[\'\"]?')   
            re_rep_var_iside = re.compile(r'\:\w+')
            re_remove_p_name =  re.compile(r'\?\P\<(\w+)\>')
            for step_item in steps_items:
                step_res = re.search(re_step_valid, step_item)
                if step_res and step_res.group(2) not in self.save['steps']:
                    step_str = step_res.group(1).strip(r' \t\n\r')
                    step_res_regex = re.search(re_if_regex_step, step_str)
                    if step_res_regex:
                        step_str_regex = step_res_regex.group(1)
                        step_str_regex = step_str = re.sub(re_remove_p_name,'', step_str_regex)
                    else:
                        step_str_regex = re.sub(re_rep_var_iside,r'"((?:[^"]|\\\\")*)"', step_str)
                        step_str_regex = re.sub(re_p_name_delete, r':\1', step_str_regex)
                    
                    self.save['steps'][step_res.group(2)] = step_str
                    
                    syntax_out = syntax_out + r'<dict>\n<key>match</key>\n<string>^\s*(Given|When|Then|And|But)(?=\s' + escape(step_str_regex) + r'$)</string>\n<key>captures</key>\n<dict>\n<key>1</key>\n<dict>\n<key>name</key>\n<string>entity.name.class.behat</string></dict></dict></dict>'+"\n";


            output = syntax_out
            behat_tmLanguage_t = open(BC_PLUGIN_PATH+"/Behat.tmLanguage.template")
            behat_tmLanguage_s = behat_tmLanguage_t.read()
            behat_tmLanguage_t.close()

            behat_tmLanguage_s = behat_tmLanguage_s.replace(r'<dict>%ADDSTEPVALIDATION%</dict>',output)

            behat_tmLanguage = open(sublime.packages_path()+"/Behat/Syntaxes/Behat.tmLanguage", 'wb')
            behat_tmLanguage.write(behat_tmLanguage_s.decode('ascii', 'ignore'))
            self.steps = self.save['steps'].values();
            self.saveObj()


    def file_change(self,data):
        new_sha1 = hashlib.sha1(data).hexdigest()

        if new_sha1 != self.save['step_file_sha1'] :
            self.save['step_file_sha1'] = new_sha1
            return False
        else:
            return True 
    def on_quick_panel_done(self, picked):
        if picked == -1:
            return
        self.view.run_command('insert_snippet', { 'contents': " " + self.steps[picked] + "$0" })

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
