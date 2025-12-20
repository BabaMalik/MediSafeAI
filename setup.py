"""
MediSafeAI Setup Configuration
A privacy-first predictive healthcare analytics system
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
def read_requirements(filename):
    """Read requirements from file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f
                if line.strip() and not line.startswith('#')]

setup(
    name='medisafe-ai',
    version='1.0.0',
    author='BabaMalik',
    author_email='babamalik206@gmail.com',
    description='A privacy-first predictive healthcare analytics system with differential privacy',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/BabaMalik/MediSafeAI',
    project_urls={
        'Bug Reports': 'https://github.com/BabaMalik/MediSafeAI/issues',
        'Source': 'https://github.com/BabaMalik/MediSafeAI',
        'Documentation': 'https://github.com/BabaMalik/MediSafeAI/blob/main/README.md',
    },
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Environment :: Web Environment',
    ],
    python_requires='>=3.8',
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'pylint>=2.17.5',
            'mypy>=1.4.1',
            'pre-commit>=3.3.3',
            'ipython>=8.14.0',
            'jupyter>=1.0.0',
        ],
        'docs': [
            'sphinx>=7.1.0',
            'sphinx-rtd-theme>=1.3.0',
            'sphinx-autodoc-typehints>=1.24.0',
        ],
        'spark': [
            'pyspark>=3.4.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'medisafe=cli.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'data_generator': ['*.json', '*.yaml'],
        'privacy': ['*.json'],
    },
    keywords=[
        'healthcare',
        'differential-privacy',
        'synthetic-data',
        'hipaa',
        'machine-learning',
        'privacy-preserving',
        'medical-analytics',
        'airflow',
        'data-generation',
    ],
    zip_safe=False,
)
