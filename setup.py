from setuptools import setup, find_packages

setup(
          name='fastapi-click',
          version='1.0.0',
          description='',
          long_description= '',
          author='Shukurali Rezamonov',
          author_email='shukuralijob@gmail.com',
          url='https://pypi.org/project/fastapi-click',
          license='',
          py_modules=['fastapi-click'],
          python_requires='>=3.8', #python version required
          install_requires = [
          'pandas',
          'matplotlib',
          ],
          packages=find_packages()
)