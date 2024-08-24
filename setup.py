from cx_Freeze import setup, Executable

setup(
    name = "abc",
    version = "0.1",
    description = "My Application",
    executables = [Executable("abc.py")]
)