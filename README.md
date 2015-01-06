SublimeDiction
==============
Diction is a plugin for SublimeText 2/3 that integrates GNU diction in the editor.

Diction highlights style mistakes and commonly misused phrases in your texts. It also gives a helpful suggestion on what to change in the text to make it better.

Installation
------------
For highlighting to work, you have to install GNU diction. On *nix you probably want to use your favorite package manager. Homebrew on OSX provides it as well, just run the following

    brew install diction

It may be neccessary to restart sublime depending on your system.

Use
---
By default, diction works on files with the extension .txt, .tex, .mdown. Have a look at the package settings to add extensions as needed.

On a medium sized text file, a diction run is too slow on most machines to be run live while editing. 
Use <kbd>CMD</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> on OSX or <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> to bring up the command palette and look for `Diction: GNU Diction run`. This command will trigger the scanning and mark the respective regions where diction has suggestions.

The suggestions text is displayed in the status bar for now, as Sublime Text currently has no API to display tooltips of any kind to the user.
