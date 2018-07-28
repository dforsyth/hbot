load("@deps//:requirements.bzl", "all_requirements")

# Don't really need this.
load(
  "@io_bazel_rules_python//python:python.bzl",
  "py_binary", "py_library",
)

py_library(
    name = "lib",
    srcs = glob(["bot/*.py"]),
    deps = [
    ] + all_requirements,
)

py_binary(
  name = "main",
  srcs = glob(["*.py"]),
  deps = [
    ":lib",
  ],
  default_python_version = "PY3"
)
