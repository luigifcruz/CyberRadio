CD = $(shell pwd)
VER = $(shell git describe --tags)
ARCH = $(shell uname -m)

## Compiler Base Image (AMD64)
COMP_IMG = debian:oldstable

## Installer Base Image (AMD64)
ARCH_IMG = archlinux:latest
UBNT_IMG = ubuntu:latest
FDRA_IMG = fedora:latest

## Base Images Override (ARM64V8)
ifeq ($(ARCH), aarch64)
COMP_IMG = debian:oldstable
UBNT_IMG = debian:oldstable
endif

## Print Base Images to Console
$(info ++++++++++++++++++++++++++++++++++++++++++)
$(info HOST ARCH IS $(ARCH))
$(info COMPILER  BASE IMAGE: $(COMP_IMG))
$(info INSTALLER BASE IMAGE: $(ARCH_IMG), $(UBNT_IMG), $(FDRA_IMG))
$(info ++++++++++++++++++++++++++++++++++++++++++)

all: compiler installer build release

fix-permission:
	sudo chown -fR $(shell whoami) target || :

compiler:
	docker build --build-arg IMAGE=$(COMP_IMG) -t cyber_linux_compiler -f ./docker/compiler/Dockerfile.linux .

installer:
	docker build --build-arg IMAGE=$(UBNT_IMG) -t cyber_deb_installer -f ./docker/installer/Dockerfile.deb .
ifneq ($(ARCH), aarch64)
	docker build --build-arg IMAGE=$(ARCH_IMG) -t cyber_pkg_installer -f ./docker/installer/Dockerfile.pkg .
	docker build --build-arg IMAGE=$(FDRA_IMG) -t cyber_rpm_installer -f ./docker/installer/Dockerfile.rpm .
endif

build:
	docker run -v $(CD):/home cyber_linux_compiler
	make fix-permission

release:
	docker run -v $(CD):/home cyber_deb_installer
ifneq ($(ARCH), aarch64)
	docker run -v $(CD):/home cyber_pkg_installer
	docker run -v $(CD):/home cyber_rpm_installer
endif
	make fix-permission
