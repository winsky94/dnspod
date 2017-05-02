#!/bin/bash

dnspod_path="/opt/server_init/pypod.py"

if [[ -f ${dnspod_path} ]]; then
	if [[ ! -x ${dnspod_path} ]]; then
		chmod u+x ${dnspod_path}
	fi

	python /opt/server_init/pypod.py
fi


