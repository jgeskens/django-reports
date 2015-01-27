#!/usr/bin/env python
from deployer.client import start
from deployer.host.ssh import SSHHost
from deployer.node import Node
import os
from deployer.utils.string_utils import esc1

REPO_DIRECTORY = os.environ.get('REPO_DIRECTORY', '/home/user/advreports')
BRANCH = os.environ.get('BRANCH', 'master')
REPOSITORY = 'https://github.com/vikingco/django-advanced-reports.git'
SSH_HOST = os.environ.get('SSH_HOST', 'vm.oemfoeland.com')
SSH_USER = os.environ.get('SSH_USER', 'user')
SSH_PASSWORD = os.environ.get('SSH_PASSWORD')
VIRTUALENV = os.environ.get('VIRTUALENV', '/home/user/env/advreports')
RUNIT_SERVICE = os.environ.get('RUNIT_SERVICE', 'advreports')

PROJECT_DIRECTORY = os.path.join(REPO_DIRECTORY, 'advreport_test_project')
PYTHON = os.path.join(VIRTUALENV, 'bin/python')
PIP = os.path.join(VIRTUALENV, 'bin/pip')


class oemfoeland_host(SSHHost):
    address = SSH_HOST
    username = SSH_USER
    password = SSH_PASSWORD


class AdvreportTestProjectDeployment(Node):
    class Hosts:
        host = oemfoeland_host

    def git_clone(self):
        self.hosts.run("git clone '%s' --branch='%s' '%s'" % (esc1(REPOSITORY), esc1(BRANCH), (REPO_DIRECTORY)))

    def git_fetch(self):
        with self.hosts.cd(REPO_DIRECTORY):
            self.hosts.run('git fetch origin')

    def git_checkout(self):
        with self.hosts.cd(REPO_DIRECTORY):
            self.hosts.run('git stash')
            self.hosts.run("git checkout '%s'" % (esc1(BRANCH),))
            self.hosts.run("git pull origin '%s'" % (esc1(BRANCH),))
            self.hosts.run('git stash pop')

    def pip_install(self):
        with self.hosts.cd(PROJECT_DIRECTORY):
            self.hosts.run("'%s' install -r requirements.txt" % esc1(PIP))

    def django_manage(self, command):
        with self.hosts.cd(PROJECT_DIRECTORY):
            self.hosts.run("'%s' manage.py %s" % (esc1(PYTHON), command))

    def django_collectstatic(self):
        self.django_manage('collectstatic --noinput')

    def django_migrate(self):
        self.django_manage('migrate')

    def restart_app(self):
        self.hosts.sudo("sv restart '%s'" % (esc1(RUNIT_SERVICE),))

    def deploy(self):
        self.git_fetch()
        self.git_checkout()
        self.pip_install()
        self.django_collectstatic()
        self.django_migrate()
        self.restart_app()


if __name__ == '__main__':
    start(AdvreportTestProjectDeployment)
