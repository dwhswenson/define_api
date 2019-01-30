# Define API

This contains some tricks I've been using to define and ensure the API for
OpenPathSampling. In the future, I may add a setup.py, etc. That probably
depends on how much I or other use it.

The basic idea is that we like to have a more flat structure in the official
(and supported) API than what comes out of our file structure. But we need
to document what that API is. And that's what this code is intended to help.

To be clear, this deals with where objects can be found, and not the
functions that a class implements, or the arguments to those functions. That
is another (and equally important) part of the API definition.

In addition to this README, this contains the following files:

* `define_api.py`: Script to create the API list
* `test_api.py`: Example pytest module to test an API. It includes an option
  to combine errors: if you do not combine errors, the test will stop at the
  first bad API entry, raising an `AttributeError`. If you combine errors,
  the test will try all API entries, and if any fail, it will report all the
  failures in an `AssertionError`. Copy it into your tests directory, and
  modify it to use an appropriate file for your own project.
* `good_api.txt`: Input file for `test_api.py` that should pass
* `bad_api.txt`: Input file for `test_api.py` that should fail
* `ops_api_dirs.txt`: Extra input file for OPS (provided as an example of
  how to create the api_dirs files)

There are several useful ways to use `define_api.py`. Here are a few, as
used with OpenPathSampling.

Find all possible locations in you package:

    ./define_api.py --allow-non-api --show-modules openpathsampling

The `--allow-non-api` argument allows things that shouldn't be considered
part of the API, such as names that begin with underscores and things that
aren't actually in your main package (for example, you'll see external
packages that you have imported). In general, you probably don't want the
`--allow-non-api` flag.  The `--show-modules` flag means that modules are
also listed, not just classes, functions, etc.

Since there an object can exist in several different locations, sometimes it
can be useful to see all the locations for each object. To see that, run
this:

    ./define_api.py --runtype=all openpathsampling

One important difference here is that the output gives 2 columns: the left
column is the filesystem-based import location; the right column is a list
of all the import locations where this can be found.

Now we will take a little extra human help to define the API. This help
comes in the forms of an API directories file, where the directories (in
dot-separated form) that you intend to support are listed. For an example,
see `ops_api_dirs.txt`.

    ./define_api.py --runtype=api_names --api-file=ops_api_dirs.txt openpathsampling

This gives us the "canonical" location of each object, according to the OPS
API. This still includes all objects (except those whose names begin with
underscores), and so it may include things that are technically part of the
"hidden" API. The closest we can get to this without the human intervention
in the `ops_api_dirs.txt` file is to use the `--runtype=first` option
instead. That essentially takes the first location found in a breadth-first
search.

To separate the "hidden" API from the supported API, we have two more
`runtype` options. The first will be what you use to define your supported
API. Redirect this into a file for the file you can use with `test_api.py`.

    ./define_api.py --runtype=in_api --api-file=ops_api_dirs.txt openpathsampling

At the same time, it is very important that you look at the objects that are
considered to be in the "hidden" API. You can do that with this:

    ./define_api.py --runtype=not_in_api --api-file=ops_api_dirs.txt openpathsampling

Check the results of that for anything you actually intended to have in the
main API.

Finally, you can see all the non-API names for objects in the API. This is
useful if, for example, you want to check that there are no aliases for API
objects that come in at a less-nested level than you expected.

    ./define_api.py --runtype=all_api_aliases --api-file=ops_api_dirs.txt openpathsampling
