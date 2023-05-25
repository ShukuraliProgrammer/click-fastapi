from setuptools import setup, find_packages

setup(
          name='fastapi-click',
          version='1.0.0',
          description='This package is preparing now, it is not ready to use but after almost 2 or 3 months it will ready to use.',
          long_description= 'Developers who work in Uzbekistan will use this package to integrate Click UZ Payment System to their own fastapi projects.',
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