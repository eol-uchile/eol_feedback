import setuptools

setuptools.setup(
    name="eol_feedback",
    version="0.0.1",
    author="matiassalinas",
    author_email="matsalinas@uchile.cl",
    description="Eol feedback",
    long_description="Eol feedback",
    url="https://eol.uchile.cl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "lms.djangoapp": [
            "eol_feedback = eol_feedback.apps:EolFeedbackConfig",
        ],
    },
)
