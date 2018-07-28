workspace(name="hbot")

git_repository(
    name = "io_bazel_rules_python",
    remote = "https://github.com/dforsyth/rules_python.git",
    commit = "9630203fa3306993c3b7cc50db1af4c309ab5d9d",
)

load("@io_bazel_rules_python//python:pip.bzl", "pip_repositories")
pip_repositories()

load("@io_bazel_rules_python//python:pip.bzl", "pip3_import")
pip3_import(
   name = "deps",
   requirements = "//:requirements.txt",
)

load("@deps//:requirements.bzl", "pip_install")
pip_install()
