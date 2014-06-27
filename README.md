patentsearch
============
This repo contains a collection of python scripts and ipython notebooks I have begun to develop for the purpose of conducting a patent search. 

Currently,

* Download zip files from Google bulk data (thanks, Stack Overflow people)
* Extract (badly formed) xml file from each zip file
* Repackage much less patent information in a python _shelf_ file
    * One _shelf_ per year
    * The idea is to reduce file size and retain only info I want to include in the patent search
    * Still working on getting all the right data in the right format
* Start a patent search
    * Choose patents and/or classifications to include in each search
    * Search through shelf files for references to selected patents and classes
    * Compile a list in a new shelf
