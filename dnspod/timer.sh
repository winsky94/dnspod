#!/bin/bash

dnspod_path="/opt/dnspod/pypod.py"

if [[ -f ${dnspod_path} ]]; then
	if [[ ! -x ${dnspod_path} ]]; then
		chmod u+x ${dnspod_path}
	fi

	python /opt/dnspod/pypod.py
fi


