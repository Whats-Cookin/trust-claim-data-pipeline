from setuptools import setup, find_packages

setup(
    name="trust-claim-data-pipeline",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'python-dotenv',
        'psycopg2-binary'
    ]
)

