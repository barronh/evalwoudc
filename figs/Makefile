MODLABEL=CMAQ
MODSRC=$(sort $(wildcard ../mod/*.nc))
OBSSRC=$(sort $(wildcard ../obs/*.nc))
STARGETS=$(addsuffix _ALL.png,$(basename $(notdir $(MODSRC)))) \
        $(addsuffix _DJF.png,$(basename $(notdir $(MODSRC)))) \
        $(addsuffix _MAM.png,$(basename $(notdir $(MODSRC)))) \
        $(addsuffix _JJA.png,$(basename $(notdir $(MODSRC)))) \
        $(addsuffix _SON.png,$(basename $(notdir $(MODSRC)))) \

TARGETS=$(MODLABEL)_TIME_PANEL.png \
    $(MODLABEL)_SITE_PANEL_ALL.png \
    $(MODLABEL)_SITE_PANEL_DJF.png \
    $(MODLABEL)_SITE_PANEL_MAM.png \
    $(MODLABEL)_SITE_PANEL_JJA.png \
    $(MODLABEL)_SITE_PANEL_SON.png \
    $(STARGETS)


all: $(TARGETS)

%_ALL.png: ../obs/SONDE_%.nc ../mod/%.nc
	python plot_sondes.py --season ALL --label $(MODLABEL) $^ $@

%_DJF.png: ../obs/SONDE_%.nc ../mod/%.nc
	python plot_sondes.py --season DJF --label $(MODLABEL) $^ $@

%_MAM.png: ../obs/SONDE_%.nc ../mod/%.nc
	python plot_sondes.py --season MAM --label $(MODLABEL) $^ $@

%_JJA.png: ../obs/SONDE_%.nc ../mod/%.nc
	python plot_sondes.py --season JJA --label $(MODLABEL) $^ $@

%_SON.png: ../obs/SONDE_%.nc ../mod/%.nc
	python plot_sondes.py --season SON --label $(MODLABEL) $^ $@


$(MODLABEL)_SITE_PANEL_%.png:
	python pcolor_pres_by_site_sondes.py --label=$(MODLABEL) --modreplace=obs/SONDE_,mod/ --season=$* --figsize=13,8 ../obs/SONDE_$(MODLABEL)_STN*.nc $(MODLABEL)_SITE_PANEL_$*.png

$(MODLABEL)_TIME_PANEL.png:
	python pcolor_pres_by_time_sondes.py --npoint=20 --label=$(MODLABEL) --modreplace=obs/SONDE_,mod/ ../obs/SONDE_$(MODLABEL)_STN*.nc $(MODLABEL)_TIME_PANEL.png

clean:
	rm $(TARGETS)
