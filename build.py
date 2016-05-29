from pybuilder.core import use_plugin, init, Author

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.distutils")


name = "hydra-deploy"
url = 'https://github.com/lake-lerna/hydra-deploy'
information = "Please visit {url}".format(url=url)

authors = [Author('Tahir Rahif', 'tahir.rauf1@gmail.com')]
license = 'Apache 2.0'
summary = "An infra to deploy Mesos-Marathon cluster on various clouds"
version = '0.1.0'

default_task = "publish"


@init
def set_properties(project):
    project.set_property("coverage_break_build", False)
    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_break_build', True)
    project.set_property('flake8_include_test_sources', True)
    project.set_property('distutils_classifiers', [
        'Development Status:: 4 - Beta',
        'Intended Audience :: Developers'
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance'
    ])

    project.build_depends_on('shell_command')
    project.build_depends_on('fabric')
    project.build_depends_on('google-api-python-client')
