CD = $(shell pwd)
VER = $(shell git describe --tags)

all: compiler build

fix-permission:
	sudo chown -fR $(shell whoami) target || :

compiler:
	docker build -t cyberradio_linux_x64 -f ./docker/Dockerfile.linux_x64 .

build:
	docker run -v $(CD):/home cyberradio_linux_x64
	make fix-permission

release:
	fbs installer