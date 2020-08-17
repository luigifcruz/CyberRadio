CD = $(shell pwd)
VER = $(shell git describe --tags)
ARCH = $(shell uname -p)
IMAGE_VER = 16.04

ifeq ($(ARCH), aarch64)
IMAGE_VER = 18.04
endif

$(info Host arch is $(ARCH))
$(info Compiler image version is $(IMAGE_VER))

all: compiler installer build release

fix-permission:
	sudo chown -fR $(shell whoami) target || :

compiler:
	docker build --build-arg IMAGE_VER=$(IMAGE_VER) -t cyber_linux_compiler -f ./docker/compiler/Dockerfile.linux .

installer:
ifneq ($(ARCH), aarch64)
	docker build -t cyber_pkg_installer -f ./docker/installer/Dockerfile.pkg .
endif
	docker build -t cyber_deb_installer -f ./docker/installer/Dockerfile.deb .
	docker build -t cyber_rpm_installer -f ./docker/installer/Dockerfile.rpm .

build:
	docker run -v $(CD):/home cyber_linux_compiler
	make fix-permission

release:
	docker run -v $(CD):/home cyber_pkg_installer
	docker run -v $(CD):/home cyber_deb_installer
	docker run -v $(CD):/home cyber_rpm_installer
	make fix-permission
