#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
ROOT_DIR="$(dirname $SCRIPT_DIR)"

# RPA install
RPA_DIR=$ROOT_DIR/rpa
RV_SUPPORT_PATH=$RPA_DIR/local_install/lib/open_rv
rm -rf $RV_SUPPORT_PATH
mkdir -p $RV_SUPPORT_PATH/Packages/
$RPA_DIR/build_scripts_spi/_install_rpa_core_pkg.sh

# App install
export APP_RV_SUPPORT_PATH=$ROOT_DIR/local_install/lib/rpa_app
export RV_SUPPORT_PATH=$RV_SUPPORT_PATH:$APP_RV_SUPPORT_PATH
rm -rf $APP_RV_SUPPORT_PATH
mkdir -p $APP_RV_SUPPORT_PATH/Packages/
$ROOT_DIR/rpa/app/core/open_rv/install.sh
