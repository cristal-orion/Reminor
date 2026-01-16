from setuptools import setup, find_packages

setup(
    name='reminor',
    version='5.0.0',
    packages=find_packages(),
    install_requires=[
        'spacy>=3.7.5,<3.8',
        'scikit-learn>=1.4.2,<1.5',
        'requests>=2.32.3,<2.33',
        'python-dotenv>=1.0.1,<1.1',
        'matplotlib>=3.8.4,<3.9',
        'networkx>=3.3,<3.4',
        'rich>=13.7.0',
        'textual>=0.60.0'
    ],
    entry_points={
        'console_scripts': [
            'reminor = reminor.cli:main',
        ],
    },
    author='Michele',
    author_email='your@email.com',
    description='A terminal-based AI-powered personal journal.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Miky94/Reminor-4.2',
)