# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Common python commands used by various build scripts."""

import inspect
import os
import subprocess
import sys

_STDOUT_IS_TTY = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# TODO(sosa):  Move logging to logging module.

def GetCallerName():
  """Returns the name of the calling module with __main__."""
  top_frame = inspect.stack()[-1][0]
  return os.path.basename(top_frame.f_code.co_filename)


def RunCommand(cmd, print_cmd=True, error_ok=False, error_message=None,
               exit_code=False, redirect_stdout=False, redirect_stderr=False,
               cwd=None, input=None, enter_chroot=False):
  """Runs a shell command.

  Keyword arguments:
    cmd - cmd to run.  Should be input to subprocess.POpen.  If a string,
      converted to an array using split().
    print_cmd -- prints the command before running it.
    error_ok -- does not raise an exception on error.
    error_message -- prints out this message when an error occurrs.
    exit_code -- returns the return code of the shell command.
    redirect_stdout -- returns the stdout.
    redirect_stderr -- holds stderr output until input is communicated.
    cwd -- the working directory to run this cmd.
    input -- input to pipe into this command through stdin.
    enter_chroot -- this command should be run from within the chroot.  If set,
      cwd must point to the scripts directory.
  Raises:
    Exception:  Raises generic exception on error with optional error_message.
  """
  # Set default for variables.
  stdout = None
  stderr = None
  stdin = None
  output = ''

  # Modify defaults based on parameters.
  if redirect_stdout:  stdout = subprocess.PIPE
  if redirect_stderr:  stderr = subprocess.PIPE
  if input:  stdin = subprocess.PIPE
  if enter_chroot:  cmd = ['./enter_chroot.sh', '--'] + cmd

  # Print out the command before running.
  if print_cmd:
    Info('PROGRAM(%s) -> RunCommand: %r in dir %s' %
         (GetCallerName(), cmd, cwd))

  try:
    proc = subprocess.Popen(cmd, cwd=cwd, stdin=stdin,
                            stdout=stdout, stderr=stderr)
    (output, error) = proc.communicate(input)
    if exit_code:
      return proc.returncode

    if not error_ok and proc.returncode:
      raise Exception('Command "%r" failed.\n' % (cmd) +
                      (error_message or error or output or ''))
  except Exception, e:
    if not error_ok:
      raise
    else:
      Warning(str(e))

  return output


class Color(object):
  """Conditionally wraps text in ANSI color escape sequences."""
  BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
  BOLD = -1
  COLOR_START = '\033[1;%dm'
  BOLD_START = '\033[1m'
  RESET = '\033[0m'

  def __init__(self, enabled=True):
    self._enabled = enabled

  def Color(self, color, text):
    """Returns text with conditionally added color escape sequences.

    Keyword arguments:
      color: Text color -- one of the color constants defined in this class.
      text: The text to color.

    Returns:
      If self._enabled is False, returns the original text. If it's True,
      returns text with color escape sequences based on the value of color.
    """
    if not self._enabled:
      return text
    if color == self.BOLD:
      start = self.BOLD_START
    else:
      start = self.COLOR_START % (color + 30)
    return start + text + self.RESET


def Die(message):
  """Emits a red error message and halts execution.

  Keyword arguments:
    message: The message to be emitted before exiting.
  """
  print >> sys.stderr, (
      Color(_STDOUT_IS_TTY).Color(Color.RED, '\nERROR: ' + message))
  sys.exit(1)


def Warning(message):
  """Emits a yellow warning message and continues execution.

  Keyword arguments:
    message: The message to be emitted.
  """
  print >> sys.stderr, (
      Color(_STDOUT_IS_TTY).Color(Color.YELLOW, '\nWARNING: ' + message))


def Info(message):
  """Emits a blue informational message and continues execution.

  Keyword arguments:
    message: The message to be emitted.
  """
  print >> sys.stderr, (
      Color(_STDOUT_IS_TTY).Color(Color.BLUE, '\nINFO: ' + message))


def FindRepoDir(path=None):
  """Returns the nearest higher-level repo dir from the specified path.

  Args:
    path: The path to use. Defaults to cwd.
  """
  if path is None:
    path = os.getcwd()
  while path != '/':
    repo_dir = os.path.join(path, '.repo')
    if os.path.isdir(repo_dir):
      return repo_dir
    path = os.path.dirname(path)
  return None


def ReinterpretPathForChroot(path):
  """Returns reinterpreted path from outside the chroot for use inside.

  Keyword arguments:
    path: The path to reinterpret.  Must be in src tree.
  """
  root_path = os.path.join(FindRepoDir(path), '..')

  path_abs_path = os.path.abspath(path)
  root_abs_path = os.path.abspath(root_path)

  # Strip the repository root from the path and strip first /.
  relative_path = path_abs_path.replace(root_abs_path, '')[1:]

  if relative_path == path_abs_path:
    raise Exception('Error: path is outside your src tree, cannot reinterpret.')

  new_path = os.path.join('/home', os.getenv('USER'), 'trunk', relative_path)
  return new_path

