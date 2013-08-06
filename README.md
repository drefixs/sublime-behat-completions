# Behat Completions for Sublime Text 2

## Installation

### Mac OS X

```sh
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages
git clone https://github.com/jadu/sublime-behat-completions.git Behat\ Completions
```

#### Configuration


Create the user settings file
```sh
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/User
open Behat\ Completions.sublime-settings
```

Set the paths:
```json
{
    "behat_executable_path": "/path/to/behat",
    "behat_config_path": "/path/to/behat.yml"
}
```

Now restart Sublime Text

## Usage

To use the completions simply type Given, When, Then, And or But and 
hit tab to open the quick panel with a listing of all available steps. 
Type in the quick panel to filter the steps and hit enter to select a step.
