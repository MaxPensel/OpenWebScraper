import os


# traceback from exceptions that inherit from this class are suppressed
class CommandLineError(Exception):
    """The traceback of all CommandLineError's is supressed when the
    errors occur on the command line to provide a useful command line
    interface.
    """
    def render(self, msg):
        return msg % vars(self)


class MissingFileError(CommandLineError):
    """This error is raised when the file can not be located at the
    specified path.
    """
    def __init__(self, filename):
        self.filename = filename
        self.root, self.ext = os.path.splitext(filename)

    def __str__(self):
        return self.render((
            'The file "%(filename)s" can not be found.\n'
            'Is this the right path/to/file/you/want/to/extract%(ext)s?'
        ))


class UnknownMethod(CommandLineError):
    """This error is raised when the specified --method on the command
    line is unknown.
    """
    def __init__(self, method):
        self.method = method

    def __str__(self):
        return self.render((
            'The method "%(method)s" can not be found for this filetype.'
        ))


class ShellError(CommandLineError):
    """This error is raised when a shell.run returns a non-zero exit code
    (meaning the command failed).
    """
    def __init__(self, command, exit_code, stdout, stderr):
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.executable = self.command.split()[0]

    def is_not_installed(self):
        return os.name == 'posix' and self.exit_code == 127

    def not_installed_message(self):
        return (
            "The command `%(command)s` failed because the executable\n"
            "`%(executable)s` is not installed on your system. Please make\n"
            "sure the appropriate dependencies are installed before using\n"
            "textract:\n\n"
            "    http://textract.readthedocs.org/en/latest/installation.html\n"
        ) % vars(self)

    def failed_message(self):
        return (
            "The command `%(command)s` failed with exit code %(exit_code)d\n"
            "------------- stdout -------------\n"
            "%(stdout)s"
            "------------- stderr -------------\n"
            "%(stderr)s"
        ) % vars(self)

    def __str__(self):
        if self.is_not_installed():
            return self.not_installed_message()
        else:
            return self.failed_message()