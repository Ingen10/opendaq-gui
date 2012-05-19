from distutils.core import setup

setup(
    name='python-opendaq', 
    version='0.1', 
    license='LGPL', 
    install_requires= ['pyserial'],
    description='Python binding for openDAQ hardware', 
    author='Juan Menendez', 
    author_email='juanmb@gmail.com',
    py_modules=['opendaq'],
)

