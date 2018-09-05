WOUDC Evaluation
----------------

Provides infrastructure to evaluate model against WOUDC sonde network.

Quick Start
-----------

 - Search for OzoneSondes and download "Data File URLs" format from woudc.org
 - save downloaded urls.csv in this folder
 - Edit Makefile and then type make
   - set YYYY in Makefile to the year for evaluation
   - set MODTMP to a strftime template for model (e.g., `/path/ACONC_%Y%m%d`)
 - Run `make`

Prerequisites
-------------
 - Model output for comparison (CMAQ, CAMx, or GEOS-Chem)
 - Python (3 recommended)
   - pandas
   - numpy
   - matplotlib
   - PseudoNetCDF

Steps
-----
1. Create a urls.csv file from woudc.org data search that points to all sonde files you want to download.
2. Download all sondes from URLs (`make dataupdated`).
3. Create a metadata file locations.json (`make locations.json`).
4. Update Makefile to point to your model data (manual).
5. Create NetCDF files (`make ncupdated`).
6. Create figures (`make -C figs`)

Directory Structure
-------------------

```
./
 |- README.md
 |- urls.csv*
 |- Makefile
 |- extract_sondes.py
 |- filecleaner.py
 |- getlocs.py
 |- locations.json
 |- data/
 |- mod/
 |- obs/
 |- figs/
```

