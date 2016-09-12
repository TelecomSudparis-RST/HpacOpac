#!/bin/bash

#"""
#VIOS Documentation
#================

#Ignacio Tamayo, TSP, 2016
#Version 1.4
#Date: Sept 2016

#This script calls Pydoc on all the Python source files to generate the .html documentation

#"""


pydoc -w ./

mv *.html ../docs/pydoc
