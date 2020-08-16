CD = $(shell pwd)
VER = $(shell git describe --tags)

all: compiler build release

fix-permission:
	sudo chown -fR $(shell whoami) target || :

compiler:
	docker build -t cyber_linux_x64_compiler -f ./docker/compiler/Dockerfile.linux_x64 .
	docker build -t cyber_pkg_x64_installer -f ./docker/installer/Dockerfile.pkg_x64 .
	docker build -t cyber_deb_x64_installer -f ./docker/installer/Dockerfile.deb_x64 .
	docker build -t cyber_rpm_x64_installer -f ./docker/installer/Dockerfile.rpm_x64 .

build:
	docker run -v $(CD):/home cyber_linux_x64_compiler
	make fix-permission

release:
	docker run -v $(CD):/home cyber_pkg_x64_installer
	docker run -v $(CD):/home cyber_deb_x64_installer
	docker run -v $(CD):/home cyber_rpm_x64_installer
	make fix-permission