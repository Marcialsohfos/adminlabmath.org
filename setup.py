from setuptools import setup, find_packages

setup(
    name="labmath-admin",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask==3.0.0",
        "Flask-SQLAlchemy==3.1.1",
        "Flask-Login==0.6.3",
        "Flask-WTF==1.2.1",
        "Flask-Bcrypt==1.0.1",
        "Flask-CORS==4.0.0",
        "psycopg2-binary==2.9.9",
        "Pillow==10.3.0",
        "python-dotenv==1.0.0",
        "gunicorn==21.2.0",
        "markdown==3.5.1",
        "bleach==6.0.0",
        "python-slugify==8.0.1",
        "email-validator==2.1.0"
    ],
)