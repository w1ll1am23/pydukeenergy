from setuptools import setup, find_packages

setup(name='pyduke-energy',
      version='0.0.1',
      description='Interface to the unofficial Duke Energy API',
      url='http://github.com/w1ll1am23/pyduke-energy',
      author='William Scanlon',
      license='MIT',
      install_requires=['requests>=2.0'],
      tests_require=['mock'],
      test_suite='tests',
      packages=find_packages(exclude=["dist", "*.test", "*.test.*", "test.*", "test"]),
      zip_safe=True)
