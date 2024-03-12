import setuptools

with open("README.md", "r") as f:
	long_description = f.read()

setuptools.setup(
	name = "EchoMessagerAPI",
	version = "0.0.5",
	author = "Fun_Dan3",
	author_email = "dfr34560@gmail.com",
	description = "API to access EchoServer post-quantum messager.",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	url = "https://github.com/FunDan3/EchoAPI/",
	project_urls = {
		"Bug Tracker": "https://github.com/FunDan3/EchoAPI/issues"
	},
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: OS Independent",
	],
	packages = setuptools.find_packages(where = "src"),
	package_dir = {"": "src"},
	python_requires = ">=3.8",
	install_requires = ["pqcryptography", "aiohttp"]
)
