#!/usr/bin/env python3
"""
Kali Terminal v2 - Masterpiece Edition
Professional Kali Linux Terminal Simulator with AI Integration
"""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = """
Kali Terminal v2 - Masterpiece Edition
Professional Kali Linux Terminal Simulator with AI Integration

Features:
- 100+ cybersecurity commands
- AI integration (Ollama, OpenAI, Anthropic, Gemini)
- Multiple themes and customization
- Tab completion and command history
- Plugin architecture for extensibility
- Session management
"""

setup(
    name='kali-terminal',
    version='2.0.0',
    description='Professional Kali Linux Terminal Simulator with AI Integration',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Cyber Security Expert',
    author_email='security@kaliterminal.local',
    url='https://github.com/kaliterminal/v2',
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'prompt-toolkit>=3.0.41',
        'pygments>=2.17.0',
        'requests>=2.31.0',
        'urllib3>=2.1.0',
        'pyyaml>=6.0.1',
        'cryptography>=41.0.7',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.12.0',
            'flake8>=6.1.0',
        ],
        'rich': ['rich>=13.7.0'],
        'httpx': ['httpx>=0.26.0'],
    },
    entry_points={
        'console_scripts': [
            'kali-terminal=main:main',
            'kali=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Security',
        'Topic :: System :: Shells',
    ],
    keywords='kali linux terminal simulator cybersecurity ai security-tools',
)