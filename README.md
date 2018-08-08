WOUDC Evaluation
----------------

Provides infrastructure to evaluate model against WOUDC sonde network.

Quick Start
-----------

Edit Makefile and then type make

Steps
-----
1. (Optional) Create a urls.csv file from WOUDC to point to all sonde files you want (manual).
2. Download all sondes from URLs (`make dataupdated`).
3. Create a metadata file locations.json (`make locations.json`).
4. Update Makefile to point to your model data (manual).
5. Create NetCDF files (`make ncupdated`).
6. Create figures (`make -C figs`)

Directory Structure
-------------------
./
 |- README.md
 |- Makefile
 |- extract\_sondes.py
 |- filecleaner.py
 |- getlocs.py
 |- locations.json
 |- data/
 |- mod/
 |- obs/
 |- figs/
 |- urls.csv


