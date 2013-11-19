'''
Guppy Installer is an experimental module which allows for installing
and updating Guppy Animation Tools for non-technical users.

*******************************************************************************
    License and Copyright
    Copyright 2013 Jordan Hueckstaedt
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


''''''*************************************************************************

    Author:........Jordan Hueckstaedt
    Website:.......RubberGuppy.com
    Email:.........AssumptionSoup@gmail.com
    Work Status:...Employed!
****************************************************************************'''

__author__ = 'Jordan Hueckstaedt'
__copyright__ = 'Copyright 2013'
__license__ = 'LGPL v3'
__version__ = '.01'
__email__ = 'AssumptionSoup@gmail.com'
__status__ = 'Alpha'


# TODO: Figure out how to use tags in the git repo and use these to
#       indicate versions.  Then have the update command only notify
#       for new "versions" by default.  It should have a flag to get
#       every update if you want though.
#
#       I'm also playing around with the idea of having this module
#       import the other modules in Guppy Animation Tools into the
#       __main__ namespace (as an ease-of-use feature for non-technical
#       users)
#
#       Cache if the module has tried to update itself that day already.
#       If so, don't try to update again.
#
# Future Plans:
#       If I made this script more generic and flexible, would any other
#       tool dev's be interested in a universal updater/package manager?

# Usage:

# Users will eventually be invited to use this installer with the
# following code. This code is subject to change, but is added here for
# documentation and tracking purposes.

# ----
# def importCode(code, name):
#     '''Import dynamically generated code as a module.'''
#     import sys, imp
#     module = imp.new_module(name)
#     exec code in module.__dict__
#     sys.modules[name] = module
#     return module

# def downloadInstaller():
#     '''Download and run installer gui'''
#     import urllib2, contextlib

#     url = 'https://raw.github.com/assumptionsoup/Guppy-Animation-Tools/master/guppyInstaller.py'
#     request = urllib2.urlopen(urllib2.Request(url))
#     with contextlib.closing(request) as response:
#         guppyInstaller = importCode(response.read(), "guppyInstaller")
#         guppyInstaller.dynamicInstall()

# downloadInstaller()
# ----


import os
import sys
import subprocess
import threading
import datetime
import maya.cmds as cmds
import maya.mel as mel

_repoIsPrepped = False
_gitEnv = None
REPO_ORIGIN = 'https://github.com/assumptionsoup/Guppy-Animation-Tools.git'
try:
    REPO_DIR = os.path.dirname(__file__)
except NameError:
    __file__ = None
    REPO_DIR = None

class GitError(IOError): pass
class GitNotFoundError(GitError): pass
class RepoNotFoundError(GitError): pass


def _addToPath(env, newLocation):
    '''
    Add path to os.environ[env]
    '''
    if not newLocation.endswith(os.path.sep):
        newLocation += os.path.sep

    if newLocation not in os.environ[env].split(os.pathsep):
        if os.environ[env]:
            os.environ[env] += os.pathsep
        os.environ[env] += newLocation


def _addPluginPath(pluginLocation):
    '''
    Add plugin path to Maya.
    '''
    _addToPath('MAYA_PLUG_IN_PATH', pluginLocation)


def _addScriptPath(scriptLocation):
    '''
    Add mel script path to Maya.
    '''
    _addToPath('MAYA_SCRIPT_PATH', scriptLocation)


def _addPythonPath(scriptLocation):
    '''
    Add python script path to Maya.
    '''
    # Adding to python path just adds the parent dir for some reason
    # (Guppy-Animation-Tools).
    # _addToPath('PYTHONPATH', scriptLocation)
    if scriptLocation not in sys.path:
        sys.path.append(scriptLocation)


def _addIconPath(iconLocation):
    '''
    Add icon path to Maya.
    '''
    _addToPath('XBMLANGPATH', iconLocation)


def doubleStringRepr(inputStr):
    return '"%s"' % repr(inputStr)[1:-1].replace('"',r'\"').replace(r"\'","'")


def install():
    '''
    Install Guppy Animation Tools to Maya's paths.
    '''
    pluginPath = os.path.join(REPO_DIR, 'Plugins')
    _addPythonPath(os.path.join(REPO_DIR, 'Scripts'))
    _addPluginPath(os.path.join(pluginPath, 'Python'))
    _addScriptPath(os.path.join(REPO_DIR, 'AETemplates'))
    _addIconPath(os.path.join(REPO_DIR, 'Icons'))


def _getScriptDirectories():
    scriptDirs = mel.eval('getenv("MAYA_SCRIPT_PATH")').split(os.pathsep)
    userScriptDir = cmds.internalVar(usd=1)
    if userScriptDir in scriptDirs:
        scriptDirs.remove(userScriptDir)
    scriptDirs = [userScriptDir] + scriptDirs
    return [p for p in scriptDirs if os.access(p, os.W_OK)]


def dynamicInstall():
    '''
    Opens a gui to install Guppy Animation Tools assuming only this
    module has been run from memory.
    '''
    window = cmds.window(title="Guppy Animation Tools Installer",
                         resizeToFitChildren=1)
    formLayout = cmds.formLayout(numberOfDivisions=100)
    scriptDirs = cmds.optionMenu('scriptDirs', label='Download To')

    for directory in _getScriptDirectories():
        cmds.menuItem(label=directory)

    checkForUpdates = cmds.checkBox(
        label='Periodically check for updates.', value=1)

    def installFromUI(*args):
        update = cmds.checkBox(checkForUpdates, q=1, value=1)
        installDir = cmds.optionMenu(scriptDirs, q=1, value=1)
        installDir = os.path.join(installDir, 'guppy_animation_tools')
        installDir = str(installDir)
        cmds.deleteUI(window, window=True)
        _dynamicInstall(installDir, checkForUpdates=update)

    install = cmds.button(label='Install', command=installFromUI)

    layout = {'af': [], 'ap': [], 'ac': []}
    layout['af'].append((scriptDirs, 'top', 5))
    layout['af'].append((scriptDirs, 'left', 5))
    layout['af'].append((scriptDirs, 'right', 5))

    layout['ac'].append((checkForUpdates, 'top', 5, scriptDirs))
    layout['af'].append((checkForUpdates, 'left', 5))
    layout['af'].append((checkForUpdates, 'right', 5))

    layout['ac'].append((install, 'top', 5, checkForUpdates))
    layout['af'].append((install, 'left', 5))
    layout['af'].append((install, 'right', 5))

    cmds.formLayout(
        formLayout,
        e=1,
        **layout)

    cmds.showWindow(window)

def _dynamicInstall(installDir, checkForUpdates=True):
    '''
    Fully install Guppy Animation Tools assuming only this module has
    been run from memory.
    '''
    global REPO_DIR
    REPO_DIR = installDir
    if not os.path.exists(REPO_DIR):
        os.makedirs(REPO_DIR)

    update()
    scriptsDir = os.path.dirname(REPO_DIR)
    userSetupPath = os.path.join(scriptsDir, 'userSetup.mel')
    pythonToEval = ['import sys',
                    'sys.path.append(%r)' % REPO_DIR,
                    'import guppyInstaller',
                    'guppyInstaller.install()']
    if checkForUpdates:
        pythonToEval.append("guppyInstaller.update(blocking=False, onDays=['monday'])")
    pythonToEval = ';'.join(pythonToEval)

    with open(userSetupPath, 'a') as userSetup:
        userSetup.write('\npython(%s);\n' % doubleStringRepr(pythonToEval))

    install()


# I had considered naming it getGitEnv, but that just seems confusing!
def gitEnv():
    '''
    Get the environment for the needed to run the git subprocess in.

    This is necessary for windows where mysysgit is not installed to the
    path by default (which is a terrible default).
    '''
    global _gitEnv
    if _gitEnv is None:
        import platform
        path = os.environ.get('PATH', '')

        # The default installation of mysysgit is not on the path.
        # So just add it as a quick 'n dirty fix
        if platform.system() == 'Windows':
            if path:
                path += os.pathsep
            path += r'C:/msysgit/bin'
            path += os.pathsep
            path += r'C:/msysgit/mingw/bin'

        _gitEnv = {}
        _gitEnv.update(os.environ)
        _gitEnv['PATH'] = path
    return _gitEnv


def runCommand(cmd, blocking=True, printOutput=False, cwd=None, env=None,
               stdout=None, stderr=None):
    env = gitEnv() if env is None else env
    cwd = REPO_DIR if cwd is None else cwd
    stdout = subprocess.PIPE if stdout is None else stdout
    stderr = subprocess.STDOUT if stderr is None else stderr

    p = subprocess.Popen(
        cmd,
        stdout=stdout,
        stderr=stderr,
        cwd=cwd,
        env=env,
        shell=True)

    output = []
    for line in iter(p.stdout.readline, ""):
        if printOutput:
            print line,
        output.append(line)
    output = '\n'.join(output)

    if blocking:
        p.wait()

    return {
        'command': cmd,
        'output': output,
        'process': p,
        'success': p.returncode == 0}


def checkCommandResults(results, errorMsg='', exception=GitError):
    if not results['success']:
        print '>>> %s' % results['command']
        print results['output']
        raise exception(errorMsg)


def _cloneRepo():
    # Create a new repo
    results = runCommand('git init')
    checkCommandResults(results, 'Failed to init a new repo.')

    results = runCommand(
        'git remote add --track master origin %s' % REPO_ORIGIN)
    checkCommandResults(results, 'Unable to add git origin.')

    _prepRepo()

    results = runCommand(
        'git commit -m "Initial Guppy Animation Tools Update" --allow-empty')
    checkCommandResults(results, 'Unable create initial commit.')

    results = runCommand('git remote set-head origin master')
    checkCommandResults(results, 'Failed to set remote head.')

    print 'Successfully created the Guppy Animation Tools repo.'
    update(force=True, blocking=True)


def _prepRepo():
    '''
    Prep the repo by making sure git is on the Path and the newest
    changes on the master branch are fetched.
    '''
    global _repoIsPrepped
    if _repoIsPrepped:
        return

    # Test it.
    results = runCommand('git status')
    repoFiles = os.listdir(REPO_DIR)
    if ((not results['success'] and 'Not a git repository' in results['output'])
            or '.git' not in repoFiles):
        raise RepoNotFoundError('Git repo not found.  '
                                'Cannot update Guppy Animation Tools.')
    checkCommandResults(
        results,
        'Unable to find git executable.  Cannot update Guppy Animation Tools.')


    results = runCommand(
        'git config user.email "guppy.animation.tools@user.com"')
    checkCommandResults(results, 'Unable to configure git.')

    results = runCommand(
        'git config user.name "Guppy Animation Tools Updater"')
    checkCommandResults(results, 'Unable to configure git.')

    results = runCommand('git fetch origin')
    checkCommandResults(results, 'Unable to fetch git updates.')
    results = runCommand('git fetch origin --tags')
    checkCommandResults(results, 'Unable to fetch git tags.')

    _repoIsPrepped = True


def isUpToDate():
    '''
    Check if Guppy Animation Tools is up to date.
    '''
    _prepRepo()
    results = runCommand('git checkout master')
    checkCommandResults(results, 'Unable checkout master branch.')
    results = runCommand('git rev-list HEAD...origin/master --count')
    checkCommandResults(results, 'Unable to query origin/master status.')
    return results['output'].strip() == '0'


def _getChangeLog():
    '''
    Return a formatted string of all the new commit messages in origin/master
    '''
    _prepRepo()

    results = runCommand('git log HEAD..origin/master --pretty=format:"  - %B"')
    checkCommandResults(results, 'Failed to get repo change log.')
    log = []
    for line in results['output'].splitlines():
        if not line:
            continue
        if not line.startswith('  - '):
            line = '    %s' % line
        log.append(line)
    return '\n'.join(log)


def update(force=False, blocking=True, onDays=None):
    '''
    Check if Guppy Animation Tools is up to date.  If it is not, prompt
    the user to update.

    Parameters
    ----------
        force: `bool`
            If true, force the update.  The user will not be prompted.
        blocking: `bool`
            If true, this function will block until completed.  Setting
            this to false is useful if the update process is placed in
            the userSetup and it is taking too long.  However, this will
            also mean that the updates will (probably) not take effect
            until the next restart.
        onDays: list of `str`
            List of days this module should try to update itself on.
            If blank, this module will always try to update itself at
            least once a day.
    '''

    # Only update on the given days
    if onDays is not None:
        if isinstance(onDays, basestring):
            onDays = [onDays]
        today = datetime.datetime.today().strftime('%A').lower()
        if not any(today == day.lower() for day in onDays):
            return
    # Open in a new thread since this could take awhile, even just to
    # determine everything is up to date.
    if not blocking:
        t = threading.Thread(target=_update, kwargs={'force': force})
        t.start()
    else:
        _update(force=force)


def _update(force=False, onError='notify'):
    '''
    Check if Guppy Animation Tools is up to date.  If it is not, prompt
    the user to update.

    Parameters
    ----------
        force : `bool`
            If true, force the update.  The user will not be prompted.
        onError : 'notify' or 'error'
            Define behavior if an error is encountered.  If set to
            notify, the user will be notified in a non-technical way of
            the error encountered.  If set to error, an exception will
            be raised.

    '''
    global _repoIsPrepped
    try:
        _prepRepo()
    except GitNotFoundError:
        if onError == 'error':
            raise
        else:
            print ('Git could not be found.  '
                   'Git must be installed for Guppy Animation Tools to '
                   'auto-update.')
            return
    except RepoNotFoundError:
        if onError != 'notify':
            raise
        if os.path.exists(REPO_DIR) and os.listdir(REPO_DIR):
            msg = ("Guppy Animation Tools is missing a git repo.\n"
                   "To fix this, it is recommended that you perform the following command in terminal\n"
                   "in the directory you would like Guppy Animation Tools to be downloaded:\n"
                   "\n"
                   "git clone %s\n"
                   "\n"
                   "Or you can use the EXPERIMENTAL download feature to let Guppy Animation Tools \n"
                   "try to update itself.\n\n"
                   "WARNING: THIS MAY CRASH MAYA AND WILL DELETE ALL FILES IN THE FOLLOWING FOLDER:\n\n"
                   "%s") % (REPO_ORIGIN, REPO_DIR)

            result = cmds.confirmDialog(
                title='Guppy Animation Tools Missing Git Repo',
                message=msg,
                button=['Experimental Download', 'Cancel'],
                defaultButton='Cancel',
                cancelButton='Cancel',
                dismissString='Cancel')
            if result != 'Experimental Download':
                return
        _repoIsPrepped = False
        _cloneRepo()
        return

    if not force:
        if not isUpToDate():
            # prompt user if update is okay.
            msg = 'Guppy Animation Tools has an update with the following changes:\n'
            msg += _getChangeLog()
            result = cmds.confirmDialog(
                title='Update Guppy Animation Tools?',
                message=msg,
                button=['Update', 'Cancel'],
                defaultButton='Update',
                cancelButton='Cancel',
                dismissString='Cancel')
            if result != 'Update':
                print 'Not updating Guppy Animation Tools'
                return
        else:
            print 'Guppy Animation Tools is up to date.'
            return

    # While I tell the user this updater will delete things (and I do
    # everything in my power to do so after this since I assume left
    # over files are modified/old python scripts which need updating), I
    # still want the tech guru's to be able to restore things if the
    # shit hits the fan.
    results = runCommand('git stash --include-untracked -a')
    checkCommandResults(results, 'Failed stash changes.')

    results = runCommand('git checkout master')
    checkCommandResults(results, 'Failed to check out repo master.')
    results = runCommand('git reset --hard origin/master')
    checkCommandResults(results, 'Failed to reset repo.')
    # Actually, I shouldn't need to run this now that I'm stashing beforehand
    # subprocess.call('git clean -fdx', env=gitEnv(), cwd=REPO_DIR, shell=True)
    print 'Guppy Animation Tools is up to date.'

    # Invalidate prep repo, so other commands will re-run it appropriately
    _repoIsPrepped = False

run = install
