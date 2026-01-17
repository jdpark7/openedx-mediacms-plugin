from setuptools import setup, find_packages

setup(
    name="tutor-mediacms",
    version="0.1.0",
    license="AGPLv3",
    author="MediaCMS",
    author_email="contact@mediacms.io",
    description="A Tutor plugin for MediaCMS integration",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "tutor.plugin.v1": [
            "mediacms = tutor_mediacms.plugin"
        ]
    },
)
