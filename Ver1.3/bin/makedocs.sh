#!/bin/bash

"""
HMAC/OMAC Documentation
================

Ignacio Tamayo, TSP, 2016
Version 1.3
Date: August 2016

This script calls Pydoc on all the Python source files to generate the .html documentation

"""



pydoc -w ./

mv *.html ../docs
