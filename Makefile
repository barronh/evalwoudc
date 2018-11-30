MODTMP=/work/ROMO/global/CMAQv5.2.1/2016fe_hemi_cb6_16jh/108km/basecase/output/CONC/CCTM_CONC_v521_intel17.0_HEMIS_cb6_%Y%m%d
MODTYP=CMAQ
MODLABEL=$(MODTYP)
DATAROOT=data
YYYY=2016

export MODTYP
export MODLABEL

.SECONDARY: dataupdated

all: ncupdated locations.json
	$(MAKE) -C figs

ncupdated: locations.json dataupdated
	python extract_sondes.py -l $< --year=$(YYYY) --sonde-format=woudcsonde --hourly-interval 1 -t $(MODTYP) --season=ALL $(MODTMP) mod/$(MODTYP)_{0}.nc obs/SONDE_$(MODTYP)_{0}.nc

locations.json: dataupdated
	python getlocs.py $(DATAROOT)

dataupdated: urls.csv
	cd $(DATAROOT); wget --continue -i $(PWD)/urls.csv
	python filecleaner.py $(DATAROOT)/*
	date > dataupdated


